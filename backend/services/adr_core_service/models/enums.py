"""
Enumerations for ADR Core Service
"""
from enum import Enum


class SeverityLevel(str, Enum):
    """Threat severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ThreatType(str, Enum):
    """Types of threats detected"""
    MALWARE = "malware"
    RANSOMWARE = "ransomware"
    TROJAN = "trojan"
    ROOTKIT = "rootkit"
    WORM = "worm"
    SPYWARE = "spyware"
    ADWARE = "adware"
    EXPLOIT = "exploit"
    BACKDOOR = "backdoor"
    BOTNET = "botnet"
    APT = "apt"
    ZERO_DAY = "zero_day"
    PHISHING = "phishing"
    C2_COMMUNICATION = "c2_communication"
    DATA_EXFILTRATION = "data_exfiltration"
    LATERAL_MOVEMENT = "lateral_movement"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    PERSISTENCE = "persistence"
    DEFENSE_EVASION = "defense_evasion"
    CREDENTIAL_ACCESS = "credential_access"
    DISCOVERY = "discovery"
    COLLECTION = "collection"
    COMMAND_AND_CONTROL = "command_and_control"
    IMPACT = "impact"
    NETWORK_ANOMALY = "network_anomaly"
    BEHAVIORAL_ANOMALY = "behavioral_anomaly"
    UNKNOWN = "unknown"


class ActionType(str, Enum):
    """Response action types"""
    BLOCK_IP = "block_ip"
    BLOCK_DOMAIN = "block_domain"
    BLOCK_HASH = "block_hash"
    QUARANTINE_FILE = "quarantine_file"
    KILL_PROCESS = "kill_process"
    ISOLATE_HOST = "isolate_host"
    DISABLE_USER = "disable_user"
    RESET_PASSWORD = "reset_password"
    ALERT = "alert"
    NOTIFY = "notify"
    LOG = "log"
    SNAPSHOT = "snapshot"
    COLLECT_EVIDENCE = "collect_evidence"
    ESCALATE = "escalate"
    CUSTOM = "custom"


class ActionStatus(str, Enum):
    """Status of response actions"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ROLLED_BACK = "rolled_back"


class DetectionSource(str, Enum):
    """Source of detection"""
    FILE_ANALYSIS = "file_analysis"
    NETWORK_ANALYSIS = "network_analysis"
    PROCESS_ANALYSIS = "process_analysis"
    MEMORY_ANALYSIS = "memory_analysis"
    BEHAVIORAL_ANALYSIS = "behavioral_analysis"
    SIGNATURE_MATCH = "signature_match"
    HEURISTIC = "heuristic"
    ML_MODEL = "ml_model"
    THREAT_INTEL = "threat_intel"
    CUSTOM_RULE = "custom_rule"
    EXTERNAL_FEED = "external_feed"


class PlaybookTrigger(str, Enum):
    """Playbook trigger conditions"""
    THREAT_TYPE = "threat_type"
    SEVERITY_LEVEL = "severity_level"
    MITRE_TECHNIQUE = "mitre_technique"
    CONFIDENCE_THRESHOLD = "confidence_threshold"
    CUSTOM_CONDITION = "custom_condition"


class AlertStatus(str, Enum):
    """Alert lifecycle status"""
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    REMEDIATED = "remediated"
    FALSE_POSITIVE = "false_positive"
    CLOSED = "closed"


class ConnectorType(str, Enum):
    """Connector integration types"""
    IP_INTELLIGENCE = "ip_intelligence"
    THREAT_INTEL = "threat_intel"
    MALWARE_ANALYSIS = "malware_analysis"
    SIEM = "siem"
    EDR = "edr"
    FIREWALL = "firewall"
    IDS_IPS = "ids_ips"
    SANDBOX = "sandbox"
    VULNERABILITY_SCANNER = "vulnerability_scanner"
    CUSTOM = "custom"


class EngineType(str, Enum):
    """Analysis engine types"""
    DETECTION = "detection"
    RESPONSE = "response"
    CORRELATION = "correlation"
    ENRICHMENT = "enrichment"
    ML_INFERENCE = "ml_inference"
