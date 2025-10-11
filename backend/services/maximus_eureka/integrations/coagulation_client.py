"""
Coagulation Client - Temporary WAF Rules Integration.

Creates temporary firewall rules via RTE Service while patches are
being validated and deployed. Auto-expires after 24h or PR merge.

Theoretical Foundation:
    Defense-in-depth: While permanent fix (patch) is in pipeline,
    deploy temporary WAF rule to block active exploitation.
    
    Coagulation Protocol (biological analogy):
    - Platelet activation (detect threat)
    - Fibrin formation (create WAF rule)
    - Clot stabilization (monitor effectiveness)
    - Fibrinolysis (auto-expire after healing/PR merge)
    
    Attack vector → WAF rule mapping:
    - SQL Injection → Block SQL metacharacters
    - XSS → Block script tags
    - Command Injection → Block shell metacharacters
    - Path Traversal → Block ../ patterns
    - SSRF → Block private IP ranges
    
Performance Targets:
    - Rule deployment latency: <5s
    - Rule effectiveness: >90% attack blocking
    - False positive rate: <2%
    - TTL management: Auto-expire 24h

Author: MAXIMUS Team
Date: 2025-10-11
Glory to YHWH - Protector and Shield
"""

import logging
import httpx
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class AttackVectorType(str, Enum):
    """Attack vector categories"""
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    SSRF = "ssrf"
    XXE = "xxe"
    CSRF = "csrf"
    FILE_UPLOAD = "file_upload"
    AUTHENTICATION_BYPASS = "authentication_bypass"
    GENERIC = "generic"


