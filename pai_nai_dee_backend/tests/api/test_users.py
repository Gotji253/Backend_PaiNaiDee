import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.orm import Session  # For type hinting db fixture if used directly

from app.core.config import settings
from app.schemas.user import UserCreate  # User removed, For response validation

# from app import crud # If we need to interact with CRUD directly for setup/teardown

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
async def test_create_user_duplicate_username(client: AsyncClient, db: Session): # Added db to ensure clean state if needed
    """
    Test creating a user with a username that already exists.
    """
    username = "testuser_dup_username_02" # Made username more unique for this test
    email_1 = "testuser_dup_username1_02@example.com"
    email_2 = "testuser_dup_username2_02@example.com"
    password = "testpassword123"

    user_data_1 = {"username": username, "email": email_1, "password": password}
    # It's better practice to ensure this user doesn't exist from a previous failed run
    # or rely on the test DB isolation provided by session_test_db fixture.
    # For this test, we assume the DB is clean for this username or the service handles it.
    response_1 = await client.post(f"{settings.API_V1_STR}/users/", json=user_data_1)
    assert response_1.status_code == status.HTTP_201_CREATED  # First user created

    user_data_2 = {"username": username, "email": email_2, "password": password}
    response_2 = await client.post(f"{settings.API_V1_STR}/users/", json=user_data_2)
    assert response_2.status_code == status.HTTP_400_BAD_REQUEST
    assert "username already exists" in response_2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_user_duplicate_email(client: AsyncClient, db: Session): # Added db
    """
    Test creating a user with an email that already exists.
    """
    email = "testuser_dup_email_02@example.com" # Made email more unique
    username_1 = "testuser_dup_email1_02"
    username_2 = "testuser_dup_email2_02"
    password = "testpassword123"

    user_data_1 = {"username": username_1, "email": email, "password": password}
    response_1 = await client.post(f"{settings.API_V1_STR}/users/", json=user_data_1)
    assert response_1.status_code == status.HTTP_201_CREATED

    user_data_2 = {"username": username_2, "email": email, "password": password}
    response_2 = await client.post(f"{settings.API_V1_STR}/users/", json=user_data_2)
    assert response_2.status_code == status.HTTP_400_BAD_REQUEST
    assert "email already exists" in response_2.json()["detail"].lower()

# Login tests were moved to test_auth.py

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


from app.schemas.user import UserRole # For creating users with roles
from app.models.user import User as UserModel # For type hinting

# Helper function to create a user directly via CRUD for test setup
def create_db_user(db: Session, user_in: UserCreate) -> UserModel:
    from app.crud import crud_user # Local import to avoid top-level if not always needed
    return crud_user.create_user(db, user_in=user_in)

