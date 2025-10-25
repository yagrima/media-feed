"""
Pytest configuration and shared fixtures for all tests.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.db.models import Base
from app.db.database import get_db
from app.main import app


# Use in-memory SQLite database for tests
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_engine():
    """Create test database engine."""
    engine = create_engine(
        SQLALCHEMY_TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db(db_engine):
    """Create test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine
    )
    session = TestingSessionLocal()

    # Override the get_db dependency
    def override_get_db():
        try:
            yield session
        finally:
            pass  # Don't close session here, we'll do it after the test

    app.dependency_overrides[get_db] = override_get_db

    try:
        yield session
    finally:
        session.close()
        app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(db):
    """Create test client with database dependency override."""
    from fastapi.testclient import TestClient
    return TestClient(app)
