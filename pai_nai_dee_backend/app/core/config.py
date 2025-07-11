from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "Pai Nai Dee API"
    PROJECT_VERSION: str = "0.1.0"

    # Database settings
    POSTGRES_USER: str = "your_db_user"
    POSTGRES_PASSWORD: str = "your_db_password"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "pai_nai_dee_db"

    # SQLALCHEMY_DATABASE_URL: Optional[str] = None # For async, build directly
    # For sync, can be built like this:
    # SQLALCHEMY_DATABASE_URL: str = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
    # However, it's better to construct it dynamically or allow full URL override.

    # Default DATABASE_URL constructed from parts, can be overridden by direct DATABASE_URL env var
    _DEFAULT_DATABASE_URL: str = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    DATABASE_URL: Optional[str] = None  # Allow override via .env

    # Test Database URL (defaults to SQLite in-memory for tests if not set)
    # TEST_DATABASE_URL: str = "sqlite:///./test.db"  # Or "sqlite:///:memory:" # Commented out for new PostgreSQL test config

    # PostgreSQL Test Database settings
    TEST_POSTGRES_USER: str = "test_user"
    TEST_POSTGRES_PASSWORD: str = "test_password"
    TEST_POSTGRES_SERVER: str = "localhost"
    TEST_POSTGRES_PORT: str = "5433"  # Different port for test DB server if needed
    TEST_POSTGRES_DB_MAIN: str = (
        "pai_nai_dee_test_template"  # Main DB that acts as a template
    )

    # This will be dynamically constructed in conftest.py for each test session/run
    # but we need a placeholder or a default if someone tries to access it directly from settings
    TEST_DATABASE_URL: Optional[str] = None

    # Dynamically construct DATABASE_URL if not explicitly set
    from pydantic import model_validator

    @model_validator(mode="before")
    @classmethod
    def build_database_url(cls, values: dict) -> dict:
        if "DATABASE_URL" not in values or values.get("DATABASE_URL") is None:
            # If DATABASE_URL is not provided directly, construct it from components
            db_user = values.get("POSTGRES_USER", "your_db_user")
            db_password = values.get("POSTGRES_PASSWORD", "your_db_password")
            db_server = values.get("POSTGRES_SERVER", "localhost")
            db_port = values.get("POSTGRES_PORT", "5432")
            db_name = values.get("POSTGRES_DB", "pai_nai_dee_db")
            values["DATABASE_URL"] = (
                f"postgresql://{db_user}:{db_password}@{db_server}:{db_port}/{db_name}"
            )
        return values

    # API general settings
    API_V1_STR: str = "/api/v1"

    # Security settings
    SECRET_KEY: str = (
        "a_very_secret_key_that_should_be_changed_in_production"  # CHANGE THIS!
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutes
    ALGORITHM: str = "HS256"

    # CORS settings (example)
    # BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"] # Example for frontend

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # case_sensitive = True # Default is False, environment variables are case-insensitive


settings = Settings()
