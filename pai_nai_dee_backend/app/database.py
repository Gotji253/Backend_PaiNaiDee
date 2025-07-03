from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# DATABASE_URL = "postgresql://user:password@host:port/database"
# Example for local development with environment variables:
DB_USER = os.getenv("DB_USER", "your_db_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "your_db_password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "pai_nai_dee_db")

#SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
# Using a default SQLite database for now for easier setup, will change to PostgreSQL later.
SQLALCHEMY_DATABASE_URL = "sqlite:///./pai_nai_dee.db"


engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    # connect_args={"check_same_thread": False} # Needed only for SQLite
)

# For SQLite, add connect_args
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to create database tables (optional, can be managed by Alembic)
# def create_db_and_tables():
#     Base.metadata.create_all(bind=engine)

# if __name__ == "__main__":
#     # This can be called to initialize the database tables
#     # For a real application, you would likely use Alembic migrations
#     print(f"Initializing database at {SQLALCHEMY_DATABASE_URL}")
#     create_db_and_tables()
#     print("Database tables created (if they didn't exist).")
