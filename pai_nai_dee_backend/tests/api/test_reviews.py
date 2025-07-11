import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.config import settings
from app.schemas.user import UserCreate, UserRole
from app.schemas.place import PlaceCreate
from app.schemas.review import ReviewCreate, ReviewUpdate
from app.crud import crud_user, crud_place, crud_review
from app.models.user import User as UserModel
from app.models.place import Place as PlaceModel
from app.models.review import Review as ReviewModel


# Helper function to create a user and get their token
async def create_user_and_get_token(client: AsyncClient, db: Session, username_prefix: str, role: UserRole) -> tuple[str, UserModel]:
    username = f"{username_prefix}_{role.value}@example.com"
    password = "testpassword"

    user = crud_user.get_user_by_username(db, username=username)
    if not user:
        user_in = UserCreate(username=username, email=username, password=password, role=role)
        user = crud_user.create_user(db, user_in=user_in)
    elif user.role != role: # Ensure role is correct if user exists
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
async def review_admin_user_token_and_obj(client: AsyncClient, db: Session) -> tuple[str, UserModel]:
    return await create_user_and_get_token(client, db, "review_admin", UserRole.ADMIN)

@pytest.fixture(scope="module")
async def review_user_token_and_obj(client: AsyncClient, db: Session) -> tuple[str, UserModel]:
    return await create_user_and_get_token(client, db, "review_user_normal", UserRole.USER)

@pytest.fixture(scope="module")
async def review_other_user_token_and_obj(client: AsyncClient, db: Session) -> tuple[str, UserModel]:
    return await create_user_and_get_token(client, db, "review_other_user", UserRole.USER)

@pytest.fixture(scope="function") # Function scope to get a fresh place for each test
def test_place(db: Session) -> PlaceModel:
    place_data = PlaceCreate(
        name="Test Place for Reviews",
        description="A place specifically for testing reviews.",
        category="Testing Category",
        latitude=10.0,
        longitude=20.0,
        address="1 Test Review Rd"
    )
    place = crud_place.create_place(db, place_in=place_data)
    yield place
    # Teardown: delete the place and its reviews (cascade should handle reviews)
    crud_place.delete_place(db, place_id=place.id)


review_data_valid: Dict[str, Any] = {
    "rating": 4.5,
    "comment": "This place is great for testing reviews!",
}