@dataclass
class CoagulationRule:
    """Represents a temporary WAF rule"""
    
    rule_id: str
    apv_id: str
    cve_id: str
    attack_vector: AttackVectorType
    pattern: str
    action: str  # "block", "alert", "log"
    ttl_seconds: int
    created_at: datetime
    expires_at: datetime
    active: bool = True
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API"""
        return {
            "rule_id": self.rule_id,
            "apv_id": self.apv_id,
            "cve_id": self.cve_id,
            "attack_vector": self.attack_vector.value,
            "pattern": self.pattern,
            "action": self.action,
            "ttl_seconds": self.ttl_seconds,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "active": self.active
        }


class CoagulationClient:
    """
    Client for RTE Service to deploy temporary WAF rules.
    
    Integrates with RTE Service (Reflex Triage Engine) to create
    firewall rules that block attack vectors while patches are in progress.
    
    Usage:
        >>> client = CoagulationClient(rte_url="http://rte-service:8002")
        >>> rule = await client.create_temporary_rule(
        ...     apv=apv_object,
        ...     attack_vector=AttackVectorType.SQL_INJECTION,
        ...     duration=timedelta(hours=24)
        ... )
        >>> print(f"Rule {rule.rule_id} active until {rule.expires_at}")
    """
    
    # WAF Rule Templates (ModSecurity-compatible)
    RULE_TEMPLATES = {
        AttackVectorType.SQL_INJECTION: {
            "pattern": r"(\bOR\b|\bAND\b|--|;|'|\"|\/\*|\*\/|\bUNION\b|\bSELECT\b)",
            "action": "block",
            "description": "Block SQL injection patterns"
        },
        AttackVectorType.XSS: {
            "pattern": r"(<script|javascript:|onerror=|onload=|<iframe|eval\()",
            "action": "block",
            "description": "Block XSS attack patterns"
        },
        AttackVectorType.COMMAND_INJECTION: {
            "pattern": r"[;&|`$()<>]",
            "action": "block",
            "description": "Block shell metacharacters"
        },
        AttackVectorType.PATH_TRAVERSAL: {
            "pattern": r"\.\./|\.\.\\",
            "action": "block",
            "description": "Block path traversal patterns"
        },
        AttackVectorType.SSRF: {
            "pattern": r"(localhost|127\.0\.0\.1|10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.)",
            "action": "block",
            "description": "Block private IP ranges"
        },
        AttackVectorType.XXE: {
            "pattern": r"(<!ENTITY|<!DOCTYPE|\bSYSTEM\b)",
            "action": "block",
            "description": "Block XXE entity declarations"
        },
        AttackVectorType.FILE_UPLOAD: {
            "pattern": r"\.(php|jsp|asp|aspx|sh|bash|exe)$",
            "action": "block",
            "description": "Block dangerous file extensions"
        },
    }
    
    def __init__(
        self,
        rte_url: str = "http://rte-service:8002",
        timeout: int = 10,
        max_retries: int = 3
    ):
        """
        Initialize Coagulation client.
        
        Args:
            rte_url: RTE Service base URL
            timeout: Request timeout in seconds
            max_retries: Max retry attempts for failed requests
        """
        self.rte_url = rte_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        
        logger.info(f"Initialized CoagulationClient for {self.rte_url}")
    
    async def create_temporary_rule(
        self,
        apv_id: str,
        cve_id: str,
        attack_vector: AttackVectorType,
        duration: timedelta = timedelta(hours=24),
        custom_pattern: Optional[str] = None
    ) -> CoagulationRule:
        """
        Create temporary WAF rule.
        
        Args:
            apv_id: APV identifier
            cve_id: CVE identifier
            attack_vector: Attack vector type
            duration: Rule TTL (default 24h)
            custom_pattern: Optional custom pattern (overrides template)
        
        Returns:
            CoagulationRule with rule_id
        
        Raises:
            CoagulationError: If rule creation fails
        """
        logger.info(
            f"Creating temporary WAF rule for {cve_id} ({attack_vector.value})"
        )
        
        # Get rule template
        template = self.RULE_TEMPLATES.get(attack_vector)
        if not template and not custom_pattern:
            raise CoagulationError(
                f"No template for {attack_vector} and no custom pattern provided"
            )
        
        # Build rule payload
        pattern = custom_pattern or template["pattern"]
        action = template["action"] if template else "block"
        ttl_seconds = int(duration.total_seconds())
        
        payload = {
            "pattern": pattern,
            "action": action,
            "ttl_seconds": ttl_seconds,
            "source": "maximus_eureka",
            "metadata": {
                "apv_id": apv_id,
                "cve_id": cve_id,
                "attack_vector": attack_vector.value,
                "created_by": "coagulation_client"
            }
        }
        
        # Call RTE API
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.rte_url}/api/v1/rules",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
            
            # Build CoagulationRule
            now = datetime.now()
            rule = CoagulationRule(
                rule_id=data["rule_id"],
                apv_id=apv_id,
                cve_id=cve_id,
                attack_vector=attack_vector,
                pattern=pattern,
                action=action,
                ttl_seconds=ttl_seconds,
                created_at=now,
                expires_at=now + duration,
                active=True
            )
            
            logger.info(
                f"Created WAF rule {rule.rule_id}, expires {rule.expires_at}"
            )
            
            return rule
            
        except httpx.HTTPStatusError as e:
            logger.error(f"RTE API error: {e.response.status_code} - {e.response.text}")
            raise CoagulationError(f"Failed to create rule: {e}") from e
        except Exception as e:
            logger.error(f"Failed to create WAF rule: {e}", exc_info=True)
            raise CoagulationError(f"Rule creation failed: {e}") from e
    
    async def expire_rule(self, rule_id: str) -> bool:
        """
        Manually expire a rule (e.g., after PR merge).
        
        Args:
            rule_id: Rule identifier
        
        Returns:
            True if rule expired successfully
        
        Raises:
            CoagulationError: If expiration fails
        """
        logger.info(f"Expiring WAF rule {rule_id}")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(
                    f"{self.rte_url}/api/v1/rules/{rule_id}"
                )
                response.raise_for_status()
            
            logger.info(f"Rule {rule_id} expired")
            return True
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Rule {rule_id} not found (already expired?)")
                return False
            logger.error(f"Failed to expire rule: {e}")
            raise CoagulationError(f"Expiration failed: {e}") from e
        except Exception as e:
            logger.error(f"Expire rule error: {e}", exc_info=True)
            raise CoagulationError(f"Expiration failed: {e}") from e
    
    async def get_rule_status(self, rule_id: str) -> Dict:
        """
        Get rule status and effectiveness metrics.
        
        Args:
            rule_id: Rule identifier
        
        Returns:
            Dictionary with status, blocks_count, expires_at
        
        Raises:
            CoagulationError: If status check fails
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.rte_url}/api/v1/rules/{rule_id}"
                )
                response.raise_for_status()
                return response.json()
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise CoagulationError(f"Rule {rule_id} not found")
            raise CoagulationError(f"Status check failed: {e}") from e
        except Exception as e:
            raise CoagulationError(f"Status check failed: {e}") from e
    
    async def list_active_rules(
        self,
        apv_id: Optional[str] = None
    ) -> List[Dict]:
        """
        List active WAF rules.
        
        Args:
            apv_id: Optional filter by APV
        
        Returns:
            List of active rules
        """
        try:
            params = {}
            if apv_id:
                params["apv_id"] = apv_id
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.rte_url}/api/v1/rules",
                    params=params
                )
                response.raise_for_status()
                return response.json()["rules"]
            
        except Exception as e:
            logger.error(f"Failed to list rules: {e}")
            raise CoagulationError(f"List rules failed: {e}") from e
    
    async def health_check(self) -> bool:
        """
        Check if RTE Service is healthy.
        
        Returns:
            True if service is healthy
        """
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.rte_url}/health")
                return response.status_code == 200
        except Exception:
            return False
    
    @staticmethod
    def detect_attack_vector_from_cwe(cwe_id: str) -> AttackVectorType:
        """
        Detect attack vector type from CWE ID.
        
        Args:
            cwe_id: CWE identifier (e.g., "CWE-89")
        
        Returns:
            AttackVectorType (best guess)
        """
        # CWE → Attack Vector mapping
        mapping = {
            "CWE-89": AttackVectorType.SQL_INJECTION,
            "CWE-79": AttackVectorType.XSS,
            "CWE-78": AttackVectorType.COMMAND_INJECTION,
            "CWE-77": AttackVectorType.COMMAND_INJECTION,
            "CWE-22": AttackVectorType.PATH_TRAVERSAL,
            "CWE-918": AttackVectorType.SSRF,
            "CWE-611": AttackVectorType.XXE,
            "CWE-352": AttackVectorType.CSRF,
            "CWE-434": AttackVectorType.FILE_UPLOAD,
            "CWE-287": AttackVectorType.AUTHENTICATION_BYPASS,
            "CWE-306": AttackVectorType.AUTHENTICATION_BYPASS,
        }
        
        return mapping.get(cwe_id, AttackVectorType.GENERIC)


class CoagulationError(Exception):
    """Raised when coagulation operations fail"""
    pass


# Convenience function
async def create_waf_rule_for_apv(
    apv: "APV",  # Type hint as string to avoid circular import
    rte_url: str = "http://rte-service:8002",
    duration: timedelta = timedelta(hours=24)
) -> CoagulationRule:
    """
    Quick function to create WAF rule from APV.
    
    Args:
        apv: APV object (from Oráculo)
        rte_url: RTE Service URL
        duration: Rule TTL
    
    Returns:
        CoagulationRule
    
    Example:
        >>> rule = await create_waf_rule_for_apv(apv)
        >>> print(f"Protection active until {rule.expires_at}")
    """
    client = CoagulationClient(rte_url)
    
    # Detect attack vector from CWE
    attack_vector = CoagulationClient.detect_attack_vector_from_cwe(
        apv.cwe_ids[0] if apv.cwe_ids else "CWE-0"
    )
    
    return await client.create_temporary_rule(
        apv_id=apv.apv_id,
        cve_id=apv.cve_id,
        attack_vector=attack_vector,
        duration=duration
    )
