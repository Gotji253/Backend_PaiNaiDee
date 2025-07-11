"""
Tests for database triggers and constraints.
"""

import pytest
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError  # To catch constraint violations

from app.models.user import User
from app.models.place import Place
from app.models.review import Review


def test_prevent_duplicate_review_trigger_or_constraint(db: Session):
    """
    Tests that a user cannot review the same place twice.
    This relies on a database trigger or a unique constraint (e.g., UNIQUE(user_id, place_id))
    on the 'reviews' table.
    """
    # 1. Setup: Create a User and a Place
    user1 = User(
        username="user_for_trigger_test",
        email="user_trigger@example.com",
        hashed_password="password_trigger",
    )
    db.add(user1)
    place1 = Place(name="Test Place for Trigger", category="Trigger Category")
    db.add(place1)
    db.commit()  # Commit to get IDs

    # 2. Action 1: Add the first review (should succeed)
    review1 = Review(
        user_id=user1.id,
        place_id=place1.id,
        rating=4.0,
        comment="First review, should work.",
    )
    db.add(review1)
    db.commit()

    # Verify the first review was added
    retrieved_review = db.query(Review).filter(Review.id == review1.id).first()
    assert retrieved_review is not None
    assert retrieved_review.comment == "First review, should work."

    # 3. Action 2: Attempt to add a duplicate review (should fail)
    duplicate_review = Review(
        user_id=user1.id,  # Same user
        place_id=place1.id,  # Same place
        rating=2.0,
        comment="Second review by same user for same place, should fail.",
    )
    db.add(duplicate_review)

    # 4. Assert: Check for IntegrityError upon commit
    with pytest.raises(IntegrityError) as excinfo:
        db.commit()  # This should violate the unique constraint or trigger a custom error

    # Rollback the session to a clean state after the expected error
    db.rollback()

    # Optional: Check the error message if it's a custom trigger error.
    # For a standard unique constraint, the message might vary by DB.
    # e.g., for PostgreSQL's unique constraint:
    # assert "uq_user_place_review" in str(excinfo.value).lower() or \
    #        "unique constraint" in str(excinfo.value).lower()
    # print(f"Caught expected IntegrityError: {excinfo.value}")

    # Verify that the duplicate review was not actually added
    review_count_after_attempt = (
        db.query(Review)
        .filter(Review.user_id == user1.id, Review.place_id == place1.id)
        .count()
    )
    assert (
        review_count_after_attempt == 1
    ), "Duplicate review should not have been saved."


# Placeholder for another trigger test, e.g., audit log or booking status change
# def test_audit_log_trigger_on_place_update(db: Session):
#     # 1. Setup: Create a place
#     place = Place(name="Place to Audit", category="Audit")
#     db.add(place)
#     db.commit()
#
#     # 2. Action: Update the place (assuming this fires an audit log trigger)
#     place.name = "Place to Audit (Updated)"
#     place.category = "Audited Category"
#     db.commit()
#
#     # 3. Assert: Check the audit log table for new entries related to this update
#     # audit_logs = db.execute(
#     #     text("SELECT * FROM audit_log_table WHERE table_name = 'places' AND record_id = :place_id ORDER BY timestamp DESC"),
#     #     {"place_id": place.id}
#     # ).fetchall()
#     #
#     # assert len(audit_logs) >= 1
#     # assert audit_logs[0].action == "UPDATE"
#     # assert "name" in audit_logs[0].changed_fields # Or however changes are logged
#     # assert audit_logs[0].old_values["name"] == "Place to Audit"
#     # assert audit_logs[0].new_values["name"] == "Place to Audit (Updated)"
#     pass
#
# def test_booking_status_change_validation_trigger(db: Session):
#     # This would depend on having a 'bookings' table and a trigger that validates
#     # transitions between statuses (e.g., 'pending' -> 'confirmed' is OK,
#     # but 'confirmed' -> 'cancelled' might have conditions or logging).
#     pass
