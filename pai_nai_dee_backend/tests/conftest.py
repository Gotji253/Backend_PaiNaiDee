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
# Connection to the PostgreSQL instance (e.g., to 'postgres' or 'template1' database for creating other DBs)
# This engine should connect to a default DB like 'postgres' or 'template1' to be able to create/drop other DBs.
# Ensure the user has CREATEDB privileges.
SUPERUSER_ENGINE = create_engine(
    f"postgresql://{settings.TEST_POSTGRES_USER}:{settings.TEST_POSTGRES_PASSWORD}@{settings.TEST_POSTGRES_SERVER}:{settings.TEST_POSTGRES_PORT}/postgres",
    isolation_level="AUTOCOMMIT",  # Important for CREATE/DROP DATABASE
)

# This will be the engine for the actual test database (dynamically created)
# It will be initialized later in a fixture.
test_db_engine = None
TestSessionLocal = None  # Will be initialized later

# Store the original app engine and session local to restore later if needed
ORIGINAL_APP_ENGINE = app_engine
ORIGINAL_APP_SESSION_LOCAL = AppSessionLocal


def wait_for_db(engine_to_check, retries=5, delay=5):
    """Wait for the database to be responsive."""
    for i in range(retries):
        try:
            with engine_to_check.connect() as connection:
                connection.execute(text("SELECT 1"))
            print("Database is responsive.")
            return True
        except OperationalError as e:
            print(f"Database not responsive yet (attempt {i+1}/{retries}): {e}")
            if i < retries - 1:
                time.sleep(delay)
    print("Database did not become responsive after multiple retries.")
    return False


@pytest.fixture(scope="session", autouse=True)
def postgres_test_db_manager():
    """
    Manages the creation of a template test database and applies migrations.
    This template database is then used by other fixtures to clone new databases for test sessions.
    """
    template_db_name = settings.TEST_POSTGRES_DB_MAIN
    print(f"Attempting to manage template database: {template_db_name}")

    with SUPERUSER_ENGINE.connect() as conn:
        # Check if template database exists
        result = conn.execute(
            text(f"SELECT 1 FROM pg_database WHERE datname = '{template_db_name}'")
        ).scalar_one_or_none()

        if result:
            print(
                f"Template database '{template_db_name}' already exists. Assuming schema is up-to-date."
            )
            # Optionally, you could drop and recreate if you always want the freshest schema
            # conn.execute(text(f"DROP DATABASE IF EXISTS {template_db_name} WITH (FORCE)"))
            # result = None # Force recreation

        if not result:
            print(f"Creating template database: {template_db_name}")
            try:
                conn.execute(text(f"CREATE DATABASE {template_db_name}"))
            except ProgrammingError as e:
                print(
                    f"Could not create template database {template_db_name}. It might already exist or another issue: {e}"
                )
                # If it failed because it exists (race condition), we can try to proceed.
                # Otherwise, this is a fatal error for setup.
                if f'database "{template_db_name}" already exists' not in str(e):
                    raise

            # Now, apply migrations to this new template database
            print(
                f"Applying Alembic migrations to template database: {template_db_name}"
            )

            # Temporarily override DATABASE_URL for Alembic
            original_db_url = settings.DATABASE_URL
            settings.DATABASE_URL = f"postgresql://{settings.TEST_POSTGRES_USER}:{settings.TEST_POSTGRES_PASSWORD}@{settings.TEST_POSTGRES_SERVER}:{settings.TEST_POSTGRES_PORT}/{template_db_name}"

            # Ensure alembic.ini uses the correct DATABASE_URL by updating env var if alembic reads from it
            # Or by ensuring settings.DATABASE_URL is what alembic's env.py reads
            # For this project, env.py reads from app.core.config.settings.DATABASE_URL

            # Path to alembic.ini, assuming conftest.py is in tests/ and alembic.ini is in pai_nai_dee_backend/
            alembic_ini_path = os.path.join(
                os.path.dirname(__file__), "..", "alembic.ini"
            )
            project_root_for_alembic = os.path.join(os.path.dirname(__file__), "..")

            try:
                # Make sure the DB is ready before running alembic
                temp_engine_for_migration = create_engine(settings.DATABASE_URL)
                if not wait_for_db(temp_engine_for_migration):
                    raise Exception(
                        f"Template database {template_db_name} not responsive for migrations."
                    )

                # Change directory to where alembic.ini is located, or provide path to alembic command
                # Running alembic upgrade head
                # The `python -m alembic upgrade head` approach is often more robust with pathing
                # Ensure that PYTHONPATH includes the project root if alembic needs to import app modules
                env = os.environ.copy()
                env["PYTHONPATH"] = (
                    f"{project_root_for_alembic}{os.pathsep}{env.get('PYTHONPATH', '')}"
                )

                process = subprocess.run(
                    ["alembic", "-c", alembic_ini_path, "upgrade", "head"],
                    capture_output=True,
                    text=True,
                    cwd=project_root_for_alembic,  # Run from project root
                    env=env,
                    check=False,  # Check manually
                )
                if process.returncode != 0:
                    print("Alembic upgrade stdout:")
                    print(process.stdout)
                    print("Alembic upgrade stderr:")
                    print(process.stderr)
                    raise Exception(
                        f"Alembic upgrade head failed for {template_db_name}. Error: {process.stderr}"
                    )
                print(f"Alembic migrations applied successfully to {template_db_name}.")
            finally:
                # Restore original DATABASE_URL in settings
                settings.DATABASE_URL = original_db_url
                if (
                    "temp_engine_for_migration" in locals()
                    and temp_engine_for_migration
                ):
                    temp_engine_for_migration.dispose()

    yield  # Tests run here

    # Teardown for the template database (optional, usually we keep it)
    # print(f"Session finished. Template database '{template_db_name}' was (re)created and migrated.")
    # Uncomment to drop the template database after all tests
    # with SUPERUSER_ENGINE.connect() as conn:
    #     print(f"Dropping template database: {template_db_name}")
    #     conn.execute(text(f"DROP DATABASE IF EXISTS {template_db_name} WITH (FORCE)"))


