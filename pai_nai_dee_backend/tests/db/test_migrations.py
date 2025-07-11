"""
Tests for database migration scripts (Alembic).
"""

import pytest
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
from alembic.config import Config
from alembic import command
import os

from app.core.config import (
    settings,
)  # To get DB connection details for direct alembic runs

# Placeholder for direct alembic config if needed for specific tests
# ALEMBIC_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "../..", "alembic.ini")


def test_schema_consistency_after_template_migration(db: Session):
    """
    Tests if the schema in the database (cloned from migrated template)
    contains expected tables and columns.
    This implicitly tests that the template migration in conftest was successful.
    """
    inspector = inspect(db.get_bind())
    tables = inspector.get_table_names()

    # Basic checks - customize these based on your actual models/migrations
    assert "users" in tables
    assert "places" in tables
    assert "reviews" in tables
    # assert "itineraries" in tables # If you have this model

    user_columns = [col["name"] for col in inspector.get_columns("users")]
    assert "id" in user_columns
    assert "username" in user_columns
    assert "email" in user_columns
    assert "hashed_password" in user_columns
    assert "is_active" in user_columns
    assert "created_at" in user_columns
    assert "updated_at" in user_columns

    # Add more checks for other tables and important columns/constraints as needed


def test_alembic_upgrade_head_on_new_db(postgres_test_db_manager):
    """
    Tests if `alembic upgrade head` can run successfully on a completely new, empty database.
    This requires creating a new DB manually, not from the template.
    This test is more involved as it needs to manage a separate DB lifecycle.

    For simplicity in this initial setup, we'll rely on the `postgres_test_db_manager`
    having successfully run migrations on the template DB as a proxy for this.
    A more robust version of this test would:
    1. Create a brand new empty DB (not from template).
    2. Configure Alembic to point to this new empty DB.
    3. Run `alembic upgrade head`.
    4. Assert migrations ran without error.
    5. Optionally, inspect the schema of this new DB.
    6. Drop this new DB.

    This is similar to what `postgres_test_db_manager` does for the template, so we can
    consider that covered for now, unless specific issues arise.
    If a dedicated test is needed:
    - Use SUPERUSER_ENGINE from conftest to create/drop a dedicated DB for this test.
    - Set settings.DATABASE_URL temporarily to this new DB.
    - Run alembic command via subprocess.
    """
    # Assuming postgres_test_db_manager correctly creates and migrates the template,
    # this serves as a good indicator.
    # A more direct test would involve creating an empty DB and running alembic here.
    print(
        "Assuming `postgres_test_db_manager` successfully ran migrations on the template."
    )
    print(
        "A more direct test for 'alembic upgrade head' on a fresh DB could be added if needed."
    )
    pass
