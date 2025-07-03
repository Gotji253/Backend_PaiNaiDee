from pydantic_settings import BaseSettings
from typing import List, Union

class Settings(BaseSettings):
    PROJECT_NAME: str = "Pai Nai Dee API"
    PROJECT_VERSION: str = "0.1.0"

    # JWT settings
    SECRET_KEY: str = "your-secret-key"  # TODO: Load from environment variable
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS settings
    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000"]'
    BACKEND_CORS_ORIGINS: List[str] = ["*"] # Allow all origins for now, should be restricted in production

    # Database
    #DATABASE_URL: str = "sqlite:///./pai_nai_dee.db" # Already in database.py, consider centralizing
    # POSTGRES_SERVER: str = "localhost"
    # POSTGRES_USER: str = "your_db_user"
    # POSTGRES_PASSWORD: str = "your_db_password"
    # POSTGRES_DB: str = "pai_nai_dee_db"
    # SQLALCHEMY_DATABASE_URI: Optional[str] = None

    # @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    # def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
    #     if isinstance(v, str):
    #         return v
    #     return PostgresDsn.build(
    #         scheme="postgresql",
    #         user=values.get("POSTGRES_USER"),
    #         password=values.get("POSTGRES_PASSWORD"),
    #         host=values.get("POSTGRES_SERVER"),
    #         path=f"/{values.get('POSTGRES_DB') or ''}",
    #     )

    class Config:
        case_sensitive = True
        # env_file = ".env" # If you want to load from a .env file

settings = Settings()
