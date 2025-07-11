from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# For testing, we might use a different engine/session
engine_test = None
SessionLocalTest = None

if settings.SQLALCHEMY_DATABASE_URI_TEST:
    engine_test = create_engine(
        settings.SQLALCHEMY_DATABASE_URI_TEST, pool_pre_ping=True
    )
    SessionLocalTest = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def get_db():
    """
    Dependency to get a database session.
    Ensures the session is closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
