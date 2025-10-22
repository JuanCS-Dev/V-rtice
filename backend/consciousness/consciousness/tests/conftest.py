"""
Pytest Configuration and Fixtures for Consciousness Tests

Provides test fixtures for:
- PostgreSQL database (for persistence tests)
- Test client (FastAPI)
- Mock services
"""

import os
import pytest
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


# PostgreSQL connection parameters from environment or defaults
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "postgres")
TEST_DB_NAME = "vertice_test"


@pytest.fixture(scope="session")
def postgres_available():
    """Check if PostgreSQL is available for testing."""
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database=POSTGRES_DB,
            connect_timeout=3
        )
        conn.close()
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def test_database(postgres_available):
    """
    Create test database for the entire test session.

    Yields the database name, then drops it after all tests.
    """
    if not postgres_available:
        pytest.skip("PostgreSQL not available")

    # Connect to default database
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database=POSTGRES_DB
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    # Drop test database if exists (from previous run)
    cursor.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}")

    # Create test database
    cursor.execute(f"CREATE DATABASE {TEST_DB_NAME}")

    cursor.close()
    conn.close()

    # Yield database name for tests
    yield TEST_DB_NAME

    # Teardown: drop test database
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database=POSTGRES_DB
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    # Force disconnect all users
    cursor.execute(f"""
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = '{TEST_DB_NAME}'
        AND pid <> pg_backend_pid()
    """)

    cursor.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}")
    cursor.close()
    conn.close()


@pytest.fixture(scope="function")
def clean_test_db(test_database):
    """
    Clean test database before each test.

    Drops and recreates all tables to ensure test isolation.
    """
    from consciousness.persistence.decision_repository import DecisionRepository

    # Initialize repository (creates tables)
    repo = DecisionRepository(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=test_database,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        min_connections=1,
        max_connections=2
    )

    try:
        repo.initialize()

        # Clean all data (keep schema)
        if repo.pool:
            conn = repo.pool.getconn()
            try:
                cursor = conn.cursor()

                # Truncate all tables
                cursor.execute("""
                    TRUNCATE TABLE decisions CASCADE;
                """)

                conn.commit()
                cursor.close()
            finally:
                repo.pool.putconn(conn)

        yield repo

    finally:
        repo.close()


@pytest.fixture
def db_connection_params(test_database):
    """Provide database connection parameters for tests."""
    return {
        "host": POSTGRES_HOST,
        "port": POSTGRES_PORT,
        "database": test_database,
        "user": POSTGRES_USER,
        "password": POSTGRES_PASSWORD
    }
