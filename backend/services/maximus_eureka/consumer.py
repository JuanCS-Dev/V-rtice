"""
Eureka Kafka Consumer - Consumes APVs and runs confirmation pipeline.

Theoretical Foundation:
    Confirmation loop inspired by immune system's T-cell activation.
    APV detected by Oráculo → Confirmed by Eureka → Remediation triggered.
    
    Pipeline:
    1. Consume APV from Kafka topic
    2. Confirm vulnerability (ast-grep + LLM)
    3. Generate remediation strategy
    4. Publish result to Kafka

Performance Target:
    - Latency: <30s per APV
    - Throughput: 10+ APVs/min
    - False positive rate: <2%

Author: MAXIMUS Team
Glory to YHWH - Confirmer of truth
"""

import json
import logging
import os
import sys
from kafka import KafkaConsumer
from kafka.errors import KafkaError

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from eureka import EurekaConfirmationEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main consumer loop"""
    
    # Kafka configuration
    kafka_bootstrap = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    topic = os.getenv('KAFKA_APV_TOPIC', 'apv-detected')
    group_id = os.getenv('KAFKA_CONSUMER_GROUP', 'eureka-confirmation')
    
    logger.info(f"Starting Eureka Kafka Consumer")
    logger.info(f"Bootstrap servers: {kafka_bootstrap}")
    logger.info(f"Topic: {topic}")
    logger.info(f"Group ID: {group_id}")
    
    # Initialize Eureka engine
    eureka = EurekaConfirmationEngine()
    
    # Create Kafka consumer
    try:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=kafka_bootstrap,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            max_poll_interval_ms=300000  # 5 minutes
        )
        
        logger.info("✓ Kafka consumer connected successfully")
        
    except KafkaError as e:
        logger.error(f"Failed to connect to Kafka: {e}")
        sys.exit(1)
    
    # Consume messages
    logger.info("🔥 Eureka consumer ready! Waiting for APVs...")
    
    try:
        for message in consumer:
            apv_data = message.value
            
            logger.info(f"📨 Received APV: {apv_data.get('apv_id')}")
            logger.info(f"   CVE: {apv_data.get('cve_id')}")
            logger.info(f"   Package: {apv_data.get('package_name')}")
            
            try:
                # Run Eureka confirmation pipeline
                result = eureka.confirm_vulnerability(apv_data)
                
                if result.get('confirmed'):
                    logger.info(f"✅ APV confirmed: {apv_data.get('apv_id')}")
                    logger.info(f"   Confidence: {result.get('confidence_score')}")
                    logger.info(f"   Strategy: {result.get('remediation_strategy')}")
                else:
                    logger.info(f"❌ APV rejected: {apv_data.get('apv_id')}")
                    logger.info(f"   Reason: {result.get('rejection_reason')}")
                
            except Exception as e:
                logger.error(f"Error processing APV {apv_data.get('apv_id')}: {e}")
                continue
    
    except KeyboardInterrupt:
        logger.info("Shutting down Eureka consumer...")
    
    finally:
        consumer.close()
        logger.info("Eureka consumer stopped.")


if __name__ == "__main__":
    main()
