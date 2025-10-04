"""ADR Core Service - Autonomous Detection & Response (Legacy Version).

This module represents a previous, monolithic version of the ADR Core Service.
It contains the initial structures for detection and response, which have since
been refactored into more modular engines and connectors in the current version.

This file is retained for historical and reference purposes.

Author: Juan (Arquiteto)
Date: 2025-10-01
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio
import logging
from uuid import uuid4
import hashlib
import os
import re
import time

# Setup basic logging for the legacy application
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Aurora ADR Core Service (Legacy)",
    description="Autonomous Detection & Response - Democratizing Enterprise Security",
    version="1.0.0-alpha",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Legacy Models
# ============================================================================

class ThreatDetection(BaseModel):
    """Represents a threat detection in the legacy system."""
    threat_id: str
    type: str
    severity: str
    source: str
    indicators: List[str]
    threat_score: int
    confidence: str
    timestamp: str
    raw_data: Optional[Dict[str, Any]] = None

class ResponseAction(BaseModel):
    """Represents a response action in the legacy system."""
    action_id: str
    threat_id: str
    action_type: str
    target: str
    status: str
    timestamp: str
    response_time_ms: Optional[int] = None
    details: Optional[Dict[str, Any]] = None

# ============================================================================
# Legacy State Management
# ============================================================================

class ADRState:
    """Manages the global state of the legacy ADR service."""
    def __init__(self):
        """Initializes the ADRState."""
        self.threats_detected: List[ThreatDetection] = []
        self.responses_executed: List[ResponseAction] = []
        self.is_armed: bool = True
        self.risk_threshold: int = 70

    def add_threat(self, threat: ThreatDetection):
        """Adds a detected threat to the state."""
        self.threats_detected.append(threat)
        logger.info(f"Threat detected: {threat.type} | Score: {threat.threat_score}")

# Global state instance for the legacy app
adr_state = ADRState()

# ============================================================================
# Legacy Connectors (Dummy Implementations)
# ============================================================================

class IPIntelligenceConnector:
    """Dummy connector for IP intelligence in the legacy system."""
    async def enrich_threat_with_ip_context(self, threat_dict: dict) -> dict:
        threat_dict['enriched_context'] = {'ip_intel': 'dummy_data'}
        return threat_dict

class ThreatIntelConnector:
    """Dummy connector for threat intelligence in the legacy system."""
    async def enrich_threat_with_intel(self, threat_dict: dict) -> dict:
        threat_dict['enriched_context'] = {'threat_intel': 'dummy_data'}
        return threat_dict

# ============================================================================
# Legacy Engines (Simplified Implementations)
# ============================================================================

class DetectionEngine:
    """A simplified detection engine from the legacy system."""
    async def analyze_file(self, file_path: str) -> ThreatDetection:
        """Analyzes a file based on a dummy hash check."""
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        
        # Dummy check
        is_malicious = 'bad' in file_path
        threat_score = 95 if is_malicious else 10

        return ThreatDetection(
            threat_id=str(uuid4()),
            type='malware' if is_malicious else 'unknown',
            severity='critical' if is_malicious else 'low',
            source=file_path,
            indicators=[f"SHA256: {file_hash}"],
            threat_score=threat_score,
            confidence='high' if is_malicious else 'low',
            timestamp=datetime.utcnow().isoformat(),
            raw_data={'file_hash': file_hash}
        )

# Instantiate legacy components
detection_engine = DetectionEngine()
ip_intel_connector = IPIntelligenceConnector()
threat_intel_connector = ThreatIntelConnector()

# ============================================================================
# Legacy API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Provides basic information about the legacy service."""
    return {
        "service": "Aurora ADR Core (Legacy)",
        "version": "1.0.0-alpha",
        "status": "operational_legacy",
    }

@app.post("/api/adr/analyze/file")
async def analyze_file(file_path: str, enrich: bool = True):
    """Analyzes a file for threats using the legacy detection engine."""
    try:
        threat = await detection_engine.analyze_file(file_path)
        threat_dict = threat.dict()

        if enrich:
            threat_dict = await threat_intel_connector.enrich_threat_with_intel(threat_dict)

        adr_state.add_threat(ThreatDetection(**threat_dict))

        return {
            "success": True,
            "threat": threat_dict,
            "will_auto_respond": threat.threat_score >= adr_state.risk_threshold,
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in legacy file analysis: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")

if __name__ == "__main__":
    logger.info("Starting Legacy Aurora ADR Core Service for debugging.")
    uvicorn.run(app, host="0.0.0.0", port=8014)