from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from ..core.config import settings
import os

# Determine if we are in a testing environment
IS_TESTING = "TESTING" in os.environ

# --- Database URL Configuration ---
if IS_TESTING:
    SQLALCHEMY_DATABASE_URL = settings.TEST_DATABASE_URL
else:
    SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# --- Synchronous Engine ---
# Add connect_args for SQLite to handle multithreading issues in tests
connect_args = (
    {"check_same_thread": False}
    if SQLALCHEMY_DATABASE_URL and SQLALCHEMY_DATABASE_URL.startswith("sqlite")
    else {}
)
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)


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
