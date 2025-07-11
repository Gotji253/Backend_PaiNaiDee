import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.config import settings
from app.schemas.user import UserCreate, UserRole
from app.schemas.place import PlaceCreate, PlaceUpdate
from app.crud import crud_user, crud_place # For test setup
from app.models.place import Place as PlaceModel

# Helper function to create a user directly via CRUD for test setup
def create_db_user_with_role(db: Session, username: str, email: str, password: str, role: UserRole) -> crud_user.User:
    user_in = UserCreate(username=username, email=email, password=password, role=role)
    return crud_user.create_user(db, user_in=user_in)

# Helper function to get a token for a specific user
async def get_auth_token_for_user(client: AsyncClient, username: str, password: str) -> str:
    login_data = {"username": username, "password": password}
    response = await client.post(f"{settings.API_V1_STR}/auth/token", data=login_data)
    assert response.status_code == status.HTTP_200_OK, f"Failed to log in user {username}. Response: {response.text}"
    return response.json()["access_token"]

@pytest.fixture(scope="module")
async def admin_token(client: AsyncClient, db: Session) -> str:
    username = "place_admin_user@example.com"
    password = "adminpassword"
    # Ensure user exists and is admin
    user = crud_user.get_user_by_username(db, username=username)
    if not user:
        user = create_db_user_with_role(db, username, username, password, UserRole.ADMIN)
    elif user.role != UserRole.ADMIN: # Ensure existing user is admin for this test module
        user.role = UserRole.ADMIN
        db.add(user)
        db.commit()
        db.refresh(user)
    return await get_auth_token_for_user(client, username, password)

@pytest.fixture(scope="module")
async def editor_token(client: AsyncClient, db: Session) -> str:
    username = "place_editor_user@example.com"
    password = "editorpassword"
    user = crud_user.get_user_by_username(db, username=username)
    if not user:
        user = create_db_user_with_role(db, username, username, password, UserRole.EDITOR)
    elif user.role != UserRole.EDITOR:
         user.role = UserRole.EDITOR
         db.add(user)
         db.commit()
         db.refresh(user)
    return await get_auth_token_for_user(client, username, password)

@pytest.fixture(scope="module")
async def regular_user_token(client: AsyncClient, db: Session) -> str:
    # This reuses the logic from conftest's test_user_token if available and suitable,
    # or creates a specific one for place tests.
    # For simplicity, creating one here to ensure role is USER.
    username = "place_regular_user@example.com"
    password = "regularpassword"
    user = crud_user.get_user_by_username(db, username=username)
    if not user:
        user = create_db_user_with_role(db, username, username, password, UserRole.USER)
    elif user.role != UserRole.USER: # Ensure role is USER
        user.role = UserRole.USER
        db.add(user)
        db.commit()
        db.refresh(user)
    return await get_auth_token_for_user(client, username, password)


place_data_valid: Dict[str, Any] = {
    "name": "Test Place Alpha",
    "description": "A nice place for testing.",
    "category": "Testing Ground",
    "latitude": 13.7563,
    "longitude": 100.5018,
    "address": "123 Test St, Bangkok",
}