# Helper function to get a token for a specific user
async def get_user_token(client: AsyncClient, username: str, password: str) -> str:
    login_data = {"username": username, "password": password}
    response = await client.post(f"{settings.API_V1_STR}/auth/token", data=login_data)
    assert response.status_code == status.HTTP_200_OK, f"Failed to log in user {username}. Response: {response.text}"
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_read_user_by_id_self(client: AsyncClient, db: Session, test_user_token: str):
    """ Test user reading their own details. """
    # The user for test_user_token is "testuser_token_fixture@example.com"
    # We need its ID.
    user_obj = crud_user.get_user_by_username(db, username="testuser_token_fixture@example.com")
    assert user_obj is not None
    user_id = user_obj.id

    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = await client.get(f"{settings.API_V1_STR}/users/{user_id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    retrieved_user = response.json()
    assert retrieved_user["id"] == user_id
    assert retrieved_user["username"] == "testuser_token_fixture@example.com"

@pytest.mark.asyncio
async def test_read_user_by_id_admin_can_read_other(client: AsyncClient, db: Session):
    """ Test admin reading another user's details. """
    # Create an admin user and get their token
    admin_username = "admin_read_user@example.com"
    admin_password = "adminpassword"
    admin_user_in = UserCreate(username=admin_username, email=admin_username, password=admin_password, role=UserRole.ADMIN)
    create_db_user(db, admin_user_in)
    admin_token = await get_user_token(client, admin_username, admin_password)

    # Create a regular user whose details will be read
    other_username = "other_user_to_read@example.com"
    other_password = "otherpassword"
    other_user_in = UserCreate(username=other_username, email=other_username, password=other_password, role=UserRole.USER)
    other_user_db = create_db_user(db, other_user_in)
    other_user_id = other_user_db.id

    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.get(f"{settings.API_V1_STR}/users/{other_user_id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    retrieved_user = response.json()
    assert retrieved_user["id"] == other_user_id
    assert retrieved_user["username"] == other_username

@pytest.mark.asyncio
async def test_read_user_by_id_user_cannot_read_other(client: AsyncClient, db: Session, test_user_token: str):
    """ Test regular user trying to read another user's details (should fail). """
    # test_user_token is for "testuser_token_fixture@example.com"

    # Create another user whose details will be attempted to be read
    other_username = "another_user_no_access@example.com"
    other_password = "otherpassword"
    other_user_in = UserCreate(username=other_username, email=other_username, password=other_password, role=UserRole.USER)
    other_user_db = create_db_user(db, other_user_in)
    other_user_id = other_user_db.id

    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = await client.get(f"{settings.API_V1_STR}/users/{other_user_id}", headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.asyncio
async def test_read_user_not_found(client: AsyncClient, test_user_token: str):
    """ Test reading a non-existent user. """
    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = await client.get(f"{settings.API_V1_STR}/users/9999999", headers=headers) # Assuming 9999999 doesn't exist
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_update_user_self(client: AsyncClient, db: Session, test_user_token: str):
    """ Test user updating their own details. """
    user_obj = crud_user.get_user_by_username(db, username="testuser_token_fixture@example.com")
    assert user_obj is not None
    user_id = user_obj.id

    update_data = {"email": "updated_self@example.com", "username": "testuser_token_fixture_updated"}
    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = await client.put(f"{settings.API_V1_STR}/users/{user_id}", json=update_data, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    updated_user = response.json()
    assert updated_user["email"] == "updated_self@example.com"
    assert updated_user["username"] == "testuser_token_fixture_updated"

    # Verify in DB
    db.refresh(user_obj)
    assert user_obj.email == "updated_self@example.com"
    assert user_obj.username == "testuser_token_fixture_updated"


@pytest.mark.asyncio
async def test_update_user_admin_can_update_other(client: AsyncClient, db: Session):
    """ Test admin updating another user's details. """
    admin_username = "admin_update_user@example.com"
    admin_password = "adminpassword"
    admin_user_in = UserCreate(username=admin_username, email=admin_username, password=admin_password, role=UserRole.ADMIN)
    create_db_user(db, admin_user_in)
    admin_token = await get_user_token(client, admin_username, admin_password)

    other_username = "other_user_to_update@example.com"
    other_password = "otherpassword"
    other_user_in = UserCreate(username=other_username, email=other_username, password=other_password, role=UserRole.USER)
    other_user_db = create_db_user(db, other_user_in)
    other_user_id = other_user_db.id

    update_data = {"email": "updated_by_admin@example.com", "role": UserRole.EDITOR.value}
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.put(f"{settings.API_V1_STR}/users/{other_user_id}", json=update_data, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    updated_user = response.json()
    assert updated_user["email"] == "updated_by_admin@example.com"
    assert updated_user["role"] == UserRole.EDITOR.value

    db.refresh(other_user_db)
    assert other_user_db.email == "updated_by_admin@example.com"
    assert other_user_db.role == UserRole.EDITOR


@pytest.mark.asyncio
async def test_update_user_user_cannot_update_other(client: AsyncClient, db: Session, test_user_token: str):
    """ Test regular user trying to update another user's details (should fail). """
    other_username = "another_user_no_update@example.com"
    other_password = "otherpassword"
    other_user_in = UserCreate(username=other_username, email=other_username, password=other_password, role=UserRole.USER)
    other_user_db = create_db_user(db, other_user_in)
    other_user_id = other_user_db.id

    update_data = {"email": "attempted_update@example.com"}
    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = await client.put(f"{settings.API_V1_STR}/users/{other_user_id}", json=update_data, headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_update_user_cannot_change_own_role(client: AsyncClient, db: Session, test_user_token: str):
    """ Test regular user trying to change their own role (should fail or be ignored). """
    user_obj = crud_user.get_user_by_username(db, username="testuser_token_fixture@example.com")
    assert user_obj is not None
    user_id = user_obj.id
    original_role = user_obj.role

    update_data = {"role": UserRole.ADMIN.value} # Attempt to become admin
    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = await client.put(f"{settings.API_V1_STR}/users/{user_id}", json=update_data, headers=headers)

    # The endpoint logic prevents non-admins from changing role, resulting in 403
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Verify role did not change in DB
    db.refresh(user_obj)
    assert user_obj.role == original_role


@pytest.mark.asyncio
async def test_delete_user_admin_can_delete_other(client: AsyncClient, db: Session):
    """ Test admin deleting another user. """
    admin_username = "admin_delete_user@example.com"
    admin_password = "adminpassword"
    admin_user_in = UserCreate(username=admin_username, email=admin_username, password=admin_password, role=UserRole.ADMIN)
    create_db_user(db, admin_user_in)
    admin_token = await get_user_token(client, admin_username, admin_password)

    other_username = "other_user_to_delete@example.com"
    other_password = "otherpassword"
    other_user_in = UserCreate(username=other_username, email=other_username, password=other_password, role=UserRole.USER)
    other_user_db = create_db_user(db, other_user_in)
    other_user_id = other_user_db.id

    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.delete(f"{settings.API_V1_STR}/users/{other_user_id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    deleted_user_data = response.json()
    assert deleted_user_data["id"] == other_user_id

    # Verify user is deleted from DB
    assert crud_user.get_user(db, user_id=other_user_id) is None


@pytest.mark.asyncio
async def test_delete_user_user_cannot_delete_other(client: AsyncClient, db: Session, test_user_token: str):
    """ Test regular user trying to delete another user (should fail). """
    other_username = "another_user_no_delete@example.com"
    other_password = "otherpassword"
    other_user_in = UserCreate(username=other_username, email=other_username, password=other_password, role=UserRole.USER)
    other_user_db = create_db_user(db, other_user_in)
    other_user_id = other_user_db.id

    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = await client.delete(f"{settings.API_V1_STR}/users/{other_user_id}", headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN # Endpoint is admin only for delete

@pytest.mark.asyncio
async def test_delete_user_user_cannot_delete_self_via_admin_endpoint(client: AsyncClient, db: Session, test_user_token: str):
    """ Test regular user trying to delete self via admin-only delete endpoint (should fail). """
    user_obj = crud_user.get_user_by_username(db, username="testuser_token_fixture@example.com")
    assert user_obj is not None
    user_id = user_obj.id

    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = await client.delete(f"{settings.API_V1_STR}/users/{user_id}", headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN # Endpoint is admin only


@pytest.mark.asyncio
async def test_read_users_authenticated_non_admin(client: AsyncClient, test_user_token: str):
    """
    Test accessing /users/ endpoint with a non-admin authenticated user.
    Should fail with 403 as this endpoint is admin-only.
    """
    headers = {"Authorization": f"Bearer {test_user_token}"} # test_user_token is for a regular user
    response = await client.get(f"{settings.API_V1_STR}/users/", headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_read_users_authenticated_admin(client: AsyncClient, db: Session):
    """
    Test accessing /users/ endpoint with an admin authenticated user.
    Should succeed.
    """
    admin_username = "admin_list_users@example.com"
    admin_password = "adminpassword"
    admin_user_in = UserCreate(username=admin_username, email=admin_username, password=admin_password, role=UserRole.ADMIN)
    create_db_user(db, admin_user_in)
    admin_token = await get_user_token(client, admin_username, admin_password)

    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.get(f"{settings.API_V1_STR}/users/", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


# TODO: Add tests for Place, Review, Itinerary CRUD and API endpoints.
# TODO: Test permission logic once fully implemented (e.g., user can only update self, admin can update any) - Partially done for users
