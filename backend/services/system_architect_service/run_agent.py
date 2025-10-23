#!/usr/bin/env python3
"""System Architect Agent Launcher - Production Ready

This script launches the System Architect Agent in standalone mode.

Usage:
    python run_agent.py                    # Run one patrol cycle
    python run_agent.py --continuous       # Run in continuous patrol mode
    python run_agent.py --interval 3       # Custom patrol interval (hours)
    python run_agent.py --service-url http://localhost:8900  # Custom service URL
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from agent import SystemArchitectAgentStandalone


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


async def run_one_patrol(agent: SystemArchitectAgentStandalone):
    """Run a single patrol cycle."""
    logging.info("\n" + "="*80)
    logging.info("SYSTEM ARCHITECT AGENT - SINGLE PATROL MODE")
    logging.info("="*80 + "\n")

    await agent.iniciar()

    try:
        await agent.patrulhar()

        logging.info("\n" + "="*80)
        logging.info("✅ PATROL COMPLETE")
        logging.info("="*80)
        logging.info(f"Patrol count: {agent.patrol_count}")
        logging.info(f"Critical gaps: {len(agent.critical_gaps)}")

    finally:
        await agent.parar()


async def run_continuous(agent: SystemArchitectAgentStandalone):
    """Run in continuous patrol mode."""
    logging.info("\n" + "="*80)
    logging.info("SYSTEM ARCHITECT AGENT - CONTINUOUS PATROL MODE")
    logging.info("="*80)
    logging.info(f"Patrol interval: {agent.patrol_interval}")
    logging.info("Press Ctrl+C to stop")
    logging.info("="*80 + "\n")

    await agent.iniciar()

    try:
        await agent.run_forever()
    except KeyboardInterrupt:
        logging.info("\n⚠️  Received interrupt signal - shutting down gracefully...")
    finally:
        await agent.parar()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="System Architect Agent - Continuous architectural analysis"
    )

    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run in continuous patrol mode (default: single patrol)"
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=6,
        help="Patrol interval in hours (default: 6)"
    )

    parser.add_argument(
        "--service-url",
        type=str,
        default="http://localhost:8900",
        help="System Architect Service URL (default: http://localhost:8900)"
    )

    parser.add_argument(
        "--docker-compose",
        type=str,
        default="/home/juan/vertice-dev/docker-compose.yml",
        help="Path to docker-compose.yml (default: /home/juan/vertice-dev/docker-compose.yml)"
    )

    parser.add_argument(
        "--agent-id",
        type=str,
        default="system_architect_001",
        help="Agent ID (default: system_architect_001)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Create agent
    agent = SystemArchitectAgentStandalone(
        agent_id=args.agent_id,
        service_url=args.service_url,
        patrol_interval_hours=args.interval,
        docker_compose_path=args.docker_compose
    )

    # Run agent
    if args.continuous:
        await run_continuous(agent)
    else:
        await run_one_patrol(agent)


if __name__ == "__main__":  # pragma: no cover
    try:  # pragma: no cover
        asyncio.run(main())  # pragma: no cover
    except KeyboardInterrupt:  # pragma: no cover
        print("\n👋 System Architect Agent stopped")  # pragma: no cover
        sys.exit(0)  # pragma: no cover
    except Exception as e:  # pragma: no cover
        logging.error(f"❌ Fatal error: {e}", exc_info=True)  # pragma: no cover
        sys.exit(1)  # pragma: no cover
