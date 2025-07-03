from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings # Import settings

# Use the DATABASE_URL from settings
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Adjust engine creation based on whether it's SQLite or PostgreSQL
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False} # Needed only for SQLite
    )
else:
    # For PostgreSQL or other databases, connect_args might not be needed or different
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
