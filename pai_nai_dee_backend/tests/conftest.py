import pytest
from typing import Generator, Any
from httpx import AsyncClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import ProgrammingError, OperationalError
import os
import subprocess  # For running alembic
import time  # For waiting for DB to be ready

# Set environment variable to indicate testing mode (optional, but can be useful)
os.environ["TESTING"] = "1"

from ..app.main import app as main_app  # Main FastAPI application # noqa: E402
from ..app.schemas.user import UserCreate  # Moved for test_user_token
from ..app.crud import crud_user  # Moved for test_user_token

# Base removed as it's unused here. Migrations are handled by alembic.
# from ..app.db.database import (
#     Base,
# )  # SQLAlchemy Base for table creation/deletion # noqa: E402
from ..app.core.config import settings  # Application settings # noqa: E402
from ..app.db.database import (
    get_db,
    SessionLocal as AppSessionLocal,
    engine as app_engine,
)  # Original get_db dependency # noqa: E402

# --- Global variables for database management ---
# --- Global variables for database management ---
SUPERUSER_ENGINE = None
if settings.USE_POSTGRES_FOR_TESTS:
    try:
        SUPERUSER_ENGINE = create_engine(
            f"postgresql://{settings.TEST_POSTGRES_USER}:{settings.TEST_POSTGRES_PASSWORD}@{settings.TEST_POSTGRES_SERVER}:{settings.TEST_POSTGRES_PORT}/postgres",
            isolation_level="AUTOCOMMIT",
        )
        # Check connection
        with SUPERUSER_ENGINE.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        print(f"Could not connect to PostgreSQL superuser DB. Falling back to SQLite. Error: {e}")
        settings.USE_POSTGRES_FOR_TESTS = False
        SUPERUSER_ENGINE = None

test_db_engine = None
TestSessionLocal = None

