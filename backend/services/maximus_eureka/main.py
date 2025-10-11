"""
MAXIMUS Eureka - Main Entry Point.

Runs Eureka orchestrator for vulnerability confirmation and remediation.

Phase 2: Consumer → Confirmation pipeline
Phase 3: Will add Remediation Strategies
Phase 4: Will add Git Integration + PR automation

Usage:
    # Run with defaults
    python main.py
    
    # Custom Kafka broker
    python main.py --kafka-broker kafka.example.com:9092
    
    # Custom codebase root
    python main.py --codebase-root /path/to/code

Author: MAXIMUS Team
Date: 2025-01-10
Glory to YHWH - The God who orchestrates all things
"""

import asyncio
import argparse
import logging
import signal
from pathlib import Path
from typing import Optional

from orchestration.eureka_orchestrator import EurekaOrchestrator
from consumers.apv_consumer import APVConsumerConfig
from confirmation.vulnerability_confirmer import ConfirmationConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('eureka.log')
    ]
)

logger = logging.getLogger(__name__)

# Global orchestrator for signal handling
_orchestrator: Optional[EurekaOrchestrator] = None


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='MAXIMUS Eureka - Vulnerability Confirmation & Remediation'
    )
    
    # Kafka configuration
    parser.add_argument(
        '--kafka-broker',
        default='localhost:9092',
        help='Kafka bootstrap server (default: localhost:9092)'
    )
    parser.add_argument(
        '--kafka-topic',
        default='maximus.adaptive-immunity.apv',
        help='Kafka topic for APVs (default: maximus.adaptive-immunity.apv)'
    )
    parser.add_argument(
        '--kafka-group',
        default='eureka-consumer-group',
        help='Kafka consumer group ID (default: eureka-consumer-group)'
    )
    
    # Codebase configuration
    parser.add_argument(
        '--codebase-root',
        type=Path,
        default=Path.cwd(),
        help='Root directory of codebase to scan (default: current directory)'
    )
    
    # Redis configuration
    parser.add_argument(
        '--redis-url',
        default='redis://localhost:6379/0',
        help='Redis URL for caching (default: redis://localhost:6379/0)'
    )
    
    return parser.parse_args()


async def shutdown(signal_name: str) -> None:
    """Handle shutdown signals gracefully."""
    logger.info(f"🛑 Received {signal_name}, shutting down...")
    
    if _orchestrator:
        await _orchestrator.stop()
    
    # Cancel all remaining tasks
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("✅ Shutdown complete")


async def main() -> None:
    """Main entry point."""
    global _orchestrator
    
    args = parse_args()
    
    logger.info("🚀 Starting MAXIMUS Eureka Orchestrator...")
    logger.info(f"   Kafka: {args.kafka_broker}")
    logger.info(f"   Topic: {args.kafka_topic}")
    logger.info(f"   Codebase: {args.codebase_root}")
    logger.info(f"   Redis: {args.redis_url}")
    
    # Validate codebase path
    if not args.codebase_root.exists():
        logger.error(f"❌ Codebase root does not exist: {args.codebase_root}")
        return
    
    # Create configurations
    consumer_config = APVConsumerConfig(
        kafka_bootstrap_servers=args.kafka_broker,
        kafka_topic=args.kafka_topic,
        kafka_group_id=args.kafka_group,
        redis_cache_url=args.redis_url,
    )
    
    confirmer_config = ConfirmationConfig(
        codebase_root=args.codebase_root,
        cache_enabled=True,
    )
    
    # Create orchestrator
    _orchestrator = EurekaOrchestrator(consumer_config, confirmer_config)
    
    # Setup signal handlers
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        def make_handler(sig_name: str) -> None:
            asyncio.create_task(shutdown(sig_name))
        
        loop.add_signal_handler(sig, lambda s=sig.name: make_handler(s))
    
    try:
        # Start orchestrator (runs until stopped)
        await _orchestrator.start()
    except KeyboardInterrupt:
        logger.info("🛑 Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
    finally:
        if _orchestrator:
            await _orchestrator.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Stopped by user")