@pytest.mark.asyncio
async def test_create_place_as_admin(client: AsyncClient, admin_token: str, db: Session):
    response = await client.post(
        f"{settings.API_V1_STR}/places/",
        json=place_data_valid,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == place_data_valid["name"]
    assert data["category"] == place_data_valid["category"]
    # Clean up created place
    crud_place.delete_place(db, place_id=data["id"])


@pytest.mark.asyncio
async def test_create_place_as_editor(client: AsyncClient, editor_token: str, db: Session):
    response = await client.post(
        f"{settings.API_V1_STR}/places/",
        json={**place_data_valid, "name": "Test Place Beta by Editor"},
        headers={"Authorization": f"Bearer {editor_token}"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Test Place Beta by Editor"
    crud_place.delete_place(db, place_id=data["id"])


@pytest.mark.asyncio
async def test_create_place_as_regular_user_forbidden(client: AsyncClient, regular_user_token: str):
    response = await client.post(
        f"{settings.API_V1_STR}/places/",
        json={**place_data_valid, "name": "Test Place Gamma by User"},
        headers={"Authorization": f"Bearer {regular_user_token}"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.asyncio
async def test_create_place_unauthenticated(client: AsyncClient):
    response = await client.post(
        f"{settings.API_V1_STR}/places/",
        json={**place_data_valid, "name": "Test Place Delta Unauth"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_read_places_public(client: AsyncClient, db: Session):
    # Create a place first to ensure list is not empty
    created_place = crud_place.create_place(db, place_in=PlaceCreate(**place_data_valid))

    response = await client.get(f"{settings.API_V1_STR}/places/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any(p["id"] == created_place.id for p in data)

    crud_place.delete_place(db, place_id=created_place.id)


@pytest.mark.asyncio
async def test_read_place_by_id_public(client: AsyncClient, db: Session):
    place_in = PlaceCreate(**{**place_data_valid, "name": "Public Read Place"})
    created_place = crud_place.create_place(db, place_in=place_in)

    response = await client.get(f"{settings.API_V1_STR}/places/{created_place.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == created_place.id
    assert data["name"] == "Public Read Place"

    crud_place.delete_place(db, place_id=created_place.id)

@pytest.mark.asyncio
async def test_read_place_by_id_not_found(client: AsyncClient):
    response = await client.get(f"{settings.API_V1_STR}/places/999999") # Non-existent ID
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_update_place_as_admin(client: AsyncClient, admin_token: str, db: Session):
    place_in = PlaceCreate(**{**place_data_valid, "name": "Place to Update (Admin)"})
    created_place = crud_place.create_place(db, place_in=place_in)

    update_payload = {"description": "Updated by Admin", "category": "Admin Category"}
    response = await client.put(
        f"{settings.API_V1_STR}/places/{created_place.id}",
        json=update_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["description"] == "Updated by Admin"
    assert data["category"] == "Admin Category"

    crud_place.delete_place(db, place_id=created_place.id)

@pytest.mark.asyncio
async def test_update_place_as_editor(client: AsyncClient, editor_token: str, db: Session):
    place_in = PlaceCreate(**{**place_data_valid, "name": "Place to Update (Editor)"})
    created_place = crud_place.create_place(db, place_in=place_in)

    update_payload = {"description": "Updated by Editor"}
    response = await client.put(
        f"{settings.API_V1_STR}/places/{created_place.id}",
        json=update_payload,
        headers={"Authorization": f"Bearer {editor_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["description"] == "Updated by Editor"

    crud_place.delete_place(db, place_id=created_place.id)


@pytest.mark.asyncio
async def test_update_place_as_regular_user_forbidden(client: AsyncClient, regular_user_token: str, db: Session):
    place_in = PlaceCreate(**{**place_data_valid, "name": "Place No Update (User)"})
    created_place = crud_place.create_place(db, place_in=place_in)

    update_payload = {"description": "Attempted Update by User"}
    response = await client.put(
        f"{settings.API_V1_STR}/places/{created_place.id}",
        json=update_payload,
        headers={"Authorization": f"Bearer {regular_user_token}"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

    crud_place.delete_place(db, place_id=created_place.id)


@pytest.mark.asyncio
async def test_update_place_not_found(client: AsyncClient, admin_token: str):
    update_payload = {"description": "Update Non Existent"}
    response = await client.put(
        f"{settings.API_V1_STR}/places/999999",
        json=update_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_place_as_admin(client: AsyncClient, admin_token: str, db: Session):
    place_in = PlaceCreate(**{**place_data_valid, "name": "Place to Delete (Admin)"})
    created_place = crud_place.create_place(db, place_in=place_in)

    response = await client.delete(
        f"{settings.API_V1_STR}/places/{created_place.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK

    # Verify deleted
    deleted_in_db = crud_place.get_place(db, place_id=created_place.id)
    assert deleted_in_db is None

@pytest.mark.asyncio
async def test_delete_place_as_editor_forbidden(client: AsyncClient, editor_token: str, db: Session):
    place_in = PlaceCreate(**{**place_data_valid, "name": "Place No Delete (Editor)"})
    created_place = crud_place.create_place(db, place_in=place_in)

    response = await client.delete(
        f"{settings.API_V1_STR}/places/{created_place.id}",
        headers={"Authorization": f"Bearer {editor_token}"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

    crud_place.delete_place(db, place_id=created_place.id) # Clean up

@pytest.mark.asyncio
async def test_delete_place_not_found(client: AsyncClient, admin_token: str):
    response = await client.delete(
        f"{settings.API_V1_STR}/places/999999",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

```
