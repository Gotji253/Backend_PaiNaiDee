from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ...app.core.config import settings
from ...app.schemas.user import UserCreate
from ..utils.user import create_random_user


def test_create_user(client: TestClient, db_session: Session) -> None:
    username = "testuser"
    password = "testpassword"
    data = {"username": username, "password": password}
    r = client.post(
        f"{settings.API_V1_STR}/users/",
        json=data,
    )
    assert r.status_code == 201
    created_user = r.json()
    assert created_user["username"] == username
    assert "hashed_password" not in created_user


def test_get_users_superuser_me(client: TestClient, db_session: Session) -> None:
    user = create_random_user(db_session)
    # TODO: Create a superuser and test getting all users
    pass


def test_get_existing_user(client: TestClient, db_session: Session) -> None:
    user = create_random_user(db_session)
    # TODO: Log in as the user and get their data
    pass


def test_create_user_existing_username(client: TestClient, db_session: Session) -> None:
    user = create_random_user(db_session)
    data = {"username": user.username, "password": "new_password"}
    r = client.post(
        f"{settings.API_V1_STR}/users/",
        json=data,
    )
    assert r.status_code == 400


def test_retrieve_users(client: TestClient, db_session: Session) -> None:
    create_random_user(db_session)
    create_random_user(db_session)
    # TODO: Log in as a superuser and retrieve all users
    pass
