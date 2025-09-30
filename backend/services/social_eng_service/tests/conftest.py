import pytest
import asyncio
from typing import Generator, AsyncGenerator
from unittest.mock import patch

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from social_eng_service.main import app
from social_eng_service.database import Base, get_db
from social_eng_service.config import settings

# Use an in-memory SQLite database for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///file::memory:?cache=shared"

@pytest.fixture(scope="session")
def event_loop(request) -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Fixture for a test database session."""
    # Create a test engine
    engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create a sessionmaker for the test database
    TestAsyncSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
    )

    async with TestAsyncSessionLocal() as session:
        yield session

    # Drop tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Fixture for an asynchronous test client."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Mock SMTP sending
    with patch('social_eng_service.main.smtplib.SMTP') as mock_smtp:
        mock_smtp_instance = mock_smtp.return_value
        mock_smtp_instance.sendmail.return_value = {}
        mock_smtp_instance.starttls.return_value = None
        mock_smtp_instance.login.return_value = None

        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def mock_settings():
    """Fixture to mock settings for tests."""
    with patch('social_eng_service.config.settings') as mock_settings_obj:
        mock_settings_obj.APP_BASE_URL = "http://test-app"
        mock_settings_obj.DATABASE_URL = TEST_DATABASE_URL
        mock_settings_obj.SMTP_HOST = "smtp.test.com"
        mock_settings_obj.SMTP_PORT = 587
        mock_settings_obj.SMTP_USERNAME = "testuser"
        mock_settings_obj.SMTP_PASSWORD = "testpass"
        mock_settings_obj.SMTP_SENDER_EMAIL = "test@test.com"
        yield mock_settings_obj