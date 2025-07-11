import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.orm import Session
from typing import List

from app.core.config import settings
from app.schemas.user import UserCreate, UserRole
from app.schemas.place import PlaceCreate
from app.schemas.itinerary import ItineraryCreate, ItineraryUpdate
from app.crud import crud_user, crud_place, crud_itinerary
from app.models.user import User as UserModel
from app.models.place import Place as PlaceModel
from app.models.itinerary import Itinerary as ItineraryModel


# Helper function to create a user and get their token
async def create_itinerary_user_and_get_token(client: AsyncClient, db: Session, username_prefix: str, role: UserRole) -> tuple[str, UserModel]:
    username = f"{username_prefix}_{role.value}_itin@example.com"
    password = "testpassword"

    user = crud_user.get_user_by_username(db, username=username)
    if not user:
        user_in = UserCreate(username=username, email=username, password=password, role=role)
        user = crud_user.create_user(db, user_in=user_in)
    elif user.role != role:
        user.role = role
        db.add(user)
        db.commit()
        db.refresh(user)

    login_data = {"username": username, "password": password}
    response = await client.post(f"{settings.API_V1_STR}/auth/token", data=login_data)
    assert response.status_code == status.HTTP_200_OK
    token = response.json()["access_token"]
    return token, user

@pytest.fixture(scope="module")
async def itinerary_admin_user(client: AsyncClient, db: Session) -> tuple[str, UserModel]:
    return await create_itinerary_user_and_get_token(client, db, "itin_admin", UserRole.ADMIN)

@pytest.fixture(scope="module")
async def itinerary_owner_user(client: AsyncClient, db: Session) -> tuple[str, UserModel]:
    return await create_itinerary_user_and_get_token(client, db, "itin_owner", UserRole.USER)

@pytest.fixture(scope="module")
async def itinerary_other_user(client: AsyncClient, db: Session) -> tuple[str, UserModel]:
    return await create_itinerary_user_and_get_token(client, db, "itin_other", UserRole.USER)

@pytest.fixture(scope="function")
def sample_places(db: Session) -> List[PlaceModel]:
    places_data = [
        PlaceCreate(name="Itin Place 1", category="Test", latitude=1.0, longitude=1.0, address="Addr 1"),
        PlaceCreate(name="Itin Place 2", category="Test", latitude=2.0, longitude=2.0, address="Addr 2"),
    ]
    created_places = [crud_place.create_place(db, place_in=pd) for pd in places_data]
    yield created_places
    for place in created_places:
        crud_place.delete_place(db, place_id=place.id) # Clean up places

itinerary_data_valid = {
    "name": "My Awesome Test Itinerary",
    "description": "Testing itinerary creation.",
}

