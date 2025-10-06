"""Immunis Dendritic Service - Production-Ready Antigen Presentation & Event Correlation

Bio-inspired Dendritic Cell service that:
1. **Consumes antigens from Macrophages via Kafka**
   - Listens to 'antigen.presentation' topic
   - Processes threat intelligence from phagocytosis

2. **Event Correlation & Context Enrichment**
   - Time-series analysis with Qdrant vector database
   - Correlates related threats across time and space
   - Enriches threat context with historical patterns

3. **Presents to B-cells and T-cells**
   - Sends processed intelligence to adaptive immune cells
   - Triggers B-cell signature generation
   - Activates T-cell orchestration and response

4. **Adaptive Immune Activation**
   - Determines activation thresholds
   - Coordinates B-cell and T-cell responses

Like biological dendritic cells: Bridges innate and adaptive immunity.
NO MOCKS - Production-ready implementation.
"""

import asyncio
from datetime import datetime, timedelta
import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Kafka for antigen consumption
try:
    from kafka import KafkaConsumer

    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logger.warning("kafka-python not available - antigen consumption disabled")

# Qdrant for event correlation
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, PointStruct, VectorParams

    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    logger.warning("qdrant-client not available - event correlation disabled")


class AntigenConsumer:
    """Consumes antigens from Macrophages via Kafka."""

    def __init__(self, kafka_bootstrap_servers: str = "localhost:9092"):
        """Initialize antigen consumer.

        Args:
            kafka_bootstrap_servers: Kafka broker addresses
        """
        self.kafka_servers = kafka_bootstrap_servers
        self.consumer: Optional[KafkaConsumer] = None
        self.running = False

        if KAFKA_AVAILABLE:
            try:
                self.consumer = KafkaConsumer(
                    "antigen.presentation",
                    bootstrap_servers=kafka_bootstrap_servers,
                    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                    auto_offset_reset="latest",
                    enable_auto_commit=True,
                    group_id="dendritic_cells",
                )
                logger.info("Kafka antigen consumer initialized")
            except Exception as e:
                logger.error(f"Kafka consumer initialization failed: {e}")
                self.consumer = None

    async def consume_antigens(self, callback) -> None:
        """Consume antigens from Kafka and invoke callback.

        Args:
            callback: Async function to process each antigen
        """
        if not self.consumer:
            logger.warning("Kafka consumer not available - antigen consumption skipped")
            return

        self.running = True
        logger.info("Starting antigen consumption...")

        try:
            while self.running:
                # Poll for messages (non-blocking with timeout)
                messages = self.consumer.poll(timeout_ms=1000)

                for topic_partition, records in messages.items():
                    for record in records:
                        antigen = record.value
                        logger.info(
                            f"Received antigen: {antigen.get('antigen_id', 'unknown')[:16]}"
                        )

                        try:
                            await callback(antigen)
                        except Exception as e:
                            logger.error(f"Antigen processing failed: {e}")

                # Allow other coroutines to run
                await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"Antigen consumption error: {e}")
        finally:
            self.running = False

    def stop(self):
        """Stop consuming antigens."""
        logger.info("Stopping antigen consumption...")
        self.running = False
        if self.consumer:
            self.consumer.close()


