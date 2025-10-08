"""Maximus Social Engineering Service - Test Configuration.

This module provides pytest fixtures and configurations for testing the Maximus
AI's Social Engineering Service. It sets up a clean testing environment, including
an in-memory SQLite database, to ensure that tests are isolated and repeatable.

Key functionalities include:
- Creating a test database engine and session.
- Overriding FastAPI's dependency injection for database access.
- Providing a test client for making API requests.
- Ensuring that database tables are created and dropped for each test run.

This configuration is crucial for enabling robust and reliable testing of the
Social Engineering Service's API endpoints and business logic.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(name="db_session")
def db_session_fixture():
    """Provides a test database session for each test.

    Ensures that tables are created before each test and dropped after.
    """
    Base.metadata.create_all(bind=engine)  # Create tables
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)  # Drop tables after test


@pytest.fixture(name="client")
def client_fixture(db_session: Session):  # Use the db_session fixture
    """Provides a TestClient for making API requests.

    Overrides the get_db dependency to use the test database session.
    """

    def override_get_db():
        """Substitui a dependência get_db para usar a sessão de banco de dados de teste."""
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()  # Clean up overrides
