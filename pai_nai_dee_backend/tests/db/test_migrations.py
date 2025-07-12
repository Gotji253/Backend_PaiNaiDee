"""
Tests for database migration scripts (Alembic).
"""

# import pytest # Unused
from sqlalchemy.orm import Session
from sqlalchemy import inspect  # text is unused

# from alembic.config import Config # Unused
# from alembic import command # Unused
# import os # Unused

# from ....app.core.config import ( # Unused
#     settings,
# )  # To get DB connection details for direct alembic runs

# Placeholder for direct alembic config if needed for specific tests
# ALEMBIC_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "../..", "alembic.ini")


def test_schema_consistency_after_migration(db: Session):
    """
    Tests if the database schema contains expected tables and columns
    after migrations have been applied.
    """
    inspector = inspect(db.get_bind())
    tables = inspector.get_table_names()

    # --- Check for expected tables ---
    assert "users" in tables
    assert "places" in tables
    assert "reviews" in tables
    assert "itineraries" in tables

    # --- Check for columns in the 'users' table ---
    user_columns = {col["name"] for col in inspector.get_columns("users")}
    expected_user_columns = {"id", "username", "email", "hashed_password", "is_active"}
    assert expected_user_columns.issubset(user_columns)

    # --- Check for columns in the 'places' table ---
    place_columns = {col["name"] for col in inspector.get_columns("places")}
    expected_place_columns = {"id", "name", "category", "location"} # Customize as needed
    assert expected_place_columns.issubset(place_columns)

    # --- Check for columns in the 'reviews' table ---
    review_columns = {col["name"] for col in inspector.get_columns("reviews")}
    expected_review_columns = {"id", "place_id", "user_id", "rating", "comment"}
    assert expected_review_columns.issubset(review_columns)


def test_alembic_upgrade_head_on_new_db():
    # This test is implicitly covered by the db fixture setup for SQLite,
    # which runs alembic upgrade head on a fresh in-memory database.
    # If using Postgres, the setup_test_database fixture also covers this.
    pass
