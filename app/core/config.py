import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file at the project root
dotenv_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"
)
load_dotenv(dotenv_path)


class Settings(BaseSettings):
    PROJECT_NAME: str = "Travel Planner API"
    API_V1_STR: str = "/api/v1"

    # Database settings
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "travel_planner_db")
    SQLALCHEMY_DATABASE_URI: str | None = None

    # For testing, use a different database
    POSTGRES_DB_TEST: str = os.getenv("POSTGRES_DB_TEST", "travel_planner_test_db")
    SQLALCHEMY_DATABASE_URI_TEST: str | None = None

    # JWT settings
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "a_very_secret_key_that_should_be_changed"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutes
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7 days

    # CORS settings
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]  # Example origins

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

    def __init__(self, **values):
        super().__init__(**values)
        self.SQLALCHEMY_DATABASE_URI = (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
        )
        self.SQLALCHEMY_DATABASE_URI_TEST = (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}/{self.POSTGRES_DB_TEST}"
        )


settings = Settings()