@pytest.mark.asyncio
async def test_create_itinerary(client: AsyncClient, itinerary_owner_user: tuple[str, UserModel], sample_places: List[PlaceModel]):
    owner_token, _ = itinerary_owner_user
    place_ids = [p.id for p in sample_places]
    payload = {**itinerary_data_valid, "place_ids": place_ids}

    response = await client.post(
        f"{settings.API_V1_STR}/itineraries/",
        json=payload,
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == itinerary_data_valid["name"]
    assert len(data["places_in_itinerary"]) == len(place_ids)
    retrieved_place_ids = sorted([p["id"] for p in data["places_in_itinerary"]])
    assert retrieved_place_ids == sorted(place_ids)


@pytest.mark.asyncio
async def test_create_itinerary_with_non_existent_place(client: AsyncClient, itinerary_owner_user: tuple[str, UserModel], sample_places: List[PlaceModel]):
    owner_token, _ = itinerary_owner_user
    valid_place_id = sample_places[0].id
    payload = {**itinerary_data_valid, "name": "Itin Bad Place", "place_ids": [valid_place_id, 999999]} # 999999 is non-existent

    response = await client.post(
        f"{settings.API_V1_STR}/itineraries/",
        json=payload,
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND # Service should check place existence


@pytest.mark.asyncio
async def test_read_my_itineraries(client: AsyncClient, db: Session, itinerary_owner_user: tuple[str, UserModel], sample_places: List[PlaceModel]):
    owner_token, owner_obj = itinerary_owner_user
    # Create an itinerary for this user
    crud_itinerary.create_itinerary(db, itinerary_in=ItineraryCreate(place_ids=[p.id for p in sample_places], **itinerary_data_valid), user_id=owner_obj.id)

    response = await client.get(f"{settings.API_V1_STR}/itineraries/my-itineraries", headers={"Authorization": f"Bearer {owner_token}"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert all(item["user_id"] == owner_obj.id for item in data)


@pytest.mark.asyncio
async def test_read_itinerary_by_id_owner(client: AsyncClient, db: Session, itinerary_owner_user: tuple[str, UserModel], sample_places: List[PlaceModel]):
    owner_token, owner_obj = itinerary_owner_user
    itinerary = crud_itinerary.create_itinerary(db, itinerary_in=ItineraryCreate(place_ids=[p.id for p in sample_places], **itinerary_data_valid), user_id=owner_obj.id)

    response = await client.get(f"{settings.API_V1_STR}/itineraries/{itinerary.id}", headers={"Authorization": f"Bearer {owner_token}"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == itinerary.id

@pytest.mark.asyncio
async def test_read_itinerary_by_id_admin(client: AsyncClient, db: Session, itinerary_admin_user: tuple[str, UserModel], itinerary_owner_user: tuple[str, UserModel], sample_places: List[PlaceModel]):
    admin_token, _ = itinerary_admin_user
    _, owner_obj = itinerary_owner_user # Itinerary belongs to this user
    itinerary = crud_itinerary.create_itinerary(db, itinerary_in=ItineraryCreate(place_ids=[p.id for p in sample_places], **itinerary_data_valid), user_id=owner_obj.id)

    response = await client.get(f"{settings.API_V1_STR}/itineraries/{itinerary.id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == status.HTTP_200_OK # Admin can read others
    data = response.json()
    assert data["id"] == itinerary.id

@pytest.mark.asyncio
async def test_read_itinerary_by_id_other_user_forbidden(client: AsyncClient, db: Session, itinerary_owner_user: tuple[str, UserModel], itinerary_other_user: tuple[str, UserModel], sample_places: List[PlaceModel]):
    _, owner_obj = itinerary_owner_user
    other_token, _ = itinerary_other_user
    itinerary = crud_itinerary.create_itinerary(db, itinerary_in=ItineraryCreate(place_ids=[p.id for p in sample_places], **itinerary_data_valid), user_id=owner_obj.id)

    response = await client.get(f"{settings.API_V1_STR}/itineraries/{itinerary.id}", headers={"Authorization": f"Bearer {other_token}"})
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_update_itinerary_owner(client: AsyncClient, db: Session, itinerary_owner_user: tuple[str, UserModel], sample_places: List[PlaceModel]):
    owner_token, owner_obj = itinerary_owner_user
    itinerary = crud_itinerary.create_itinerary(db, itinerary_in=ItineraryCreate(place_ids=[sample_places[0].id], **itinerary_data_valid), user_id=owner_obj.id)

    update_payload = {"name": "Updated Itinerary Name", "place_ids": [sample_places[1].id]}
    response = await client.put(
        f"{settings.API_V1_STR}/itineraries/{itinerary.id}",
        json=update_payload,
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Updated Itinerary Name"
    assert len(data["places_in_itinerary"]) == 1
    assert data["places_in_itinerary"][0]["id"] == sample_places[1].id

@pytest.mark.asyncio
async def test_delete_itinerary_owner(client: AsyncClient, db: Session, itinerary_owner_user: tuple[str, UserModel], sample_places: List[PlaceModel]):
    owner_token, owner_obj = itinerary_owner_user
    itinerary = crud_itinerary.create_itinerary(db, itinerary_in=ItineraryCreate(place_ids=[p.id for p in sample_places], **itinerary_data_valid), user_id=owner_obj.id)

    response = await client.delete(f"{settings.API_V1_STR}/itineraries/{itinerary.id}", headers={"Authorization": f"Bearer {owner_token}"})
    assert response.status_code == status.HTTP_200_OK
    assert crud_itinerary.get_itinerary(db, itinerary_id=itinerary.id) is None

@pytest.mark.asyncio
async def test_delete_itinerary_admin(client: AsyncClient, db: Session, itinerary_admin_user: tuple[str, UserModel], itinerary_owner_user: tuple[str, UserModel], sample_places: List[PlaceModel]):
    admin_token, _ = itinerary_admin_user
    _, owner_obj = itinerary_owner_user
    itinerary = crud_itinerary.create_itinerary(db, itinerary_in=ItineraryCreate(place_ids=[p.id for p in sample_places], **itinerary_data_valid), user_id=owner_obj.id)

    response = await client.delete(f"{settings.API_V1_STR}/itineraries/{itinerary.id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == status.HTTP_200_OK # Admin can delete
    assert crud_itinerary.get_itinerary(db, itinerary_id=itinerary.id) is None


@pytest.mark.asyncio
async def test_add_place_to_itinerary(client: AsyncClient, db: Session, itinerary_owner_user: tuple[str, UserModel], sample_places: List[PlaceModel]):
    owner_token, owner_obj = itinerary_owner_user
    # Create itinerary with only the first place
    itinerary = crud_itinerary.create_itinerary(db, itinerary_in=ItineraryCreate(name="Itin for Add/Remove", place_ids=[sample_places[0].id]), user_id=owner_obj.id)

    second_place_id = sample_places[1].id
    response = await client.post(
        f"{settings.API_V1_STR}/itineraries/{itinerary.id}/places/{second_place_id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    place_ids_in_response = sorted([p["id"] for p in data["places_in_itinerary"]])
    assert sorted([sample_places[0].id, second_place_id]) == place_ids_in_response


@pytest.mark.asyncio
async def test_remove_place_from_itinerary(client: AsyncClient, db: Session, itinerary_owner_user: tuple[str, UserModel], sample_places: List[PlaceModel]):
    owner_token, owner_obj = itinerary_owner_user
    # Create itinerary with both places
    itinerary = crud_itinerary.create_itinerary(db, itinerary_in=ItineraryCreate(name="Itin for Remove", place_ids=[p.id for p in sample_places]), user_id=owner_obj.id)

    place_to_remove_id = sample_places[0].id
    response = await client.delete(
        f"{settings.API_V1_STR}/itineraries/{itinerary.id}/places/{place_to_remove_id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["places_in_itinerary"]) == 1
    assert data["places_in_itinerary"][0]["id"] == sample_places[1].id

```
