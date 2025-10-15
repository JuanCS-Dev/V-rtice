#!/usr/bin/env python3
"""Debug script to test submit endpoint"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8002"

# Step 1: Login
print("1. Logging in...")
login_response = requests.post(
    f"{BASE_URL}/api/auth/login",
    data={"username": "admin", "password": "ChangeMe123!"}
)
print(f"Login status: {login_response.status_code}")
print(f"Login response: {login_response.text}")

if login_response.status_code != 200:
    print("❌ Login failed!")
    exit(1)

tokens = login_response.json()
access_token = tokens["access_token"]
print(f"✅ Token: {access_token[:50]}...")

# Step 2: Test submit endpoint
print("\n2. Testing submit endpoint...")
headers = {"Authorization": f"Bearer {access_token}"}

decision_request = {
    "analysis_id": "TEST-DEBUG-001",
    "incident_id": "INC-DEBUG-001",
    "threat_level": "APT",
    "source_ip": "1.2.3.4",
    "attributed_actor": "APT28",
    "confidence": 85.0,
    "iocs": ["ip:1.2.3.4"],
    "ttps": ["T1110"],
    "recommended_actions": ["Block IP"],
    "forensic_summary": "Test",
    "priority": "critical",
    "created_at": datetime.now().isoformat()
}

print(f"Headers: {headers}")
print(f"Payload: {json.dumps(decision_request, indent=2)}")

submit_response = requests.post(
    f"{BASE_URL}/api/decisions/submit",
    headers=headers,
    json=decision_request
)

print(f"\nSubmit status: {submit_response.status_code}")
print(f"Submit response: {submit_response.text}")

if submit_response.status_code == 200:
    print("✅ Submit successful!")
else:
    print("❌ Submit failed!")
