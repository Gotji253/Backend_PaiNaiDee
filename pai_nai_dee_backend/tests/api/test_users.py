import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.orm import Session  # For type hinting db fixture if used directly

from ...app.core.config import settings
from ...app.schemas.user import UserCreate  # User removed, For response validation
from ...app.crud import crud_user  # Moved to top

# from ...app import crud # If we need to interact with CRUD directly for setup/teardown

# A utility to generate unique usernames/emails for tests if needed
# def random_lower_string() -> str:
# import random, string
# return "".join(random.choices(string.ascii_lowercase, k=10))


@pytest.mark.asyncio
async def test_create_user_new_username_email(
    client: AsyncClient, db: Session
):  # db fixture can be used for setup/cleanup if needed
    """
    Test creating a new user with a unique username and email.
    """
    username = "testuser_create_01"
    email = "testuser_create_01@example.com"
    password = "testpassword123"

    user_data = UserCreate(username=username, email=email, password=password)

    response = await client.post(
        f"{settings.API_V1_STR}/users/", json=user_data.model_dump()
    )

    assert response.status_code == status.HTTP_201_CREATED
    created_user = response.json()
    assert created_user["username"] == username
    assert created_user["email"] == email
    assert "id" in created_user
    assert "hashed_password" not in created_user  # Ensure password is not returned


@pytest.mark.asyncio
async def test_create_user_duplicate_username(client: AsyncClient):
    """
    Test creating a user with a username that already exists.
    """
    username = "testuser_dup_username"
    email_1 = "testuser_dup_username1@example.com"
    email_2 = "testuser_dup_username2@example.com"
    password = "testpassword123"

    user_data_1 = {"username": username, "email": email_1, "password": password}
    response_1 = await client.post(f"{settings.API_V1_STR}/users/", json=user_data_1)
    assert response_1.status_code == status.HTTP_201_CREATED  # First user created

    user_data_2 = {"username": username, "email": email_2, "password": password}
    response_2 = await client.post(f"{settings.API_V1_STR}/users/", json=user_data_2)
    assert response_2.status_code == status.HTTP_400_BAD_REQUEST
    assert "username already exists" in response_2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_user_duplicate_email(client: AsyncClient):
    """
    Test creating a user with an email that already exists.
    """
    email = "testuser_dup_email@example.com"
    username_1 = "testuser_dup_email1"
    username_2 = "testuser_dup_email2"
    password = "testpassword123"

    user_data_1 = {"username": username_1, "email": email, "password": password}
    response_1 = await client.post(f"{settings.API_V1_STR}/users/", json=user_data_1)
    assert response_1.status_code == status.HTTP_201_CREATED

    user_data_2 = {"username": username_2, "email": email, "password": password}
    response_2 = await client.post(f"{settings.API_V1_STR}/users/", json=user_data_2)
    assert response_2.status_code == status.HTTP_400_BAD_REQUEST
    assert "email already exists" in response_2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_for_access_token(client: AsyncClient, db: Session):
    """
    Test login endpoint to get an access token.
    Requires a user to be already created.
    """
    username = "logintestuser"
    email = "logintestuser@example.com"
    password = "testpassword123"

    # Ensure user exists (could also use a fixture for this)
    # from ...app.crud import crud_user # Moved to top

    existing_user = crud_user.get_user_by_username(db, username=username)
    if not existing_user:
        user_in_create = UserCreate(username=username, email=email, password=password)
        crud_user.create_user(db=db, user_in=user_in_create)

    login_data = {"username": username, "password": password}
    response = await client.post(f"{settings.API_V1_STR}/auth/token", data=login_data)

    assert response.status_code == status.HTTP_200_OK
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_incorrect_password(client: AsyncClient, db: Session):
    username = "loginfailuser"
    email = "loginfailuser@example.com"
    password = "correctpassword"

    # from ...app.crud import crud_user # Already moved to top

    existing_user = crud_user.get_user_by_username(db, username=username)
    if not existing_user:
        user_in_create = UserCreate(username=username, email=email, password=password)
        crud_user.create_user(db=db, user_in=user_in_create)

    login_data = {"username": username, "password": "wrongpassword"}
    response = await client.post(f"{settings.API_V1_STR}/auth/token", data=login_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Incorrect username or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_read_users_unauthenticated(client: AsyncClient):
    """
    Test accessing /users/ endpoint without authentication.
    It should fail as it's now protected (even if further role checks are pending).
    """
    response = await client.get(f"{settings.API_V1_STR}/users/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED  # Expecting auth error


@pytest.mark.asyncio
async def test_read_users_authenticated(client: AsyncClient, test_user_token: str):
    """
    Test accessing /users/ endpoint with authentication.
    """
    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = await client.get(f"{settings.API_V1_STR}/users/", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    # Further checks can be added if specific users are expected or based on roles
    assert isinstance(response.json(), list)


# TODO: Add more tests for other user endpoints (GET /user/{id}, PUT /user/{id}, DELETE /user/{id})
# TODO: Add tests for Place, Review, Itinerary CRUD and API endpoints.
# TODO: Test permission logic once fully implemented (e.g., user can only update self, admin can update any)
