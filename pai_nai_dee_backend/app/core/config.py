from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import model_validator  # Moved to top-level


class Settings(BaseSettings):
    PROJECT_NAME: str = "Pai Nai Dee API"
    PROJECT_VERSION: str = "0.1.0"

    # --- Development Database Settings ---
    POSTGRES_USER: str = "your_db_user"
    POSTGRES_PASSWORD: str = "your_db_password"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "pai_nai_dee_db"
    DATABASE_URL: Optional[str] = None

    # --- Test Environment Settings ---
    USE_POSTGRES_FOR_TESTS: bool = False

    # --- PostgreSQL Test Settings ---
    TEST_POSTGRES_USER: str = "test_user"
    TEST_POSTGRES_PASSWORD: str = "test_password"
    TEST_POSTGRES_SERVER: str = "localhost"
    TEST_POSTGRES_PORT: str = "5433"
    TEST_POSTGRES_DB_MAIN: str = "pai_nai_dee_test_template"

    # --- Test Database URL ---
    # This will be dynamically set based on whether we are using Postgres or SQLite for tests.
    TEST_DATABASE_URL: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def build_database_urls(cls, values: dict) -> dict:
        # --- Build Development DATABASE_URL ---
        if values.get("DATABASE_URL") is None:
            values["DATABASE_URL"] = (
                f"postgresql://{values.get('POSTGRES_USER')}:{values.get('POSTGRES_PASSWORD')}@{values.get('POSTGRES_SERVER')}:{values.get('POSTGRES_PORT')}/{values.get('POSTGRES_DB')}"
            )

        # --- Build Test DATABASE_URL ---
        if values.get("USE_POSTGRES_FOR_TESTS", False):
            # Construct Postgres test URL for the template DB
            values["TEST_DATABASE_URL"] = (
                f"postgresql://{values.get('TEST_POSTGRES_USER')}:{values.get('TEST_POSTGRES_PASSWORD')}@{values.get('TEST_POSTGRES_SERVER')}:{values.get('TEST_POSTGRES_PORT')}/{values.get('TEST_POSTGRES_DB_MAIN')}"
            )
        else:
            # Default to SQLite in-memory for tests
            values["TEST_DATABASE_URL"] = "sqlite:///:memory:"

        return values

    # --- API and Security Settings ---
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "a_very_secret_key_that_should_be_changed_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    class Config:
        # Load environment variables from .env file first
        env_file = ".env"
        # If a .env.test file exists, it will override the .env file
        # This is useful for setting test-specific variables like USE_POSTGRES_FOR_TESTS
        # Pydantic-settings handles this chain loading automatically if both files are present
        extra = "allow"  # allows other env files to be loaded


settings = Settings(_env_file=".env.test", _env_file_encoding="utf-8")
