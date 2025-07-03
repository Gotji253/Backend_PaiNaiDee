from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Determine database URL (SQLite for simplicity, configurable for PostgreSQL)
# For production, use environment variables for database credentials.
# Example for PostgreSQL:
# SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@host:port/db")
# For local development with SQLite:
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pai_nai_dee.db")

connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Import all models here so Base knows about them before create_all is called
# This is crucial for Base.metadata.create_all(bind=engine) to work correctly.
# Ensure __init__.py in models directory allows easy import or import them individually.
from .models import user, place, review, favorite # Assuming __init__.py in models makes these available
                                                 # or direct imports like from .models.user import User

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to create database tables
def create_db_and_tables():
    """Creates all tables in the database."""
    # This will create tables for all classes that inherit from Base
    print(f"Initializing database at {SQLALCHEMY_DATABASE_URL}")
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully (if they didn't already exist).")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        # Depending on the error, you might want to raise it or handle it differently

# Example of running this directly (e.g., for initial setup script)
if __name__ == "__main__":
    # This is useful for standalone script execution to initialize the DB.
    # For a FastAPI app, you might call create_db_and_tables() on startup (e.g., in main.py),
    # or preferably use Alembic for migrations in a production environment.
    create_db_and_tables()
