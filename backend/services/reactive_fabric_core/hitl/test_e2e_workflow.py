#!/usr/bin/env python3
"""
HITL End-to-End Workflow Test
Tests complete flow: CANDI → HITL → Decision → Action
"""

import requests
import time
from datetime import datetime
from uuid import uuid4

BASE_URL = "http://localhost:8002"

def print_step(step, desc):
    print(f"\n{'='*60}")
    print(f"STEP {step}: {desc}")
    print('='*60)

def test_e2e_workflow():
    """Test complete HITL workflow"""

    print("\n🎯 HITL END-TO-END WORKFLOW TEST")
    print(f"Testing: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")

    # ============================================================================
    # STEP 1: Health Check
    # ============================================================================
    print_step(1, "Health Check")

    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200, "Health check failed"
    print(f"✅ Backend is healthy: {response.json()}")

    # ============================================================================
    # STEP 2: Admin Login
    # ============================================================================
    print_step(2, "Admin Login (JWT Authentication)")

    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={"username": "admin", "password": "ChangeMe123!"}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"

    tokens = response.json()
    access_token = tokens["access_token"]
    print(f"✅ Login successful")
    print(f"   Token: {access_token[:50]}...")
    print(f"   Requires 2FA: {tokens['requires_2fa']}")

    headers = {"Authorization": f"Bearer {access_token}"}

    # ============================================================================
    # STEP 3: Check System Status
    # ============================================================================
    print_step(3, "System Status Check")

    response = requests.get(f"{BASE_URL}/api/status", headers=headers)
    assert response.status_code == 200

    status = response.json()
    print(f"✅ System Status:")
    print(f"   Pending Decisions: {status['pending_decisions']}")
    print(f"   Critical Pending: {status['critical_pending']}")
    print(f"   Total Users: {status['total_users']}")

    # ============================================================================
    # STEP 4: Simulate CANDI Analysis Result
    # ============================================================================
    print_step(4, "Simulate CANDI Analysis (APT Detection)")

    analysis_id = f"CANDI-{uuid4().hex[:8]}"
    incident_id = f"INC-{datetime.now().strftime('%Y%m%d')}-0001"

    decision_request = {
        "analysis_id": analysis_id,
        "incident_id": incident_id,
        "threat_level": "APT",
        "source_ip": "185.86.148.10",
        "attributed_actor": "APT28 (Fancy Bear)",
        "confidence": 87.5,
        "iocs": [
            "ip:185.86.148.10",
            "domain:apt28-c2.ru",
            "hash:a3f8b2c1d4e5f6a7b8c9d0e1f2a3b4c5"
        ],
        "ttps": [
            "T1110.003",  # Password Spraying
            "T1059.001",  # PowerShell
            "T1053.005"   # Scheduled Task
        ],
        "recommended_actions": [
            "CRITICAL: APT28 activity detected - nation-state threat actor",
            "Isolate affected system immediately",
            "Block source IP at firewall",
            "Escalate to security leadership",
            "Initiate incident response protocol"
        ],
        "forensic_summary": (
            "Threat Level: APT | Attribution: APT28 (Fancy Bear) | "
            "Confidence: 87.5% | "
            "TTPs: Password spraying followed by PowerShell execution and "
            "scheduled task creation for persistence. "
            "Source IP 185.86.148.10 associated with known APT28 infrastructure."
        ),
        "priority": "critical",
        "created_at": datetime.now().isoformat()
    }

    print(f"📊 CANDI Analysis Summary:")
    print(f"   Analysis ID: {analysis_id}")
    print(f"   Threat Level: {decision_request['threat_level']}")
    print(f"   Actor: {decision_request['attributed_actor']}")
    print(f"   Confidence: {decision_request['confidence']}%")
    print(f"   Priority: {decision_request['priority'].upper()}")

    # ============================================================================
    # STEP 5: Submit Decision Request to HITL
    # ============================================================================
    print_step(5, "Submit Decision to HITL Queue")

    response = requests.post(
        f"{BASE_URL}/api/decisions/submit",
        headers=headers,
        json=decision_request
    )
    assert response.status_code == 200, f"Submit failed: {response.text}"

    submit_result = response.json()
    print(f"✅ Decision submitted to HITL queue")
    print(f"   Analysis ID: {submit_result['analysis_id']}")

    # ============================================================================
    # STEP 6: Retrieve Pending Decisions
    # ============================================================================
    print_step(6, "Retrieve Pending Decisions (Analyst View)")

    response = requests.get(
        f"{BASE_URL}/api/decisions/pending?priority=critical",
        headers=headers
    )
    assert response.status_code == 200

    pending = response.json()
    print(f"✅ Retrieved {len(pending)} critical pending decision(s)")

    if pending:
        decision = pending[0]
        print(f"\n📋 Decision Details:")
        print(f"   Analysis ID: {decision['analysis_id']}")
        print(f"   Threat: {decision['threat_level']}")
        print(f"   Actor: {decision['attributed_actor']}")
        print(f"   IOCs: {len(decision['iocs'])} indicators")
        print(f"   TTPs: {', '.join(decision['ttps'])}")

    # ============================================================================
    # STEP 7: Get Specific Decision
    # ============================================================================
    print_step(7, "Get Decision Details")

    response = requests.get(
        f"{BASE_URL}/api/decisions/{analysis_id}",
        headers=headers
    )
    assert response.status_code == 200

    decision_detail = response.json()
    print(f"✅ Retrieved decision details for {analysis_id}")
    print(f"\n   Recommended Actions:")
    for i, action in enumerate(decision_detail['recommended_actions'], 1):
        print(f"   {i}. {action}")

    # ============================================================================
    # STEP 8: Human Decision (Approve Actions)
    # ============================================================================
    print_step(8, "Human Analyst Makes Decision (APPROVE)")

    decision_data = {
        "decision_id": analysis_id,
        "status": "approved",
        "approved_actions": [
            "block_ip",
            "quarantine_system",
            "escalate_to_soc"
        ],
        "notes": (
            "APT28 confirmed based on TTPs and infrastructure correlation. "
            "Immediate containment authorized. "
            "SOC escalation initiated for full incident response."
        )
    }

    response = requests.post(
        f"{BASE_URL}/api/decisions/{analysis_id}/decide",
        headers=headers,
        json=decision_data
    )
    assert response.status_code == 200

    decision_response = response.json()
    print(f"✅ Decision made: {decision_response['status'].upper()}")
    print(f"   Decided by: {decision_response['decided_by']}")
    print(f"   Decided at: {decision_response['decided_at']}")
    print(f"   Approved Actions: {', '.join([a.replace('_', ' ').title() for a in decision_response['approved_actions']])}")

    # ============================================================================
    # STEP 9: Retrieve Decision Response
    # ============================================================================
    print_step(9, "Retrieve Decision Response")

    response = requests.get(
        f"{BASE_URL}/api/decisions/{analysis_id}/response",
        headers=headers
    )
    assert response.status_code == 200

    final_response = response.json()
    print(f"✅ Decision Response Retrieved")
    print(f"   Status: {final_response['status'].upper()}")
    print(f"   Notes: {final_response['notes']}")

    # ============================================================================
    # STEP 10: Get Statistics
    # ============================================================================
    print_step(10, "Get Decision Statistics")

    response = requests.get(
        f"{BASE_URL}/api/decisions/stats/summary",
        headers=headers
    )
    assert response.status_code == 200

    stats = response.json()
    print(f"✅ Decision Statistics:")
    print(f"   Total Pending: {stats['total_pending']}")
    print(f"   Critical Pending: {stats['critical_pending']}")
    print(f"   Total Completed: {stats['total_completed']}")
    print(f"   Avg Response Time: {stats['avg_response_time_minutes']:.2f} minutes")
    print(f"   Decisions (24h): {stats['decisions_last_24h']}")

    # ============================================================================
    # SUCCESS
    # ============================================================================
    print("\n" + "="*60)
    print("✅ E2E WORKFLOW TEST: COMPLETE SUCCESS!")
    print("="*60)
    print("\nWorkflow Validated:")
    print("1. ✅ Backend Health Check")
    print("2. ✅ JWT Authentication")
    print("3. ✅ System Status")
    print("4. ✅ CANDI Analysis Simulation")
    print("5. ✅ Submit Decision to HITL")
    print("6. ✅ Retrieve Pending Decisions")
    print("7. ✅ Get Decision Details")
    print("8. ✅ Human Decision (Approve)")
    print("9. ✅ Retrieve Decision Response")
    print("10. ✅ Get Statistics")

    print("\n🎯 HITL System: 100% OPERATIONAL!")
    print(f"\nComplete flow tested in {time.time() - start_time:.2f}s")
    print("\nNext Steps:")
    print("- Frontend integration (React UI)")
    print("- WebSocket real-time alerts")
    print("- CANDI → HITL integration")
    print("- Production deployment")

if __name__ == "__main__":
    start_time = time.time()
    try:
        test_e2e_workflow()
    except requests.ConnectionError:
        print(f"\n❌ ERROR: Could not connect to {BASE_URL}")
        print("Make sure HITL backend is running:")
        print("  cd /home/juan/vertice-dev/backend/services/reactive_fabric_core")
        print("  ./hitl/start_hitl.sh")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
