"""
Tests for database stored procedures and functions.
"""

import pytest
from sqlalchemy.orm import Session
from sqlalchemy import text
import decimal  # For handling NUMERIC type from PostgreSQL

from ...app.models.user import User
from ...app.models.place import Place
from ...app.models.review import Review


def test_calculate_average_rating(db: Session):
    """
    Tests the calculate_average_rating(place_id) SQL function.
    Assumes the function is already created in the database via migrations.
    """
    # 1. Setup: Create Users, a Place, and Reviews
    user1 = User(
        username="user1_for_rating_test",
        email="user1_rating@example.com",
        hashed_password="password1",
    )
    user2 = User(
        username="user2_for_rating_test",
        email="user2_rating@example.com",
        hashed_password="password2",
    )
    db.add_all([user1, user2])
    db.commit()  # Commit users to get their IDs

    place1 = Place(name="Test Place for Rating", category="Test Category")
    db.add(place1)
    db.commit()  # Commit place to get its ID

    # Reviews for place1
    review1_p1 = Review(
        place_id=place1.id, user_id=user1.id, rating=5.0, comment="Excellent!"
    )
    review2_p1 = Review(
        place_id=place1.id, user_id=user2.id, rating=3.0, comment="Okay"
    )
    db.add_all([review1_p1, review2_p1])
    db.commit()

    # 2. Execute: Call the stored function
    # Note: The function name in SQL might be case-sensitive depending on how it was created.
    # Assuming it's lowercase 'calculate_average_rating'.
    sql_query = text("SELECT calculate_average_rating(:place_id)")
    result = db.execute(sql_query, {"place_id": place1.id}).scalar_one_or_none()

    # 3. Assert: Check the result
    # Average of 5.0 and 3.0 is 4.0
    assert result is not None, "The function should return a value, not NULL."
    # PSQL NUMERIC might come back as Decimal
    assert isinstance(result, decimal.Decimal) or isinstance(
        result, float
    ), "Result should be a numeric type"
    assert float(result) == pytest.approx(4.0)

    # Test case: No reviews for a place
    place2 = Place(name="Test Place No Reviews", category="Test Category")
    db.add(place2)
    db.commit()

    result_no_reviews = db.execute(
        sql_query, {"place_id": place2.id}
    ).scalar_one_or_none()
    assert result_no_reviews is not None
    assert float(result_no_reviews) == pytest.approx(
        0.0
    ), "Should return 0 for a place with no reviews."

    # Test case: Place does not exist
    non_existent_place_id = 99999
    result_non_existent = db.execute(
        sql_query, {"place_id": non_existent_place_id}
    ).scalar_one_or_none()
    assert result_non_existent is not None
    assert float(result_non_existent) == pytest.approx(
        0.0
    ), "Should return 0 for a non-existent place_id."

    # Test case: Add another review and check if average updates
    user3 = User(
        username="user3_for_rating_test",
        email="user3_rating@example.com",
        hashed_password="password3",
    )
    db.add(user3)
    db.commit()
    review3_p1 = Review(place_id=place1.id, user_id=user3.id, rating=1.0, comment="Bad")
    db.add(review3_p1)
    db.commit()

    result_updated = db.execute(sql_query, {"place_id": place1.id}).scalar_one_or_none()
    # Average of 5.0, 3.0, 1.0 is (5+3+1)/3 = 9/3 = 3.0
    assert result_updated is not None
    assert float(result_updated) == pytest.approx(3.0)


# Placeholder for recommend_place_for_user
# This would be more complex and depend on the exact logic of the SQL function.
# def test_recommend_place_for_user(db: Session):
#     # Setup:
#     # - Create users with different review histories or preferences (if applicable)
#     # - Create places with various categories, ratings
#     # - Create reviews linking users to places
#
#     user_target = User(username="target_user_recommend", email="target_rec@example.com", hashed_password="pw")
#     db.add(user_target)
#     db.commit()
#
#     # Example: A simple recommendation might be "places not reviewed by user_target with high average rating"
#     # The actual SQL function `recommend_place_for_user` needs to be defined.
#     # e.g., CREATE FUNCTION recommend_place_for_user(p_user_id INTEGER) RETURNS SETOF places AS ...
#
#     # sql_query = text("SELECT * FROM recommend_place_for_user(:user_id)")
#     # recommendations = db.execute(sql_query, {"user_id": user_target.id}).fetchall()
#
#     # Assert:
#     # - Check that recommended places are valid (e.g., exist, meet criteria)
#     # - Check that places already reviewed by user_target are not in recommendations (if that's the logic)
#     # - Check the order of recommendations (if applicable)
#     pass