@pytest.mark.asyncio
async def test_create_review_for_place(client: AsyncClient, review_user_token_and_obj: tuple[str, UserModel], test_place: PlaceModel, db: Session):
    token, user_obj = review_user_token_and_obj

    payload = {**review_data_valid, "place_id": test_place.id}

    response = await client.post(
        f"{settings.API_V1_STR}/reviews/",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["rating"] == review_data_valid["rating"]
    assert data["comment"] == review_data_valid["comment"]
    assert data["user_id"] == user_obj.id
    assert data["place_id"] == test_place.id

    # Check average rating update
    db.refresh(test_place) # Refresh to get updated average_rating
    assert test_place.average_rating == review_data_valid["rating"] # First review sets it directly

@pytest.mark.asyncio
async def test_create_review_for_non_existent_place(client: AsyncClient, review_user_token_and_obj: tuple[str, UserModel]):
    token, _ = review_user_token_and_obj
    payload = {**review_data_valid, "place_id": 999999} # Non-existent place
    response = await client.post(
        f"{settings.API_V1_STR}/reviews/",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND # Service should raise 404 for place

@pytest.mark.asyncio
async def test_read_reviews_for_place(client: AsyncClient, test_place: PlaceModel, db: Session, review_user_token_and_obj: tuple[str, UserModel]):
    token, user_obj = review_user_token_and_obj
    # Create a review first
    review = crud_review.create_review(db, review_in=ReviewCreate(place_id=test_place.id, **review_data_valid), user_id=user_obj.id)

    response = await client.get(f"{settings.API_V1_STR}/reviews/place/{test_place.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(r["id"] == review.id for r in data)

@pytest.mark.asyncio
async def test_read_reviews_by_user_self(client: AsyncClient, test_place: PlaceModel, db: Session, review_user_token_and_obj: tuple[str, UserModel]):
    token, user_obj = review_user_token_and_obj
    review = crud_review.create_review(db, review_in=ReviewCreate(place_id=test_place.id, **review_data_valid), user_id=user_obj.id)

    response = await client.get(f"{settings.API_V1_STR}/reviews/user/{user_obj.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert any(r["id"] == review.id for r in data)

@pytest.mark.asyncio
async def test_read_reviews_by_user_admin_can_read_other(client: AsyncClient, test_place: PlaceModel, db: Session, review_admin_user_token_and_obj: tuple[str, UserModel], review_user_token_and_obj: tuple[str, UserModel]):
    admin_token, _ = review_admin_user_token_and_obj
    _, regular_user_obj = review_user_token_and_obj # User whose reviews are being read

    crud_review.create_review(db, review_in=ReviewCreate(place_id=test_place.id, **review_data_valid), user_id=regular_user_obj.id)

    response = await client.get(f"{settings.API_V1_STR}/reviews/user/{regular_user_obj.id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
async def test_read_reviews_by_user_other_user_forbidden(client: AsyncClient, db: Session, review_user_token_and_obj: tuple[str, UserModel], review_other_user_token_and_obj: tuple[str, UserModel]):
    _, user_to_view = review_user_token_and_obj # The user whose reviews we want to view
    other_token, _ = review_other_user_token_and_obj # The user trying to view them

    response = await client.get(f"{settings.API_V1_STR}/reviews/user/{user_to_view.id}", headers={"Authorization": f"Bearer {other_token}"})
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.asyncio
async def test_update_review_by_author(client: AsyncClient, test_place: PlaceModel, db: Session, review_user_token_and_obj: tuple[str, UserModel]):
    token, user_obj = review_user_token_and_obj
    review = crud_review.create_review(db, review_in=ReviewCreate(place_id=test_place.id, **review_data_valid), user_id=user_obj.id)

    update_payload = {"rating": 1.0, "comment": "Updated review comment"}
    response = await client.put(
        f"{settings.API_V1_STR}/reviews/{review.id}",
        json=update_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["rating"] == 1.0
    assert data["comment"] == "Updated review comment"

    db.refresh(test_place)
    assert test_place.average_rating == 1.0 # Rating updated

@pytest.mark.asyncio
async def test_update_review_by_other_user_forbidden(client: AsyncClient, test_place: PlaceModel, db: Session, review_user_token_and_obj: tuple[str, UserModel], review_other_user_token_and_obj: tuple[str, UserModel]):
    _, author_obj = review_user_token_and_obj
    other_token, _ = review_other_user_token_and_obj

    review = crud_review.create_review(db, review_in=ReviewCreate(place_id=test_place.id, **review_data_valid), user_id=author_obj.id)

    update_payload = {"comment": "Attempted update by other user"}
    response = await client.put(
        f"{settings.API_V1_STR}/reviews/{review.id}",
        json=update_payload,
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_delete_review_by_author(client: AsyncClient, test_place: PlaceModel, db: Session, review_user_token_and_obj: tuple[str, UserModel]):
    token, user_obj = review_user_token_and_obj
    review = crud_review.create_review(db, review_in=ReviewCreate(place_id=test_place.id, rating=3.0, comment="To be deleted by author"), user_id=user_obj.id)
    # Create another review to test average rating calculation after deletion
    crud_review.create_review(db, review_in=ReviewCreate(place_id=test_place.id, rating=5.0, comment="Stays"), user_id=user_obj.id)
    db.refresh(test_place)
    assert test_place.average_rating == 4.0 # (3+5)/2

    response = await client.delete(
        f"{settings.API_V1_STR}/reviews/{review.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_200_OK

    assert crud_review.get_review(db, review.id) is None
    db.refresh(test_place)
    assert test_place.average_rating == 5.0 # Only the 5.0 rating review remains


@pytest.mark.asyncio
async def test_delete_review_by_admin(client: AsyncClient, test_place: PlaceModel, db: Session, review_admin_user_token_and_obj: tuple[str, UserModel], review_user_token_and_obj: tuple[str, UserModel]):
    admin_token, _ = review_admin_user_token_and_obj
    _, author_obj = review_user_token_and_obj # Review author

    review = crud_review.create_review(db, review_in=ReviewCreate(place_id=test_place.id, rating=2.0, comment="To be deleted by admin"), user_id=author_obj.id)
    crud_review.create_review(db, review_in=ReviewCreate(place_id=test_place.id, rating=4.0, comment="Stays after admin delete"), user_id=author_obj.id)
    db.refresh(test_place)
    assert test_place.average_rating == 3.0 # (2+4)/2

    response = await client.delete(
        f"{settings.API_V1_STR}/reviews/{review.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK

    assert crud_review.get_review(db, review.id) is None
    db.refresh(test_place)
    assert test_place.average_rating == 4.0 # Only the 4.0 rating review remains

@pytest.mark.asyncio
async def test_delete_review_by_other_user_forbidden(client: AsyncClient, test_place: PlaceModel, db: Session, review_user_token_and_obj: tuple[str, UserModel], review_other_user_token_and_obj: tuple[str, UserModel]):
    _, author_obj = review_user_token_and_obj
    other_token, _ = review_other_user_token_and_obj

    review = crud_review.create_review(db, review_in=ReviewCreate(place_id=test_place.id, **review_data_valid), user_id=author_obj.id)

    response = await client.delete(
        f"{settings.API_V1_STR}/reviews/{review.id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

```
