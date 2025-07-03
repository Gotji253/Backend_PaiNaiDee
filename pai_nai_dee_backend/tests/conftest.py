import pytest
from typing import Generator, Any
# FastAPI removed
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os

# Set environment variable to indicate testing mode (optional, but can be useful)
os.environ["TESTING"] = "1"

from app.main import app as main_app  # Main FastAPI application # noqa: E402
from app.db.database import Base  # SQLAlchemy Base for table creation/deletion # noqa: E402
from app.core.config import settings  # Application settings # noqa: E402
from app.db.database import get_db  # Original get_db dependency # noqa: E402

# Use the test database URL from settings
SQLALCHEMY_TEST_DATABASE_URL = settings.TEST_DATABASE_URL

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args=(
        {"check_same_thread": False}
        if SQLALCHEMY_TEST_DATABASE_URL.startswith("sqlite")
        else {}
    ),
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_test_database():
    """
    Create all tables in the test database before tests run, and drop them after.
    `autouse=True` makes this fixture run automatically for the session.
    """
    # Remove the test DB file if it exists (for SQLite file-based DBs)
    if SQLALCHEMY_TEST_DATABASE_URL.startswith("sqlite:///") and os.path.exists(
        SQLALCHEMY_TEST_DATABASE_URL.split(":///")[1]
    ):
        os.remove(SQLALCHEMY_TEST_DATABASE_URL.split(":///")[1])

    Base.metadata.create_all(bind=engine)  # Create tables
    yield  # This is where the tests will run
    Base.metadata.drop_all(bind=engine)  # Drop tables

    # Clean up the test DB file after tests (for SQLite file-based DBs)
    if SQLALCHEMY_TEST_DATABASE_URL.startswith("sqlite:///") and os.path.exists(
        SQLALCHEMY_TEST_DATABASE_URL.split(":///")[1]
    ):
        try:
            os.remove(SQLALCHEMY_TEST_DATABASE_URL.split(":///")[1])
        except OSError as e:
            print(f"Error removing test database file: {e}")


@pytest.fixture(
    scope="function"
)  # Changed from module to function for cleaner test isolation
def db() -> Generator[Session, Any, None]:
    """
    Fixture to provide a database session to test functions.
    Rolls back transactions after each test.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")  # Changed from module to function
async def client(db: Session) -> Generator[AsyncClient, Any, None]:
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
    from app.schemas.user import UserCreate
    from app.crud import crud_user
    from app.core.config import settings

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