def wait_for_db(engine_to_check, retries=5, delay=5):
    """Wait for the database to be responsive."""
    for i in range(retries):
        try:
            with engine_to_check.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except OperationalError as e:
            if i < retries - 1:
                time.sleep(delay)
    return False

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Session-wide fixture to manage the test database setup.
    It either prepares a PostgreSQL template database or does nothing for SQLite.
    """
    if not settings.USE_POSTGRES_FOR_TESTS:
        print("Using SQLite for tests. No special session setup required.")
        yield
        return

    # --- PostgreSQL-specific setup ---
    template_db_name = settings.TEST_POSTGRES_DB_MAIN
    with SUPERUSER_ENGINE.connect() as conn:
        result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{template_db_name}'")).scalar_one_or_none()
        if not result:
            conn.execute(text(f"CREATE DATABASE {template_db_name}"))

            # Apply migrations to the template database
            alembic_ini_path = os.path.join(os.path.dirname(__file__), "..", "alembic.ini")
            project_root = os.path.join(os.path.dirname(__file__), "..")

            env = os.environ.copy()
            env["PYTHONPATH"] = f"{project_root}{os.pathsep}{env.get('PYTHONPATH', '')}"

            # Temporarily set DATABASE_URL for Alembic
            original_db_url = settings.DATABASE_URL
            settings.DATABASE_URL = f"postgresql://{settings.TEST_POSTGRES_USER}:{settings.TEST_POSTGRES_PASSWORD}@{settings.TEST_POSTGRES_SERVER}:{settings.TEST_POSTGRES_PORT}/{template_db_name}"

            subprocess.run(
                ["alembic", "-c", alembic_ini_path, "upgrade", "head"],
                cwd=project_root, env=env, check=True
            )

            # Restore original DATABASE_URL
            settings.DATABASE_URL = original_db_url

    yield

    # Optional: Teardown for the template database
    # with SUPERUSER_ENGINE.connect() as conn:
    #     conn.execute(text(f"DROP DATABASE IF EXISTS {template_db_name} WITH (FORCE)"))


@pytest.fixture(scope="function")
def db() -> Generator[Session, Any, None]:
    """
    Main database fixture for tests. It provides a transactional session to a test database.
    It handles both PostgreSQL (cloning from template) and SQLite (in-memory) cases.
    """
    global test_db_engine, TestSessionLocal

    if settings.USE_POSTGRES_FOR_TESTS:
        # --- PostgreSQL: Create a unique DB for the test function ---
        unique_id = os.urandom(4).hex()
        current_test_db_name = f"test_db_{unique_id}"
        template_db_name = settings.TEST_POSTGRES_DB_MAIN

        with SUPERUSER_ENGINE.connect() as conn:
            conn.execute(text(f"CREATE DATABASE {current_test_db_name} TEMPLATE {template_db_name}"))

        current_test_db_url = f"postgresql://{settings.TEST_POSTGRES_USER}:{settings.TEST_POSTGRES_PASSWORD}@{settings.TEST_POSTGRES_SERVER}:{settings.TEST_POSTGRES_PORT}/{current_test_db_name}"
        test_db_engine = create_engine(current_test_db_url)
    else:
        # --- SQLite: Use in-memory database ---
        test_db_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False}
        )
        # Apply migrations for SQLite
        alembic_ini_path = os.path.join(os.path.dirname(__file__), "..", "alembic.ini")
        project_root = os.path.join(os.path.dirname(__file__), "..")

        env = os.environ.copy()
        env["PYTHONPATH"] = f"{project_root}{os.pathsep}{env.get('PYTHONPATH', '')}"

        # Temporarily set DATABASE_URL for Alembic
        original_db_url = settings.DATABASE_URL
        settings.DATABASE_URL = str(test_db_engine.url)

        subprocess.run(
            ["alembic", "-c", alembic_ini_path, "upgrade", "head"],
            cwd=project_root, env=env, check=True
        )
        settings.DATABASE_URL = original_db_url


    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)

    connection = test_db_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

    if test_db_engine:
        test_db_engine.dispose()

    if settings.USE_POSTGRES_FOR_TESTS and 'current_test_db_name' in locals():
        with SUPERUSER_ENGINE.connect() as conn:
            conn.execute(text(f"DROP DATABASE {current_test_db_name} WITH (FORCE)"))


@pytest.fixture(scope="function")
async def client(
    db: Session,
) -> Generator[AsyncClient, Any, None]:  # db fixture will ensure correct DB is used
    """
    Fixture to provide an AsyncClient for making API requests to the test app.
    Overrides the `get_db` dependency to use the test database session.
    """

    def override_get_db():
        # The session 'db' is managed by the 'db' fixture (transaction rollback, close).
        # This override just needs to yield it.
        yield db

    main_app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=main_app, base_url="http://testserver") as c:
        yield c

    # Clean up overrides after tests if necessary, though usually not needed per function
    main_app.dependency_overrides.clear()


# Fixture for obtaining an auth token (example, can be expanded)
# You'll need a test user created in your test DB for this.
@pytest.fixture(scope="function")
async def test_user_token(client: AsyncClient, db: Session) -> str:
    """
    Creates a test user and returns an authentication token for that user.
    This assumes you have user creation and login endpoints.
    """
    # from ..app.schemas.user import UserCreate # Moved to top
    # from ..app.crud import crud_user # Moved to top
    # settings is already imported at the top level with a relative path
    # from ..app.core.config import settings # No longer needed here

    # Create a unique user for testing to avoid conflicts if tests run in parallel or are stateful
    test_username = "testuser_token_fixture@example.com"
    test_password = "testpassword123"

    user = crud_user.get_user_by_username(db, username=test_username)
    if not user:
        user_in_create = UserCreate(
            username=test_username, email=test_username, password=test_password
        )
        user = crud_user.create_user(db, user_in=user_in_create)

    # Login to get token
    login_data = {"username": test_username, "password": test_password}
    response = await client.post(f"{settings.API_V1_STR}/auth/token", data=login_data)

    if response.status_code != 200:
        print(f"Failed to get token: {response.json()}")
        raise Exception(
            f"Could not log in test user {test_username} to get token. Status: {response.status_code}, Response: {response.text}"
        )

    token_data = response.json()
    return token_data["access_token"]
