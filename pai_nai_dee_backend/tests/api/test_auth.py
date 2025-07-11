import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.schemas.user import UserCreate, User as UserSchema # For response validation
from app.crud import crud_user # For test setup
from app.models.user import User as UserModel # For type hinting current_user

# Fixtures like `client`, `db` are automatically injected by pytest from conftest.py

@pytest.mark.asyncio
async def test_login_for_access_token(client: AsyncClient, db: Session):
    """
    Test login endpoint to get an access token.
    Requires a user to be already created.
    """
    username = "auth_logintestuser" # Use unique username to avoid conflict
    email = "auth_logintestuser@example.com"
    password = "testpassword123"

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
    """
    Test login with an incorrect password.
    """
    username = "auth_loginfailuser" # Unique username
    email = "auth_loginfailuser@example.com"
    password = "correctpassword"

    existing_user = crud_user.get_user_by_username(db, username=username)
    if not existing_user:
        user_in_create = UserCreate(username=username, email=email, password=password)
        crud_user.create_user(db=db, user_in=user_in_create)

    login_data = {"username": username, "password": "wrongpassword"}
    response = await client.post(f"{settings.API_V1_STR}/auth/token", data=login_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    content = response.json()
    assert "detail" in content
    assert "Incorrect username or password" in content["detail"]

@pytest.mark.asyncio
async def test_login_non_existent_user(client: AsyncClient):
    """
    Test login with a username that does not exist.
    """
    login_data = {"username": "nonexistentuser123", "password": "anypassword"}
    response = await client.post(f"{settings.API_V1_STR}/auth/token", data=login_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    content = response.json()
    assert "detail" in content
    assert "Incorrect username or password" in content["detail"]


@pytest.mark.asyncio
async def test_test_token_endpoint_valid_token(client: AsyncClient, test_user_token: str, db: Session):
    """
    Test the /auth/test-token endpoint with a valid token.
    It should return the user's information.
    """
    # We need to know the user associated with test_user_token to verify response.
    # The test_user_token fixture creates "testuser_token_fixture@example.com"
    expected_username = "testuser_token_fixture@example.com"

    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = await client.post(f"{settings.API_V1_STR}/auth/test-token", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    user_info = response.json()
    assert user_info["username"] == expected_username
    assert "email" in user_info # Assuming User schema includes email

@pytest.mark.asyncio
async def test_test_token_endpoint_invalid_token(client: AsyncClient):
    """
    Test the /auth/test-token endpoint with an invalid/malformed token.
    """
    headers = {"Authorization": "Bearer invalidtoken123"}
    response = await client.post(f"{settings.API_V1_STR}/auth/test-token", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    content = response.json()
    assert "detail" in content
    assert "Could not validate credentials" in content["detail"] # Or specific JWT error

@pytest.mark.asyncio
async def test_test_token_endpoint_no_token(client: AsyncClient):
    """
    Test the /auth/test-token endpoint without providing a token.
    """
    response = await client.post(f"{settings.API_V1_STR}/auth/test-token")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    content = response.json()
    assert "detail" in content
    assert "Not authenticated" in content["detail"] # FastAPI's default for missing token

# TODO: Test for expired token. This may require mocking time or adjusting token expiry.
# One way to test expired token:
# 1. Create a token with a very short expiry (e.g., 1 second).
# 2. Wait for longer than the expiry time.
# 3. Make a request with the token.
# This requires `create_access_token` to be accessible or an endpoint that issues tokens with custom expiry.
# For now, this is a placeholder.
# async def test_test_token_endpoint_expired_token(client: AsyncClient, db: Session):
#     from app.core.security import create_access_token # Needs to be importable
#     from datetime import timedelta
#
#     username = "expiredtokenuser"
#     email = "expiredtokenuser@example.com"
#     password = "testpassword"
#
#     user = crud_user.get_user_by_username(db, username=username)
#     if not user:
#         user_in_create = UserCreate(username=username, email=email, password=password)
#         user = crud_user.create_user(db=db, user_in=user_in_create)
#
#     # Create a token that expires in 1 second
#     expired_access_token = create_access_token(
#         data={"sub": user.username}, expires_delta=timedelta(seconds=1)
#     )
#
#     import asyncio
#     await asyncio.sleep(2) # Wait for the token to expire
#
#     headers = {"Authorization": f"Bearer {expired_access_token}"}
#     response = await client.post(f"{settings.API_V1_STR}/auth/test-token", headers=headers)
#     assert response.status_code == status.HTTP_401_UNAUTHORIZED
#     content = response.json()
#     assert "detail" in content
#     assert "Could not validate credentials" in content["detail"] # Or "Token has expired"
#     # The exact message depends on JWT library and FastAPI error handling
#     # Often "Signature has expired" is part of the JWTError caught.
#     # Fastapi might return "Could not validate credentials" generally.
#     # If using `python-jose`, a `jose.exceptions.ExpiredSignatureError` would be raised.
#     # The default credentials_exception in security.py would be raised.
```