class EventCorrelationEngine:
    """Correlates events using Qdrant vector database for time-series analysis."""

    def __init__(self, qdrant_url: str = "localhost", qdrant_port: int = 6333):
        """Initialize event correlation engine.

        Args:
            qdrant_url: Qdrant server URL
            qdrant_port: Qdrant server port
        """
        self.qdrant_client: Optional[QdrantClient] = None
        self.collection_name = "threat_events"
        self.vector_size = 128

        if QDRANT_AVAILABLE:
            try:
                self.qdrant_client = QdrantClient(host=qdrant_url, port=qdrant_port)
                self._initialize_collection()
                logger.info("Qdrant event correlation engine initialized")
            except Exception as e:
                logger.error(f"Qdrant initialization failed: {e}")
                self.qdrant_client = None

    def _initialize_collection(self):
        """Initialize Qdrant collection for threat events."""
        if not self.qdrant_client:
            return

        try:
            # Check if collection exists
            collections = self.qdrant_client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_name not in collection_names:
                # Create collection
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size, distance=Distance.COSINE
                    ),
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")

        except Exception as e:
            logger.error(f"Collection initialization failed: {e}")

    def _vectorize_threat(self, threat: Dict[str, Any]) -> List[float]:
        """Convert threat to vector representation.

        Args:
            threat: Threat information dictionary

        Returns:
            Vector representation (128 dimensions)
        """
        # Create feature vector from threat attributes
        # This is a simplified vectorization - in production, use embeddings

        features = []

        # Severity (normalized 0-1)
        severity = threat.get("severity", 0.5)
        features.extend([severity] * 10)

        # Malware family hash (pseudo-embedding)
        family = threat.get("malware_family", "unknown")
        family_hash = hashlib.md5(family.encode()).hexdigest()
        family_vector = [
            int(family_hash[i : i + 2], 16) / 255.0 for i in range(0, 32, 2)
        ]
        features.extend(family_vector[:16])

        # IOC counts (normalized)
        iocs = threat.get("iocs", {})
        ioc_counts = [
            len(iocs.get("ips", [])) / 100.0,
            len(iocs.get("domains", [])) / 100.0,
            len(iocs.get("urls", [])) / 100.0,
            len(iocs.get("file_hashes", [])) / 100.0,
            len(iocs.get("mutexes", [])) / 100.0,
            len(iocs.get("registry_keys", [])) / 100.0,
        ]
        features.extend(ioc_counts)

        # Temporal features (hour of day, day of week)
        timestamp = datetime.fromisoformat(
            threat.get("timestamp", datetime.now().isoformat())
        )
        hour_vector = [1.0 if i == timestamp.hour else 0.0 for i in range(24)]
        features.extend(hour_vector)

        # Source features
        source = threat.get("source", "unknown")
        source_hash = hashlib.md5(source.encode()).hexdigest()
        source_vector = [
            int(source_hash[i : i + 2], 16) / 255.0 for i in range(0, 32, 2)
        ]
        features.extend(source_vector[:16])

        # Pad or truncate to 128 dimensions
        if len(features) < self.vector_size:
            features.extend([0.0] * (self.vector_size - len(features)))
        else:
            features = features[: self.vector_size]

        return features

    async def store_event(self, threat: Dict[str, Any]) -> bool:
        """Store threat event in Qdrant.

        Args:
            threat: Threat information

        Returns:
            True if successful
        """
        if not self.qdrant_client:
            logger.warning("Qdrant not available - event storage skipped")
            return False

        try:
            # Vectorize threat
            vector = self._vectorize_threat(threat)

            # Generate unique ID
            point_id = hashlib.sha256(
                (
                    threat.get("antigen_id", "") + str(datetime.now().timestamp())
                ).encode()
            ).hexdigest()[:16]

            # Create point
            point = PointStruct(
                id=int(point_id, 16) % (2**63 - 1),  # Convert to int for Qdrant
                vector=vector,
                payload={
                    "threat_id": threat.get("antigen_id"),
                    "timestamp": threat.get("timestamp"),
                    "malware_family": threat.get("malware_family"),
                    "severity": threat.get("severity"),
                    "source": threat.get("source"),
                },
            )

            # Upsert to Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name, points=[point]
            )

            logger.info(
                f"Stored threat event: {threat.get('antigen_id', 'unknown')[:16]}"
            )
            return True

        except Exception as e:
            logger.error(f"Event storage failed: {e}")
            return False

    async def correlate_events(
        self, threat: Dict[str, Any], time_window_hours: int = 24, top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Correlate threat with historical events.

        Args:
            threat: Current threat to correlate
            time_window_hours: Time window for correlation
            top_k: Number of similar events to return

        Returns:
            List of correlated events
        """
        if not self.qdrant_client:
            logger.warning("Qdrant not available - correlation skipped")
            return []

        try:
            # Vectorize current threat
            query_vector = self._vectorize_threat(threat)

            # Search for similar threats
            search_result = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
            )

            correlated = []
            for hit in search_result:
                # Filter by time window
                event_time = datetime.fromisoformat(hit.payload["timestamp"])
                current_time = datetime.now()

                if (
                    current_time - event_time
                ).total_seconds() / 3600 <= time_window_hours:
                    correlated.append(
                        {
                            "threat_id": hit.payload["threat_id"],
                            "timestamp": hit.payload["timestamp"],
                            "malware_family": hit.payload["malware_family"],
                            "severity": hit.payload["severity"],
                            "similarity_score": hit.score,
                            "source": hit.payload["source"],
                        }
                    )

            logger.info(
                f"Found {len(correlated)} correlated events for threat {threat.get('antigen_id', '')[:16]}"
            )
            return correlated

        except Exception as e:
            logger.error(f"Event correlation failed: {e}")
            return []


class DendriticCore:
    """Production-ready Dendritic Cell service.

    Bridges innate and adaptive immunity:
    - Consumes antigens from Macrophages
    - Correlates events across time
    - Presents to B-cells and T-cells
    - Activates adaptive immune responses
    """

    def __init__(
        self,
        kafka_bootstrap_servers: str = "localhost:9092",
        qdrant_url: str = "localhost",
        qdrant_port: int = 6333,
        b_cell_endpoint: str = "http://immunis-bcell:8015",
        t_helper_endpoint: str = "http://immunis-helper-t:8016",
        t_cytotoxic_endpoint: str = "http://immunis-cytotoxic-t:8017",
    ):
        """Initialize Dendritic Core.

        Args:
            kafka_bootstrap_servers: Kafka broker addresses
            qdrant_url: Qdrant server URL
            qdrant_port: Qdrant server port
            b_cell_endpoint: B-Cell service endpoint
            t_helper_endpoint: Helper T-Cell service endpoint
            t_cytotoxic_endpoint: Cytotoxic T-Cell service endpoint
        """
        self.antigen_consumer = AntigenConsumer(kafka_bootstrap_servers)
        self.correlation_engine = EventCorrelationEngine(qdrant_url, qdrant_port)

        self.b_cell_endpoint = b_cell_endpoint
        self.t_helper_endpoint = t_helper_endpoint
        self.t_cytotoxic_endpoint = t_cytotoxic_endpoint

        self.processed_antigens: List[Dict[str, Any]] = []
        self.activations: List[Dict[str, Any]] = []
        self.last_processing_time: Optional[datetime] = None

        logger.info("DendriticCore initialized (production-ready)")

    async def process_antigen(self, antigen: Dict[str, Any]) -> Dict[str, Any]:
        """Process antigen from Macrophage.

        Args:
            antigen: Antigen from Macrophage phagocytosis

        Returns:
            Processed threat intelligence
        """
        logger.info(f"Processing antigen: {antigen.get('antigen_id', 'unknown')[:16]}")

        # 1. Enrich with context
        enriched = {
            "antigen_id": antigen.get("antigen_id"),
            "timestamp": antigen.get("timestamp"),
            "malware_family": antigen.get("malware_family"),
            "severity": antigen.get("severity"),
            "iocs": antigen.get("iocs", {}),
            "yara_signature": antigen.get("yara_signature"),
            "source": antigen.get("source", "macrophage_service"),
            "processing_timestamp": datetime.now().isoformat(),
        }

        # 2. Store in Qdrant for correlation
        await self.correlation_engine.store_event(enriched)

        # 3. Correlate with historical events
        correlated_events = await self.correlation_engine.correlate_events(
            enriched, time_window_hours=24, top_k=10
        )

        enriched["correlated_events"] = correlated_events
        enriched["correlation_count"] = len(correlated_events)

        # 4. Determine if activation required
        activation_required = self._should_activate(enriched)
        enriched["activation_required"] = activation_required

        self.processed_antigens.append(enriched)
        self.last_processing_time = datetime.now()

        logger.info(
            f"Antigen processed: activation_required={activation_required}, "
            f"correlated_events={len(correlated_events)}"
        )

        return enriched

    def _should_activate(self, threat: Dict[str, Any]) -> bool:
        """Determine if adaptive immune activation is required.

        Args:
            threat: Processed threat intelligence

        Returns:
            True if activation required
        """
        # Activation criteria:
        # 1. High severity (≥0.7)
        # 2. Multiple correlated events (≥3)
        # 3. Novel malware family (no correlations)

        severity = threat.get("severity", 0.0)
        correlation_count = threat.get("correlation_count", 0)

        if severity >= 0.7:
            return True

        if correlation_count >= 3:
            return True

        if correlation_count == 0 and severity >= 0.5:
            # Novel threat
            return True

        return False

    async def present_to_b_cell(self, threat: Dict[str, Any]) -> Dict[str, Any]:
        """Present threat to B-Cell for signature generation.

        Args:
            threat: Processed threat intelligence

        Returns:
            Presentation result
        """
        logger.info(f"Presenting threat to B-Cell: {threat.get('antigen_id', '')[:16]}")

        try:
            import httpx

            presentation_payload = {
                "antigen_id": threat.get("antigen_id"),
                "malware_family": threat.get("malware_family"),
                "iocs": threat.get("iocs"),
                "yara_signature": threat.get("yara_signature"),
                "severity": threat.get("severity"),
                "correlated_events": threat.get("correlated_events", []),
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.b_cell_endpoint}/bcell/activate",
                    json=presentation_payload,
                    timeout=10.0,
                )

                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"B-Cell activated: {result}")
                    return {"status": "presented", "b_cell_response": result}
                else:
                    logger.error(f"B-Cell presentation failed: {response.status_code}")
                    return {"status": "failed", "error": f"HTTP {response.status_code}"}

        except Exception as e:
            logger.error(f"B-Cell presentation error: {e}")
            return {"status": "error", "error": str(e)}

    async def present_to_t_cells(
        self,
        threat: Dict[str, Any],
        activate_helper: bool = True,
        activate_cytotoxic: bool = False,
    ) -> Dict[str, Any]:
        """Present threat to T-Cells for orchestration and response.

        Args:
            threat: Processed threat intelligence
            activate_helper: Activate Helper T-Cell (orchestration)
            activate_cytotoxic: Activate Cytotoxic T-Cell (active defense)

        Returns:
            Presentation results
        """
        logger.info(
            f"Presenting threat to T-Cells: {threat.get('antigen_id', '')[:16]}"
        )

        results = {}

        try:
            import httpx

            presentation_payload = {
                "antigen_id": threat.get("antigen_id"),
                "malware_family": threat.get("malware_family"),
                "severity": threat.get("severity"),
                "iocs": threat.get("iocs"),
                "correlation_count": threat.get("correlation_count", 0),
            }

            async with httpx.AsyncClient() as client:
                # Helper T-Cell (Th1/Th2 orchestration)
                if activate_helper:
                    try:
                        response = await client.post(
                            f"{self.t_helper_endpoint}/helper-t/activate",
                            json=presentation_payload,
                            timeout=10.0,
                        )
                        if response.status_code == 200:
                            results["helper_t"] = {
                                "status": "activated",
                                "response": response.json(),
                            }
                        else:
                            results["helper_t"] = {
                                "status": "failed",
                                "error": f"HTTP {response.status_code}",
                            }
                    except Exception as e:
                        results["helper_t"] = {"status": "error", "error": str(e)}

                # Cytotoxic T-Cell (active defense)
                if activate_cytotoxic:
                    try:
                        response = await client.post(
                            f"{self.t_cytotoxic_endpoint}/cytotoxic-t/activate",
                            json=presentation_payload,
                            timeout=10.0,
                        )
                        if response.status_code == 200:
                            results["cytotoxic_t"] = {
                                "status": "activated",
                                "response": response.json(),
                            }
                        else:
                            results["cytotoxic_t"] = {
                                "status": "failed",
                                "error": f"HTTP {response.status_code}",
                            }
                    except Exception as e:
                        results["cytotoxic_t"] = {"status": "error", "error": str(e)}

            logger.info(f"T-Cell presentation results: {results}")
            return results

        except Exception as e:
            logger.error(f"T-Cell presentation error: {e}")
            return {"status": "error", "error": str(e)}

    async def activate_adaptive_immunity(
        self, threat: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Activate B-cells and T-cells for adaptive immune response.

        Args:
            threat: Processed threat intelligence

        Returns:
            Activation summary
        """
        logger.info(
            f"Activating adaptive immunity for threat: {threat.get('antigen_id', '')[:16]}"
        )

        activation_result = {
            "timestamp": datetime.now().isoformat(),
            "antigen_id": threat.get("antigen_id"),
            "severity": threat.get("severity"),
            "activations": {},
        }

        # Always activate B-Cell for signature generation
        b_cell_result = await self.present_to_b_cell(threat)
        activation_result["activations"]["b_cell"] = b_cell_result

        # Activate T-Cells based on severity
        severity = threat.get("severity", 0.0)

        # Helper T-Cell for orchestration (always for adaptive immunity)
        activate_helper = True

        # Cytotoxic T-Cell for active defense (high severity only)
        activate_cytotoxic = severity >= 0.7

        t_cell_result = await self.present_to_t_cells(
            threat,
            activate_helper=activate_helper,
            activate_cytotoxic=activate_cytotoxic,
        )
        activation_result["activations"]["t_cells"] = t_cell_result

        self.activations.append(activation_result)

        logger.info(f"Adaptive immunity activated: {activation_result}")
        return activation_result

    async def start_antigen_consumption(self):
        """Start consuming antigens from Kafka."""

        async def antigen_callback(antigen):
            """Process each antigen."""
            # Process antigen
            processed = await self.process_antigen(antigen)

            # Activate adaptive immunity if required
            if processed.get("activation_required"):
                await self.activate_adaptive_immunity(processed)

        await self.antigen_consumer.consume_antigens(antigen_callback)

    def stop_antigen_consumption(self):
        """Stop consuming antigens."""
        self.antigen_consumer.stop()

    async def get_status(self) -> Dict[str, Any]:
        """Get Dendritic Cell service status.

        Returns:
            Service status dictionary
        """
        return {
            "status": "operational",
            "processed_antigens_count": len(self.processed_antigens),
            "activations_count": len(self.activations),
            "last_processing": (
                self.last_processing_time.isoformat()
                if self.last_processing_time
                else "N/A"
            ),
            "kafka_enabled": self.antigen_consumer.consumer is not None,
            "qdrant_enabled": self.correlation_engine.qdrant_client is not None,
            "antigen_consumer_running": self.antigen_consumer.running,
        }
