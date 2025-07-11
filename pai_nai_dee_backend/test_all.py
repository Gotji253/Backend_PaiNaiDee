import pytest
import os
from httpx import AsyncClient
from fastapi import status
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


from .app.main import app  # FastAPI app instance
from .app.db.database import Base, get_db
from .app.core.config import settings
from .app.models.user import User as UserModel
from .app.core.security import create_access_token  # get_password_hash is no longer here
from .app.core.password_utils import get_password_hash  # Import from new location
from datetime import timedelta
import pytest_asyncio  # Moved to top

# Attempt to import testcontainers
try:
    from testcontainers.postgres import PostgresContainer
except ImportError:
    PostgresContainer = None  # type: ignore

# Determine if running in CI or locally
IS_CI = os.getenv("CI", "false").lower() == "true"

# Global variables for database engine and session factory, configured by fixtures
_test_engine = None
_TestingSessionLocal = None
SQLALCHEMY_DATABASE_URL_FOR_TESTS = ""  # Will be set by setup logic


@pytest.fixture(scope="session", autouse=True)
def database_setup_logic():
    """
    Sets up the database for the entire test session.
    - In CI: Uses DATABASE_URL from settings.
    - Locally with testcontainers: Spins up a PostgreSQL container.
    - Locally without testcontainers: Uses TEST_DATABASE_URL from settings (e.g., local SQLite).
    Manages table creation and deletion.
    """
    global _test_engine, _TestingSessionLocal, SQLALCHEMY_DATABASE_URL_FOR_TESTS

    if IS_CI:
        print(
            f"CI Environment: Using DATABASE_URL from settings: {settings.DATABASE_URL}"
        )
        SQLALCHEMY_DATABASE_URL_FOR_TESTS = settings.DATABASE_URL
        _test_engine = create_engine(SQLALCHEMY_DATABASE_URL_FOR_TESTS)
        _TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=_test_engine
        )
        Base.metadata.drop_all(bind=_test_engine)  # Ensure clean state
        Base.metadata.create_all(bind=_test_engine)  # Create tables
        yield
        Base.metadata.drop_all(bind=_test_engine)  # Clean up
    else:
        if PostgresContainer is None:
            print(
                f"Local Environment: testcontainers not found. Using TEST_DATABASE_URL: {settings.TEST_DATABASE_URL}"
            )
            SQLALCHEMY_DATABASE_URL_FOR_TESTS = settings.TEST_DATABASE_URL
            if SQLALCHEMY_DATABASE_URL_FOR_TESTS is None:
                print("TEST_DATABASE_URL is None, defaulting to SQLite in-memory for test_all.py")
                SQLALCHEMY_DATABASE_URL_FOR_TESTS = "sqlite:///:memory:"
            connect_args = (
                {"check_same_thread": False}
                    if SQLALCHEMY_DATABASE_URL_FOR_TESTS and "sqlite" in SQLALCHEMY_DATABASE_URL_FOR_TESTS
                else {}
            )
            _test_engine = create_engine(
                SQLALCHEMY_DATABASE_URL_FOR_TESTS, connect_args=connect_args
            )
            _TestingSessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=_test_engine
            )
            Base.metadata.drop_all(bind=_test_engine)
            Base.metadata.create_all(bind=_test_engine)
            yield
            Base.metadata.drop_all(bind=_test_engine)
        else:
            print("Local Environment: Using testcontainers for PostgreSQL.")
            try:
                with PostgresContainer("postgres:14-alpine") as pg:
                    SQLALCHEMY_DATABASE_URL_FOR_TESTS = pg.get_connection_url()
                    print(
                        f"PostgreSQL container started: {SQLALCHEMY_DATABASE_URL_FOR_TESTS}"
                    )
                    _test_engine = create_engine(SQLALCHEMY_DATABASE_URL_FOR_TESTS)
                    _TestingSessionLocal = sessionmaker(
                        autocommit=False, autoflush=False, bind=_test_engine
                    )
                    Base.metadata.drop_all(bind=_test_engine)
                    Base.metadata.create_all(bind=_test_engine)
                    yield  # DB is up for the session
                    Base.metadata.drop_all(bind=_test_engine)
                print("PostgreSQL container stopped.")
            except Exception as e:
                print(f"Error with PostgreSQL container: {e}")
                print(
                    f"Falling back to TEST_DATABASE_URL: {settings.TEST_DATABASE_URL}"
                )
                SQLALCHEMY_DATABASE_URL_FOR_TESTS = settings.TEST_DATABASE_URL
            if SQLALCHEMY_DATABASE_URL_FOR_TESTS is None: # Corrected indentation
                print("TEST_DATABASE_URL is None in fallback, defaulting to SQLite in-memory for test_all.py")
                SQLALCHEMY_DATABASE_URL_FOR_TESTS = "sqlite:///:memory:"
                connect_args = (
                    {"check_same_thread": False}
                    if SQLALCHEMY_DATABASE_URL_FOR_TESTS and "sqlite" in SQLALCHEMY_DATABASE_URL_FOR_TESTS
                    else {}
                )
                _test_engine = create_engine(
                    SQLALCHEMY_DATABASE_URL_FOR_TESTS, connect_args=connect_args
                )
                _TestingSessionLocal = sessionmaker(
                    autocommit=False, autoflush=False, bind=_test_engine
                )
                Base.metadata.drop_all(bind=_test_engine)
                Base.metadata.create_all(bind=_test_engine)
                yield
                Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture(scope="function")
