"""
Reactive Fabric Core Service
Orchestrates honeypots and aggregates threat intelligence.

Part of MAXIMUS VÉRTICE - Projeto Tecido Reativo
Sprint 1: Real implementation with PostgreSQL + Kafka
"""

from .database import Database
from .kafka_producer import (
    KafkaProducer,
    create_threat_detected_message,
    create_honeypot_status_message
)

# Re-export commonly used models
from .models import (
    # Enums
    HoneypotType,
    HoneypotStatus,
    AttackSeverity,
    ProcessingStatus,
    
    # Honeypot models
    Honeypot,
    HoneypotCreate,
    HoneypotStats,
    HoneypotHealthCheck,
    
    # Attack models
    Attack,
    AttackCreate,
    AttackSummary,
    
    # TTP models
    TTP,
    TTPCreate,
    TTPFrequency,
    
    # IoC models
    IOC,
    IOCCreate,
    
    # Forensic models
    ForensicCapture,
    ForensicCaptureCreate,
    
    # API Response models
    HoneypotListResponse,
    AttackListResponse,
    TTPListResponse,
    HealthResponse,
    
    # Kafka message models
    ThreatDetectedMessage,
    HoneypotStatusMessage
)

__version__ = "1.0.0"

__all__ = [
    # Core classes
    "Database",
    "KafkaProducer",
    
    # Utility functions
    "create_threat_detected_message",
    "create_honeypot_status_message",
    
    # Enums
    "HoneypotType",
    "HoneypotStatus",
    "AttackSeverity",
    "ProcessingStatus",
    
    # Models
    "Honeypot",
    "HoneypotCreate",
    "HoneypotStats",
    "HoneypotHealthCheck",
    "Attack",
    "AttackCreate",
    "AttackSummary",
    "TTP",
    "TTPCreate",
    "TTPFrequency",
    "IOC",
    "IOCCreate",
    "ForensicCapture",
    "ForensicCaptureCreate",
    "HoneypotListResponse",
    "AttackListResponse",
    "TTPListResponse",
    "HealthResponse",
    "ThreatDetectedMessage",
    "HoneypotStatusMessage",
]
