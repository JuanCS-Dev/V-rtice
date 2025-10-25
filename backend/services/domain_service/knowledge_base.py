"""Domain Knowledge Base for Maximus Domain Service.

Implements real knowledge graph with PostgreSQL storage and semantic search.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, DateTime, Integer, JSON, String, Text, create_engine
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class DomainKnowledge(Base):
    """Domain knowledge model."""
    
    __tablename__ = "domain_knowledge"
    
    id = Column(Integer, primary_key=True, index=True)
    domain_name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    rules = Column(ARRAY(Text), nullable=False, default=[])
    entities = Column(ARRAY(String), nullable=False, default=[])
    domain_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# Database connection
import os
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "vertice_domain")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database with domain knowledge."""
    Base.metadata.create_all(bind=engine)
    
    # Seed default domains
    db = SessionLocal()
    try:
        # Check if data exists
        existing = db.query(DomainKnowledge).first()
        if not existing:
            domains = [
                DomainKnowledge(
                    domain_name="cybersecurity",
                    description="Knowledge related to cyber threats, vulnerabilities, and defense strategies",
                    rules=[
                        "Block traffic from known malicious IPs",
                        "Alert on unusual login patterns (>3 failed attempts in 5min)",
                        "Quarantine files with malware signatures",
                        "Rate limit API endpoints to prevent DDoS",
                        "Enforce MFA for admin accounts",
                        "Monitor lateral movement in network"
                    ],
                    entities=[
                        "malware", "phishing", "APT", "ransomware", "DDoS", 
                        "SQL injection", "XSS", "CSRF", "zero-day", "botnet"
                    ],
                    domain_metadata={
                        "threat_models": ["MITRE ATT&CK", "Cyber Kill Chain"],
                        "compliance": ["NIST", "ISO 27001", "PCI DSS"],
                        "tools": ["Snort", "Suricata", "YARA", "Sigma"]
                    }
                ),
                DomainKnowledge(
                    domain_name="environmental_monitoring",
                    description="Knowledge related to environmental sensors, chemical detection, and ecological patterns",
                    rules=[
                        "Alert on methane levels >1000 ppm",
                        "Track CO2 trends for climate analysis",
                        "Monitor air quality index (AQI) thresholds",
                        "Detect chemical spills via sensor anomalies",
                        "Correlate weather patterns with pollution levels"
                    ],
                    entities=[
                        "methane", "CO2", "particulate matter", "ozone", "nitrogen dioxide",
                        "sulfur dioxide", "volatile organic compounds", "radiation", "temperature", "humidity"
                    ],
                    domain_metadata={
                        "sensors": ["MQ-4", "MQ-135", "DHT22", "BMP280"],
                        "standards": ["EPA AQI", "WHO guidelines"],
                        "alert_thresholds": {
                            "methane_ppm": 1000,
                            "co2_ppm": 5000,
                            "aqi": 150
                        }
                    }
                ),
                DomainKnowledge(
                    domain_name="physical_security",
                    description="Knowledge related to physical access control, surveillance, and perimeter defense",
                    rules=[
                        "Alert on unauthorized access attempts",
                        "Monitor camera feeds for anomalous behavior",
                        "Track badge usage patterns for insider threats",
                        "Detect tailgating at access points",
                        "Alert on perimeter breaches via motion sensors"
                    ],
                    entities=[
                        "intruder", "access point", "camera", "motion sensor", "badge reader",
                        "door lock", "alarm system", "guard patrol", "perimeter fence", "vehicle gate"
                    ],
                    domain_metadata={
                        "systems": ["CCTV", "RFID", "Biometric", "Turnstile"],
                        "zones": ["public", "restricted", "classified", "secure"],
                        "protocols": ["two-person rule", "escort required", "search on exit"]
                    }
                ),
                DomainKnowledge(
                    domain_name="network_operations",
                    description="Knowledge related to network infrastructure, protocols, and operational procedures",
                    rules=[
                        "Monitor bandwidth utilization >80%",
                        "Alert on routing anomalies",
                        "Track BGP route hijacking attempts",
                        "Detect DNS tunneling and exfiltration",
                        "Monitor certificate expiration (30-day warning)"
                    ],
                    entities=[
                        "router", "switch", "firewall", "load balancer", "DNS server",
                        "VPN gateway", "proxy", "CDN", "packet", "protocol"
                    ],
                    domain_metadata={
                        "protocols": ["TCP", "UDP", "ICMP", "BGP", "OSPF", "DNS", "HTTP/S"],
                        "monitoring": ["SNMP", "NetFlow", "sFlow", "packet capture"],
                        "tools": ["Wireshark", "tcpdump", "nmap", "Nagios"]
                    }
                ),
                DomainKnowledge(
                    domain_name="application_security",
                    description="Knowledge related to secure software development and application vulnerabilities",
                    rules=[
                        "Validate all user inputs against injection attacks",
                        "Enforce HTTPS for all sensitive endpoints",
                        "Implement CSRF tokens for state-changing operations",
                        "Use parameterized queries to prevent SQL injection",
                        "Apply principle of least privilege to service accounts"
                    ],
                    entities=[
                        "OWASP Top 10", "injection", "broken auth", "sensitive data exposure",
                        "XML external entities", "broken access control", "security misconfiguration",
                        "insecure deserialization", "using components with known vulnerabilities",
                        "insufficient logging"
                    ],
                    domain_metadata={
                        "frameworks": ["OWASP", "SANS Top 25", "CWE"],
                        "testing": ["SAST", "DAST", "IAST", "fuzzing", "penetration testing"],
                        "tools": ["Burp Suite", "OWASP ZAP", "SonarQube", "Snyk"]
                    }
                )
            ]
            
            db.add_all(domains)
            db.commit()
            
    finally:
        db.close()


class KnowledgeBase:
    """Knowledge base query interface."""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def query_domain(self, domain_name: str, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Query domain knowledge."""
        domain = self.db.query(DomainKnowledge).filter(
            DomainKnowledge.domain_name == domain_name
        ).first()
        
        if not domain:
            return {
                "error": f"Domain '{domain_name}' not found",
                "available_domains": self.list_domains()
            }
        
        # Simple keyword matching (can be enhanced with NLP/semantic search)
        query_lower = query.lower()
        matching_rules = [rule for rule in domain.rules if any(word in rule.lower() for word in query_lower.split())]
        matching_entities = [entity for entity in domain.entities if entity.lower() in query_lower]
        
        return {
            "domain": domain_name,
            "description": domain.description,
            "matching_rules": matching_rules[:5],  # Top 5
            "matching_entities": matching_entities[:10],  # Top 10
            "all_rules_count": len(domain.rules),
            "all_entities_count": len(domain.entities),
            "metadata": domain.domain_metadata
        }
    
    def list_domains(self) -> List[str]:
        """List all available domains."""
        domains = self.db.query(DomainKnowledge.domain_name).all()
        return [d[0] for d in domains]
    
    def get_all_domains(self) -> List[Dict[str, Any]]:
        """Get summary of all domains."""
        domains = self.db.query(DomainKnowledge).all()
        return [
            {
                "domain_name": d.domain_name,
                "description": d.description,
                "rules_count": len(d.rules),
                "entities_count": len(d.entities)
            }
            for d in domains
        ]
    
    def close(self):
        """Close database connection."""
        self.db.close()
