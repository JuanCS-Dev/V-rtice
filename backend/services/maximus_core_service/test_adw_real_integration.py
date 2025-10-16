"""ADW Real Integration Test Script.

Tests all 9 ADW endpoints with real service integration.
Purple Team endpoints use REAL data.
Offensive/Defensive endpoints ready for real integration (currently mock).

Run with: python test_adw_real_integration.py
"""

import sys
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Import router
from adw_router import router

# Create app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_endpoint(name: str, method: str, path: str, **kwargs):
    """Test single endpoint."""
    try:
        if method == "GET":
            resp = client.get(path)
        elif method == "POST":
            resp = client.post(path, **kwargs)
        else:
            raise ValueError(f"Unknown method: {method}")

        status = "✅" if resp.status_code == 200 else f"❌ {resp.status_code}"
        print(f"{name}: {status}")

        if resp.status_code == 200:
            return True, resp.json()
        else:
            print(f"  Error: {resp.text}")
            return False, None
    except Exception as e:
        print(f"{name}: ❌ Exception: {e}")
        return False, None


def main():
    """Run all ADW endpoint tests."""
    print("=" * 70)
    print("ADW REAL INTEGRATION TEST")
    print("=" * 70)
    print()

    success_count = 0
    total_count = 0

    # 1. Health Check
    print("🏥 Health Check")
    total_count += 1
    ok, data = test_endpoint(
        "GET /api/adw/health", "GET", "/api/adw/health"
    )
    if ok:
        success_count += 1
        print(f"  Status: {data['status']}")
    print()

    # 2. Offensive Status (mock for now)
    print("🔴 Offensive AI (Red Team) - Mock Data")
    total_count += 1
    ok, data = test_endpoint(
        "GET /api/adw/offensive/status", "GET", "/api/adw/offensive/status"
    )
    if ok:
        success_count += 1
        print(f"  Status: {data['status']}")
        print(f"  Active campaigns: {data['active_campaigns']}")
        print(f"  Total exploits: {data['total_exploits']}")
    print()

    # 3. Create Campaign (mock for now)
    total_count += 1
    ok, data = test_endpoint(
        "POST /api/adw/offensive/campaign",
        "POST",
        "/api/adw/offensive/campaign",
        json={"objective": "Test integration", "scope": ["192.168.1.0/24"]},
    )
    if ok:
        success_count += 1
        print(f"  Campaign ID: {data['campaign_id']}")
        print(f"  Status: {data['status']}")
    print()

    # 4. List Campaigns (mock for now)
    total_count += 1
    ok, data = test_endpoint(
        "GET /api/adw/offensive/campaigns", "GET", "/api/adw/offensive/campaigns"
    )
    if ok:
        success_count += 1
        print(f"  Total campaigns: {data['total']}")
        print(f"  Active: {data['active']}")
    print()

    # 5. Defensive Status (mock for now)
    print("🔵 Defensive AI (Blue Team) - Mock Data")
    total_count += 1
    ok, data = test_endpoint(
        "GET /api/adw/defensive/status", "GET", "/api/adw/defensive/status"
    )
    if ok:
        success_count += 1
        print(f"  Status: {data['status']}")
        print(f"  Active agents: {data['active_agents']}/{data['total_agents']}")
        print(f"  Threats detected: {data['threats_detected']}")
    print()

    # 6. Threats (mock for now)
    total_count += 1
    ok, data = test_endpoint(
        "GET /api/adw/defensive/threats", "GET", "/api/adw/defensive/threats"
    )
    if ok:
        success_count += 1
        print(f"  Active threats: {len(data)}")
    print()

    # 7. Coagulation Status (mock for now)
    total_count += 1
    ok, data = test_endpoint(
        "GET /api/adw/defensive/coagulation", "GET", "/api/adw/defensive/coagulation"
    )
    if ok:
        success_count += 1
        print(f"  Status: {data['status']}")
        print(f"  Cascades completed: {data['cascades_completed']}")
    print()

    # 8. Purple Metrics (REAL DATA!)
    print("🟣 Purple Team - REAL DATA ✨")
    total_count += 1
    ok, data = test_endpoint(
        "GET /api/adw/purple/metrics", "GET", "/api/adw/purple/metrics"
    )
    if ok:
        success_count += 1
        print(f"  Status: {data['status']}")
        print(f"  Cycles completed: {data['cycles_completed']}")
        print(f"  Red Team score: {data['red_team_score']:.2f}")
        print(f"  Blue Team score: {data['blue_team_score']:.2f}")
        print(f"  Red trend: {data['improvement_trend']['red']}")
        print(f"  Blue trend: {data['improvement_trend']['blue']}")
    print()

    # 9. Trigger Evolution Cycle (REAL DATA!)
    total_count += 1
    ok, data = test_endpoint(
        "POST /api/adw/purple/cycle", "POST", "/api/adw/purple/cycle"
    )
    if ok:
        success_count += 1
        print(f"  Cycle ID: {data['cycle_id']}")
        print(f"  Status: {data['status']}")
    print()

    # 10. Overview (includes real purple data)
    print("📊 ADW Overview")
    total_count += 1
    ok, data = test_endpoint("GET /api/adw/overview", "GET", "/api/adw/overview")
    if ok:
        success_count += 1
        print(f"  Overall status: {data['status']}")
        print(f"  Offensive status: {data['offensive']['status']}")
        print(f"  Defensive status: {data['defensive']['status']}")
        print(f"  Purple status: {data['purple']['status']}")
    print()

    # Summary
    print("=" * 70)
    print(f"RESULTS: {success_count}/{total_count} endpoints passing")
    print("=" * 70)
    print()

    if success_count == total_count:
        print("✅ ALL TESTS PASSED!")
        print()
        print("Purple Team Integration: REAL DATA ✨")
        print("Offensive/Defensive: Mock data (ready for real integration)")
        print()
        print("To enable real Offensive/Defensive integration:")
        print("1. Uncomment service imports in adw_router.py")
        print("2. Uncomment dependency injection functions")
        print("3. Uncomment real integration code in endpoint functions")
        print("4. Set ANTHROPIC_API_KEY environment variable")
        return 0
    else:
        print(f"❌ {total_count - success_count} tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