def db_session(database_setup_logic):
    """
    Provides a transactional database session for each test function.
    Overrides the main app's get_db dependency.
    """
    if _test_engine is None or _TestingSessionLocal is None:
        pytest.fail("Database not initialized. Check database_setup_logic fixture.")

    connection = _test_engine.connect()
    transaction = connection.begin()
    session = _TestingSessionLocal(bind=connection)

    # Override get_db dependency for the FastAPI app
    app.dependency_overrides[get_db] = lambda: session

    yield session  # This session is used by the test and API calls via overridden get_db

    session.close()
    transaction.rollback()  # Rollback changes after each test
    connection.close()
    app.dependency_overrides.clear()  # Clear the override




@pytest_asyncio.fixture(scope="function")  # Use the specific decorator
async def client(db_session):  # Added db_session dependency
    """
    Provides an AsyncClient for making API requests to the test app.
    Relies on the db_session fixture to handle DB setup and dependency override.
    """
    from httpx import ASGITransport  # Import ASGITransport

    transport = ASGITransport(app=app)  # app is the FastAPI instance
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="function")
def test_user_data(db_session):  # Depends on db_session to interact with the DB
    """Creates a test user directly in the database."""
    user_payload = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword",
    }
    hashed_password = get_password_hash(user_payload["password"])
    db_user_model = UserModel(
        username=user_payload["username"],
        email=user_payload["email"],
        hashed_password=hashed_password,
    )
    db_session.add(db_user_model)
    db_session.commit()
    db_session.refresh(db_user_model)
    return {"db_user": db_user_model, "password": user_payload["password"]}


@pytest.fixture(scope="function")
def test_auth_token(test_user_data):  # Depends on test_user_data
    """Generates an access token for the test user."""
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": test_user_data["db_user"].username},
        expires_delta=access_token_expires,
    )
    return access_token


# --- Test Cases ---


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Welcome to Pai Nai Dee API"}


