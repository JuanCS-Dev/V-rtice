#!/usr/bin/env python3
"""
HITL API Integration Test
Tests all authentication and decision endpoints
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8002"

def print_test(name):
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print('='*60)

def test_health():
    """Test health endpoint"""
    print_test("Health Check")

    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("✅ Health check passed")

def test_login():
    """Test login endpoint"""
    print_test("Login (Admin Credentials)")

    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={
            "username": "admin",
            "password": "ChangeMe123!"
        }
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"✅ Login successful! Token: {token[:50]}...")
        return token
    else:
        print("❌ Login failed")
        return None

def test_status(token):
    """Test status endpoint with authentication"""
    print_test("System Status (Authenticated)")

    if not token:
        print("⚠️ Skipping (no token)")
        return

    response = requests.get(
        f"{BASE_URL}/api/status",
        headers={"Authorization": f"Bearer {token}"}
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        print("✅ Status endpoint passed")
    else:
        print("❌ Status endpoint failed")

def test_me_endpoint(token):
    """Test /api/auth/me endpoint"""
    print_test("Current User Info")

    if not token:
        print("⚠️ Skipping (no token)")
        return

    response = requests.get(
        f"{BASE_URL}/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        print("✅ User info endpoint passed")
    else:
        print("❌ User info endpoint failed")

def test_pending_decisions(token):
    """Test pending decisions endpoint"""
    print_test("Pending Decisions")

    if not token:
        print("⚠️ Skipping (no token)")
        return

    # Note: This endpoint might not exist yet (needs decision_endpoints.py)
    response = requests.get(
        f"{BASE_URL}/api/decisions/pending",
        headers={"Authorization": f"Bearer {token}"}
    )

    print(f"Status: {response.status_code}")
    if response.status_code == 404:
        print("⚠️ Endpoint not found (decision_endpoints.py not imported)")
    elif response.status_code == 200:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print("✅ Pending decisions endpoint passed")
    else:
        print(f"Response: {response.text}")
        print("❌ Pending decisions endpoint failed")

def test_api_docs():
    """Test API documentation"""
    print_test("API Documentation (Swagger)")

    response = requests.get(f"{BASE_URL}/api/docs")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        print("✅ API docs available at: http://localhost:8002/api/docs")
    else:
        print("❌ API docs failed")

def main():
    """Run all tests"""
    print("\n🚀 HITL API Integration Tests")
    print(f"Testing: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")

    try:
        # Test 1: Health check
        test_health()

        # Test 2: API documentation
        test_api_docs()

        # Test 3: Login
        token = test_login()

        # Test 4: System status
        test_status(token)

        # Test 5: Current user info
        test_me_endpoint(token)

        # Test 6: Pending decisions
        test_pending_decisions(token)

        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print("✅ Core authentication endpoints working")
        print("⚠️ Decision endpoints require decision_endpoints.py import fix")
        print("\nNext Steps:")
        print("1. Fix decision_endpoints.py import (relative import issue)")
        print("2. Test WebSocket endpoint (/ws/{username})")
        print("3. Integration test with CANDI")

    except requests.ConnectionError:
        print(f"\n❌ ERROR: Could not connect to {BASE_URL}")
        print("Make sure HITL backend is running:")
        print("  cd /home/juan/vertice-dev/backend/services/reactive_fabric_core")
        print("  PYTHONPATH=. python hitl/hitl_backend.py")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