# Commenting out the old SQLite based fixture
# @pytest.fixture(scope="session", autouse=True)
# def create_test_database():
#     """
#     Create all tables in the test database before tests run, and drop them after.
#     `autouse=True` makes this fixture run automatically for the session.
#     """
#     # Remove the test DB file if it exists (for SQLite file-based DBs)
#     if SQLALCHEMY_TEST_DATABASE_URL and SQLALCHEMY_TEST_DATABASE_URL.startswith("sqlite:///") and os.path.exists(
#         SQLALCHEMY_TEST_DATABASE_URL.split(":///")[1]
#     ):
#         os.remove(SQLALCHEMY_TEST_DATABASE_URL.split(":///")[1])
#
#     if SQLALCHEMY_TEST_DATABASE_URL: # Ensure it's set
#         engine = create_engine(
#             SQLALCHEMY_TEST_DATABASE_URL,
#             connect_args=(
#                 {"check_same_thread": False}
#                 if SQLALCHEMY_TEST_DATABASE_URL.startswith("sqlite")
#                 else {}
#             ),
#         )
#         Base.metadata.create_all(bind=engine)  # Create tables
#         yield  # This is where the tests will run
#         Base.metadata.drop_all(bind=engine)  # Drop tables
#         engine.dispose()
#
#         # Clean up the test DB file after tests (for SQLite file-based DBs)
#         if SQLALCHEMY_TEST_DATABASE_URL.startswith("sqlite:///") and os.path.exists(
#             SQLALCHEMY_TEST_DATABASE_URL.split(":///")[1]
#         ):
#             try:
#                 os.remove(SQLALCHEMY_TEST_DATABASE_URL.split(":///")[1])
#             except OSError as e:
#                 print(f"Error removing test database file: {e}")


