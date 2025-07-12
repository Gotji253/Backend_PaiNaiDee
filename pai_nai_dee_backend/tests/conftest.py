import pytest
from typing import Generator, Any
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os

os.environ["TESTING"] = "1"

from ..app.main import app as main_app
from ..app.core.config import settings
from ..app.db.database import get_db, Base


@pytest.fixture(scope="session")
def db_engine():
    # Ensure a test database URL is set
    if not settings.TEST_DATABASE_URL:
        settings.TEST_DATABASE_URL = "sqlite:///./test.db"
    engine = create_engine(settings.TEST_DATABASE_URL, echo=True)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = SessionLocal()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, Any, None]:
    def override_get_db():
        yield db_session

    main_app.dependency_overrides[get_db] = override_get_db
    with TestClient(main_app) as c:
        yield c
    main_app.dependency_overrides.clear()
