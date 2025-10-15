"""
pytest fixtures for HITL backend testing
Now using proper TestClient with isolated in-memory database
"""

import pytest
from datetime import datetime
from starlette.testclient import TestClient


@pytest.fixture
def client():
    """Test client using proper FastAPI TestClient with in-memory app"""
    # Import here to avoid circular imports
    import sys
    sys.path.insert(0, str("/home/juan/vertice-dev/backend/services/reactive_fabric_core"))
    from hitl.hitl_backend import app

    # Create proper test client (no external server needed)
    return TestClient(app)


@pytest.fixture
def reset_db():
    """Reset in-memory database before each test"""
    from hitl.hitl_backend import db, UserInDB, UserRole, pwd_context

    # Clear all data
    db.users.clear()
    db.decisions.clear()
    db.responses.clear()
    db.sessions.clear()
    db.audit_log.clear()

    # Recreate default admin user
    admin = UserInDB(
        username="admin",
        email="admin@reactive-fabric.local",
        full_name="System Administrator",
        role=UserRole.ADMIN,
        hashed_password=pwd_context.hash("ChangeMe123!"),
        is_active=True,
        is_2fa_enabled=False,
        created_at=datetime.now()
    )
    db.users["admin"] = admin

    yield db

    # Cleanup after test
    db.users.clear()
    db.decisions.clear()
    db.responses.clear()
    db.sessions.clear()
    db.audit_log.clear()


@pytest.fixture
def admin_token(client, reset_db):
    """Get valid admin JWT token"""
    response = client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "ChangeMe123!"}
    )
    assert response.status_code == 200, f"Admin login failed: {response.status_code} - {response.text}"
    return response.json()["access_token"]


@pytest.fixture
def analyst_token(client, reset_db, admin_token):
    """Create analyst user and get token"""
    from hitl.hitl_backend import UserRole

    # Register analyst user
    response = client.post(
        "/api/auth/register",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "analyst1",
            "email": "analyst@test.com",
            "password": "TestPass123",
            "full_name": "Test Analyst",
            "role": "analyst"
        }
    )
    assert response.status_code == 200, f"Registration failed: {response.status_code} - {response.text}"

    # Login as analyst
    response = client.post(
        "/api/auth/login",
        data={"username": "analyst1", "password": "TestPass123"}
    )
    assert response.status_code == 200, f"Login failed: {response.status_code} - {response.text}"
    return response.json()["access_token"]


@pytest.fixture
def viewer_token(client, reset_db, admin_token):
    """Create viewer user and get token"""
    # Register viewer user
    response = client.post(
        "/api/auth/register",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "viewer1",
            "email": "viewer@test.com",
            "password": "TestPass123",
            "full_name": "Test Viewer",
            "role": "viewer"
        }
    )
    assert response.status_code == 200, f"Registration failed: {response.status_code} - {response.text}"

    # Login as viewer
    response = client.post(
        "/api/auth/login",
        data={"username": "viewer1", "password": "TestPass123"}
    )
    assert response.status_code == 200, f"Login failed: {response.status_code} - {response.text}"
    return response.json()["access_token"]


@pytest.fixture
def sample_decision_payload():
    """Sample decision request payload"""
    return {
        "analysis_id": "TEST-001",
        "incident_id": "INC-001",
        "threat_level": "APT",
        "source_ip": "192.168.1.100",
        "attributed_actor": "APT28",
        "confidence": 87.5,
        "iocs": ["ip:192.168.1.100", "hash:abc123"],
        "ttps": ["T1110", "T1059"],
        "recommended_actions": ["Block IP", "Quarantine system"],
        "forensic_summary": "APT28 activity detected",
        "priority": "critical",
        "created_at": datetime.now().isoformat()
    }


@pytest.fixture
def submitted_decision(client, admin_token, sample_decision_payload):
    """Submit a decision and return analysis_id"""
    response = client.post(
        "/api/decisions/submit",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=sample_decision_payload
    )
    assert response.status_code == 200, f"Decision submission failed: {response.status_code} - {response.text}"
    return sample_decision_payload["analysis_id"]
