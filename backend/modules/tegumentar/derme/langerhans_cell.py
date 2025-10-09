"""Células de Langerhans digitais - captura e disseminação de antígenos."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import secrets
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import asyncpg
import httpx
from aiokafka import AIOKafkaProducer

from ..config import TegumentarSettings, get_settings
from ..metrics import (
    record_antigen_capture,
    record_lymphnode_validation,
    record_vaccination,
)
from .deep_inspector import InspectionResult
from .ml.feature_extractor import FeatureExtractor
from .stateful_inspector import FlowObservation
from ..lymphnode import LymphnodeAPI

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class AntigenRecord:
    antigen_id: str
    src_ip: str
    dst_ip: str
    protocol: str
    anomaly_score: float
    payload_preview: str


class LangerhansCell:
    """Captures anomalous payloads and publishes them for adaptive immunity."""

    def __init__(self, settings: Optional[TegumentarSettings] = None):
        self._settings = settings or get_settings()
        self._pool: Optional[asyncpg.Pool] = None
        self._producer: Optional[AIOKafkaProducer] = None
        self._feature_extractor = FeatureExtractor()
        self._lymphnode_api = LymphnodeAPI(self._settings)
        self._lock = asyncio.Lock()

    async def startup(self) -> None:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self._settings.postgres_dsn, min_size=2, max_size=5)
            await self._initialise_schema()
        if self._producer is None:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self._settings.kafka_bootstrap_servers,
                value_serializer=lambda payload: json.dumps(payload).encode("utf-8"),
            )
            await self._producer.start()

    async def shutdown(self) -> None:
        if self._producer:
            await self._producer.stop()
            self._producer = None
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def capture_antigen(
        self,
        observation: FlowObservation,
        inspection: InspectionResult,
        payload: bytes,
    ) -> AntigenRecord:
        if inspection.anomaly_score is None:
            raise ValueError("Inspection must contain anomaly score to capture antigen.")
        antigen_id = secrets.token_hex(8)
        preview = base64.b64encode(payload[:512]).decode("ascii")
        record = AntigenRecord(
            antigen_id=antigen_id,
            src_ip=observation.src_ip,
            dst_ip=observation.dst_ip,
            protocol=observation.protocol,
            anomaly_score=inspection.anomaly_score,
            payload_preview=preview,
        )

        await self._store(record)
        await self._publish(record)
        record_antigen_capture(observation.protocol)

        threat_report = {
            "threat_id": record.antigen_id,
            "threat_type": observation.protocol.lower(),
            "severity": self._severity_from_score(inspection.anomaly_score),
            "anomaly_score": inspection.anomaly_score,
            "source_ip": record.src_ip,
            "destination_ip": record.dst_ip,
            "payload_preview": record.payload_preview,
            "source": "tegumentar",
        }

        severity = threat_report["severity"]
        start = time.perf_counter()
        try:
            validation = await self._lymphnode_api.submit_threat(threat_report)
            latency = time.perf_counter() - start
            record_lymphnode_validation(
                "confirmed" if validation.confirmed else "rejected",
                severity,
                latency,
            )
        except httpx.HTTPError as exc:
            latency = time.perf_counter() - start
            record_lymphnode_validation("error", severity, latency)
            logger.error("Falha ao comunicar Linfonodo: %s", exc)
            logger.debug("Threat report descartado: %s", threat_report, exc_info=True)
            return record

        if validation.confirmed:
            logger.info(
                "Linfonodo confirmou ameaça %s (confidence=%.2f)",
                validation.threat_id,
                validation.confidence,
            )
            rule = {
                "id": validation.threat_id,
                "signature": record.payload_preview,
                "severity": validation.severity or threat_report["severity"],
                "anomaly_score": inspection.anomaly_score,
                "source": "tegumentar",
                "created_at": datetime.fromtimestamp(observation.timestamp).isoformat(),
            }
            try:
                await self._lymphnode_api.broadcast_vaccination(rule)
                record_vaccination("success")
            except httpx.HTTPError as exc:
                logger.error("Falha ao disparar vacinação %s: %s", rule["id"], exc)
                logger.debug("Rule payload: %s", rule, exc_info=True)
                record_vaccination("failure")
        else:
            logger.warning("Linfonodo não confirmou ameaça %s", record.antigen_id)

        logger.info("Captured antigen %s score=%.3f", antigen_id, inspection.anomaly_score)
        return record

    async def _store(self, record: AntigenRecord) -> None:
        if not self._pool:
            raise RuntimeError("LangerhansCell not initialised; call startup()")
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO tegumentar_antigens
                    (antigen_id, src_ip, dst_ip, protocol, anomaly_score, payload_preview, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
                """,
                record.antigen_id,
                record.src_ip,
                record.dst_ip,
                record.protocol,
                record.anomaly_score,
                record.payload_preview,
            )

    async def _publish(self, record: AntigenRecord) -> None:
        if not self._producer:
            raise RuntimeError("Kafka producer not initialised")
        payload = {
            "antigen_id": record.antigen_id,
            "src_ip": record.src_ip,
            "dst_ip": record.dst_ip,
            "protocol": record.protocol,
            "anomaly_score": record.anomaly_score,
            "payload_preview": record.payload_preview,
        }
        async with self._lock:
            await self._producer.send_and_wait(self._settings.langerhans_topic, payload)

    @staticmethod
    def _severity_from_score(score: float) -> str:
        if score >= 0.98:
            return "critical"
        if score >= 0.9:
            return "high"
        if score >= 0.75:
            return "medium"
        return "low"

    async def _initialise_schema(self) -> None:
        if not self._pool:
            return
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tegumentar_antigens (
                    antigen_id text PRIMARY KEY,
                    src_ip inet NOT NULL,
                    dst_ip inet NOT NULL,
                    protocol text NOT NULL,
                    anomaly_score double precision NOT NULL,
                    payload_preview text NOT NULL,
                    created_at timestamp with time zone NOT NULL
                );
                """
            )


__all__ = ["LangerhansCell", "AntigenRecord"]
