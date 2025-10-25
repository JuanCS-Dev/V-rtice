#!/usr/bin/env python
"""
Enqueue Test Decision - E2E Validation Script

Creates and enqueues a realistic HITL decision for manual E2E testing.
This decision will appear in the Governance Workspace SSE stream.

Usage:
    python enqueue_test_decision.py

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
Quality: Production-ready, REGRA DE OURO compliant
"""

import requests
from datetime import datetime, timezone


def create_test_decision_payload(risk_level: str = "high") -> dict:
    """
    Create a realistic test decision payload for E2E validation.

    Args:
        risk_level: Risk level (critical/high/medium/low)

    Returns:
        Decision dictionary ready to send to API
    """
    decision_id = f"test_dec_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    payload = {
        "decision_id": decision_id,
        "risk_level": risk_level,
        "automation_level": "supervised",
        "context": {
            "action_type": "block_ip",
            "action_params": {
                "target": "192.168.100.50",
                "action": "block",
                "duration": "24h",
                "reason": "Malicious activity detected",
            },
            "ai_reasoning": (
                "Detected sustained port scanning activity from 192.168.100.50 "
                "targeting critical infrastructure. Pattern matches known APT28 "
                "reconnaissance techniques. Confidence: 95%. Recommendation: "
                "Immediate block with 24h duration pending investigation."
            ),
            "confidence": 0.95,
            "threat_score": 0.95,
            "threat_type": "reconnaissance",
            "metadata": {
                "source": "network_monitor",
                "detection_time": datetime.now(timezone.utc).isoformat(),
                "iocs": ["192.168.100.50", "port_scan_signature_123"],
                "mitre_tactics": ["TA0043"],
                "severity": "high",
            },
        },
    }

    return payload


def main():
    """Main entry point."""
    print("=" * 80)
    print("🎯 Enqueue Test Decision - E2E Validation")
    print("=" * 80)
    print()

    backend_url = "http://localhost:8001"

    # Check backend health
    print(f"📡 Checking backend health at {backend_url}...")
    try:
        response = requests.get(f"{backend_url}/api/v1/governance/health", timeout=5)
        response.raise_for_status()
        health_data = response.json()
        print(f"   ✅ Backend healthy")
        print(f"      Active connections: {health_data['active_connections']}")
        print(f"      Queue size: {health_data['queue_size']}")
        print()
    except Exception as e:
        print(f"   ❌ Backend not accessible: {e}")
        print(f"   💡 Start server with: python governance_sse/standalone_server.py")
        return 1

    # Create test decision payload
    print("🔧 Creating test decision (RISK=HIGH)...")
    payload = create_test_decision_payload(risk_level="high")
    print(f"   Decision ID: {payload['decision_id']}")
    print(f"   Risk Level: {payload['risk_level']}")
    print(f"   Action: {payload['context']['action_type']}")
    print(f"   Target: {payload['context']['action_params']['target']}")
    print()

    # Enqueue decision via API
    print("📤 Enqueuing decision via API...")
    try:
        response = requests.post(
            f"{backend_url}/api/v1/governance/test/enqueue",
            json=payload,
            timeout=5,
        )
        response.raise_for_status()
        result = response.json()

        print(f"   ✅ {result['message']}")
        print(f"      Decision ID: {result['decision_id']}")
        print(f"      Risk Level: {result['risk_level']}")
        print()

        print("=" * 80)
        print("✅ SUCCESS - Decision enqueued")
        print("=" * 80)
        print()

    except requests.exceptions.HTTPError as e:
        print(f"   ❌ HTTP Error: {e}")
        print(f"      Response: {e.response.text}")
        return 1
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return 1

    # Verify via pending stats API
    print("🔍 Verifying via pending stats API...")
    try:
        response = requests.get(f"{backend_url}/api/v1/governance/pending", timeout=5)
        response.raise_for_status()
        stats = response.json()
        print(f"   Total Pending: {stats['total_pending']}")
        print(f"   By Risk Level:")
        for level, count in stats['by_risk_level'].items():
            if count > 0:
                print(f"      - {level}: {count}")
        print()

        if stats['total_pending'] > 0:
            print("   ✅ Decision confirmed in queue")
        else:
            print("   ⚠️  Decision not visible in queue (may take a moment)")
        print()
    except Exception as e:
        print(f"   ⚠️  Could not verify: {e}")
        print()

    # Next steps
    print("📋 Next Steps:")
    print("   1. Launch workspace:")
    print(f"      vertice governance start --backend-url {backend_url}")
    print()
    print("   2. You should see the decision appear in the Pending panel")
    print("   3. Click on it to review in the Active panel")
    print("   4. Test Approve/Reject/Escalate actions")
    print()

    return 0


if __name__ == "__main__":
    exit(main())