# --- User Endpoint Tests ---
@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    response = await client.post(
        f"{settings.API_V1_STR}/users/",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpassword",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_user_duplicate_username(
    client: AsyncClient, test_user_data
):  # Uses test_user_data
    response = await client.post(
        f"{settings.API_V1_STR}/users/",
        json={
            "username": test_user_data["db_user"].username,  # Existing username
            "email": "another@example.com",
            "password": "newpassword",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_login_for_access_token(
    client: AsyncClient, test_user_data
):  # Uses test_user_data
    login_data = {
        "username": test_user_data["db_user"].username,
        "password": test_user_data["password"],
    }
    response = await client.post(f"{settings.API_V1_STR}/auth/token", data=login_data)
    assert response.status_code == status.HTTP_200_OK
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_read_users_unauthenticated(client: AsyncClient):
    response = await client.get(f"{settings.API_V1_STR}/users/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_read_users_authenticated(
    client: AsyncClient, test_auth_token
):  # Uses test_auth_token
    headers = {"Authorization": f"Bearer {test_auth_token}"}
    response = await client.get(f"{settings.API_V1_STR}/users/", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


# --- Place Endpoint Tests ---
@pytest.mark.asyncio
async def test_create_place(
    client: AsyncClient, test_auth_token
):  # Uses test_auth_token
    headers = {"Authorization": f"Bearer {test_auth_token}"}
    place_data = {
        "name": "Test Cafe",
        "description": "A nice cafe",
        "category": "Cafe",
        "latitude": 13.75,
        "longitude": 100.5,
        "address": "123 Test St",
    }
    response = await client.post(
        f"{settings.API_V1_STR}/places/", json=place_data, headers=headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Test Cafe"
    assert "id" in data


@pytest.mark.asyncio
async def test_read_places(client: AsyncClient):
    response = await client.get(f"{settings.API_V1_STR}/places/")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


# --- Review Endpoint Tests ---
@pytest.mark.asyncio
async def test_create_review_for_place(
    client: AsyncClient, test_auth_token, db_session
):  # Uses test_auth_token and db_session
    headers = {"Authorization": f"Bearer {test_auth_token}"}
    place_data = {
        "name": "Reviewable Place",
        "category": "Test",
        "address": "Review Addr",
    }
    place_response = await client.post(
        f"{settings.API_V1_STR}/places/", json=place_data, headers=headers
    )
    assert place_response.status_code == status.HTTP_201_CREATED
    created_place = place_response.json()

    review_data = {
        "place_id": created_place["id"],
        "rating": 4.5,
        "comment": "Great place for testing reviews!",
    }
    review_response = await client.post(
        f"{settings.API_V1_STR}/reviews/", json=review_data, headers=headers
    )
    assert review_response.status_code == status.HTTP_201_CREATED
    review_json = review_response.json()
    assert review_json["rating"] == 4.5
    assert review_json["place_id"] == created_place["id"]


# --- Itinerary Endpoint Tests ---
@pytest.mark.asyncio
async def test_create_itinerary(
    client: AsyncClient, test_auth_token, db_session
):  # Uses test_auth_token and db_session
    headers = {"Authorization": f"Bearer {test_auth_token}"}
    place_data = {
        "name": "Itinerary Place",
        "category": "Itinerary Test",
        "address": "Itin Addr",
    }
    place_response = await client.post(
        f"{settings.API_V1_STR}/places/", json=place_data, headers=headers
    )
    assert place_response.status_code == status.HTTP_201_CREATED
    created_place = place_response.json()

    itinerary_data = {
        "name": "My Test Itinerary",
        "description": "An itinerary for testing",
        "place_ids": [created_place["id"]],
    }
    itinerary_response = await client.post(
        f"{settings.API_V1_STR}/itineraries/", json=itinerary_data, headers=headers
    )
    assert itinerary_response.status_code == status.HTTP_201_CREATED
    itinerary_json = itinerary_response.json()
    assert itinerary_json["name"] == "My Test Itinerary"
    # To check places in itinerary, the schema must include them.
    # Assuming Itinerary schema includes places_in_itinerary with Place details:
    # assert len(itinerary_json["places_in_itinerary"]) == 1
    # assert itinerary_json["places_in_itinerary"][0]["id"] == created_place["id"]


@pytest.mark.asyncio
async def test_read_my_itineraries(
    client: AsyncClient, test_auth_token
):  # Uses test_auth_token
    headers = {"Authorization": f"Bearer {test_auth_token}"}
    response = await client.get(
        f"{settings.API_V1_STR}/itineraries/my-itineraries", headers=headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


# --- System Pipeline Test ---
def mock_train_model():  # As requested by user
    print("Mocking model training... (Not applicable for this project type)")
    return True


@pytest.mark.asyncio
async def test_system_pipeline(
    client: AsyncClient, test_auth_token, db_session
):  # Uses all main fixtures
    print("Starting system pipeline test...")

    # 1. Mock Environment Load (checked by settings and successful fixture setup)
    assert settings.PROJECT_NAME == "Pai Nai Dee API"
    print("Step 1: Environment loaded.")

    # 2. Import all modules (FastAPI app loading implies this)
    assert app is not None
    print("Step 2: Modules imported (FastAPI app available).")

    # 3. Run mock train model
    model_trained = mock_train_model()
    assert model_trained is True
    print("Step 3: Mock model training completed.")

    # 4. Verify system can work through a typical user flow
    headers = {"Authorization": f"Bearer {test_auth_token}"}

    # Create a place
    place_data = {
        "name": "Pipeline Place",
        "category": "Pipeline",
        "address": "Pipe Addr",
    }
    p_res = await client.post(
        f"{settings.API_V1_STR}/places/", json=place_data, headers=headers
    )
    assert (
        p_res.status_code == status.HTTP_201_CREATED
    ), f"Failed to create place: {p_res.text}"
    pipeline_place_id = p_res.json()["id"]
    print(f"Step 4a: Created place ID {pipeline_place_id}.")

    # Create an itinerary with this place
    itinerary_data = {"name": "Pipeline Itinerary", "place_ids": [pipeline_place_id]}
    i_res = await client.post(
        f"{settings.API_V1_STR}/itineraries/", json=itinerary_data, headers=headers
    )
    assert (
        i_res.status_code == status.HTTP_201_CREATED
    ), f"Failed to create itinerary: {i_res.text}"
    print("Step 4b: Created itinerary.")

    # Read itineraries to confirm
    my_i_res = await client.get(
        f"{settings.API_V1_STR}/itineraries/my-itineraries", headers=headers
    )
    assert my_i_res.status_code == status.HTTP_200_OK
    itineraries_list = my_i_res.json()
    assert isinstance(itineraries_list, list)
    assert any(item["name"] == "Pipeline Itinerary" for item in itineraries_list)
    print("Step 4c: Read and confirmed itinerary.")

    print("System pipeline test completed successfully.")