@pytest.fixture(scope="function")  # Each test function gets its own DB
def session_test_db(postgres_test_db_manager) -> Generator[str, Any, None]:
    """
    Creates a new database for a test function by cloning the template database,
    and drops it after the test.
    Yields the name of the created database.
    This fixture depends on `postgres_test_db_manager` to ensure the template is ready.
    """
    global test_db_engine, TestSessionLocal  # Allow modification of global engine/session for tests

    # Generate a unique database name for each test function
    # Using os.urandom for more uniqueness if tests run in parallel or very quickly
    unique_id = os.urandom(4).hex()
    current_test_db_name = f"test_db_{unique_id}"
    template_db_name = settings.TEST_POSTGRES_DB_MAIN

    print(
        f"Creating test database: {current_test_db_name} from template {template_db_name}"
    )

    with SUPERUSER_ENGINE.connect() as conn:
        try:
            conn.execute(
                text(
                    f"CREATE DATABASE {current_test_db_name} TEMPLATE {template_db_name}"
                )
            )
        except Exception as e:
            print(
                f"Failed to create database {current_test_db_name} from template {template_db_name}: {e}"
            )
            # Attempt to drop if creation failed mid-way or due to leftovers
            try:
                conn.execute(
                    text(f"DROP DATABASE IF EXISTS {current_test_db_name} WITH (FORCE)")
                )
            except Exception as drop_e:
                print(
                    f"Also failed to drop partially created DB {current_test_db_name}: {drop_e}"
                )
            raise

    # --- Configure engine and session for the newly created database ---
    original_test_db_url = settings.TEST_DATABASE_URL
    current_test_db_url = f"postgresql://{settings.TEST_POSTGRES_USER}:{settings.TEST_POSTGRES_PASSWORD}@{settings.TEST_POSTGRES_SERVER}:{settings.TEST_POSTGRES_PORT}/{current_test_db_name}"
    settings.TEST_DATABASE_URL = current_test_db_url  # Update settings for this test

    if (
        test_db_engine
    ):  # Dispose previous engine if any (e.g. from a previous test function)
        test_db_engine.dispose()

    test_db_engine = create_engine(current_test_db_url)
    if not wait_for_db(test_db_engine):
        # Cleanup before raising exception
        with SUPERUSER_ENGINE.connect() as conn:
            conn.execute(
                text(f"DROP DATABASE IF EXISTS {current_test_db_name} WITH (FORCE)")
            )
        settings.TEST_DATABASE_URL = original_test_db_url  # Restore
        raise Exception(
            f"Newly created test database {current_test_db_name} was not responsive."
        )

    TestSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_db_engine
    )

    # This is important: if your app's main db module (app.db.database) uses a global engine
    # and SessionLocal, you might need to override them for the duration of the test,
    # or ensure that get_db() uses the TestSessionLocal.
    # For now, we assume `override_get_db` in the `client` fixture handles this by using the `db` fixture,
    # which in turn will use this `TestSessionLocal`.

    yield current_test_db_name  # Provide the DB name to the test or other fixtures

    print(f"Dropping test database: {current_test_db_name}")
    if test_db_engine:
        test_db_engine.dispose()  # Close all connections before dropping
        test_db_engine = None
    TestSessionLocal = None

    with SUPERUSER_ENGINE.connect() as conn:
        conn.execute(text(f"DROP DATABASE {current_test_db_name} WITH (FORCE)"))

    settings.TEST_DATABASE_URL = original_test_db_url  # Restore settings


@pytest.fixture(scope="function")
def db(session_test_db: str) -> Generator[Session, Any, None]:
    """
    Fixture to provide a database session to test functions, using the
    dynamically created test database.
    Rolls back transactions after each test.
    Depends on `session_test_db` to ensure the DB is ready.
    """
    if not TestSessionLocal:
        raise Exception(
            "TestSessionLocal not initialized. session_test_db fixture might have failed."
        )

    connection = test_db_engine.connect()  # Use the dynamic engine
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)  # Use the dynamic sessionmaker

    yield session

    session.close()
    transaction.rollback()
    connection.close()


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
@pytest.fixture(
    scope="module"
)  # Or function, depending on how often you need new tokens
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
