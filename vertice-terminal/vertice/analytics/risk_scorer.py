"""
⚖️ Risk Scoring Engine - Cálculo de risk score para assets e users

Integra com backend risk_analysis_service.

Calcula risk score baseado em:
- Vulnerabilidades conhecidas
- Detecções de malware/anomalias
- Behavioral analytics
- Threat intelligence
- Compliance violations
- Privilege level
- Data sensitivity

Score: 0-100 (0 = sem risco, 100 = risco crítico)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Nível de risco"""
    CRITICAL = "critical"  # 80-100
    HIGH = "high"  # 60-79
    MEDIUM = "medium"  # 40-59
    LOW = "low"  # 20-39
    MINIMAL = "minimal"  # 0-19


@dataclass
class RiskFactor:
    """
    Fator individual de risco
    """
    name: str
    category: str  # vulnerability, malware, behavioral, compliance, etc
    score_impact: float  # 0-100
    weight: float = 1.0  # 0.0-1.0

    description: str = ""
    detected_at: datetime = field(default_factory=datetime.now)

    # Evidence
    evidence: Dict[str, Any] = field(default_factory=dict)

    # Mitigation
    is_mitigated: bool = False
    mitigation_actions: List[str] = field(default_factory=list)


@dataclass
class RiskScore:
    """
    Risk score calculado para entity (user, endpoint, application)
    """
    entity_id: str
    entity_type: str  # user, endpoint, application, network_segment

    # Overall score
    total_score: float  # 0-100
    risk_level: RiskLevel

    # Score breakdown by category
    vulnerability_score: float = 0.0
    malware_score: float = 0.0
    behavioral_score: float = 0.0
    compliance_score: float = 0.0
    threat_intel_score: float = 0.0

    # Contributing factors
    risk_factors: List[RiskFactor] = field(default_factory=list)

    # Trending
    score_change_7d: float = 0.0  # Change in last 7 days
    score_change_30d: float = 0.0  # Change in last 30 days

    # Metadata
    calculated_at: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0  # 0.0-1.0


class RiskScorer:
    """
    Risk Scoring Engine

    Features:
    - Multi-factor risk calculation
    - Weighted scoring by category
    - Trend analysis
    - Backend integration for historical data
    """

    def __init__(
        self,
        backend_url: Optional[str] = None,
        use_backend: bool = True,
        # Weights for each category (sum should be 1.0)
        vulnerability_weight: float = 0.25,
        malware_weight: float = 0.30,
        behavioral_weight: float = 0.20,
        compliance_weight: float = 0.15,
        threat_intel_weight: float = 0.10,
    ):
        """
        Args:
            backend_url: URL do risk_analysis_service
            use_backend: Se True, usa backend
            vulnerability_weight: Peso de vulnerabilities no score
            malware_weight: Peso de malware detections
            behavioral_weight: Peso de anomalias comportamentais
            compliance_weight: Peso de compliance violations
            threat_intel_weight: Peso de threat intel indicators
        """
        self.backend_url = backend_url or "http://localhost:8008"
        self.use_backend = use_backend

        # Category weights
        self.weights = {
            "vulnerability": vulnerability_weight,
            "malware": malware_weight,
            "behavioral": behavioral_weight,
            "compliance": compliance_weight,
            "threat_intel": threat_intel_weight,
        }

        # Validate weights sum to 1.0
        total_weight = sum(self.weights.values())
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"Category weights sum to {total_weight}, normalizing...")
            # Normalize
            for k in self.weights:
                self.weights[k] /= total_weight

        # Risk scores cache
        self.risk_scores: Dict[str, RiskScore] = {}

    def calculate_risk_score(
        self,
        entity_id: str,
        entity_type: str,
        risk_factors: List[RiskFactor],
    ) -> RiskScore:
        """
        Calcula risk score baseado em fatores de risco

        Args:
            entity_id: Entity ID
            entity_type: Entity type
            risk_factors: Lista de RiskFactor

        Returns:
            RiskScore object
        """
        if self.use_backend:
            try:
                return self._calculate_risk_score_backend(entity_id, entity_type, risk_factors)
            except Exception as e:
                logger.warning(f"Backend scoring failed, falling back to local: {e}")

        # Fallback: local calculation
        return self._calculate_risk_score_local(entity_id, entity_type, risk_factors)

    def _calculate_risk_score_local(
        self,
        entity_id: str,
        entity_type: str,
        risk_factors: List[RiskFactor],
    ) -> RiskScore:
        """
        Calcula risk score localmente

        Args:
            entity_id: Entity ID
            entity_type: Entity type
            risk_factors: Risk factors

        Returns:
            RiskScore
        """
        # Initialize category scores
        category_scores = {
            "vulnerability": 0.0,
            "malware": 0.0,
            "behavioral": 0.0,
            "compliance": 0.0,
            "threat_intel": 0.0,
        }

        # Group factors by category
        for factor in risk_factors:
            if factor.category in category_scores:
                # Weighted impact
                weighted_impact = factor.score_impact * factor.weight

                # Use max impact for each category (worst case)
                category_scores[factor.category] = max(
                    category_scores[factor.category],
                    weighted_impact
                )

        # Calculate weighted total score
        total_score = sum(
            category_scores[cat] * self.weights[cat]
            for cat in category_scores
        )

        # Determine risk level
        if total_score >= 80:
            risk_level = RiskLevel.CRITICAL
        elif total_score >= 60:
            risk_level = RiskLevel.HIGH
        elif total_score >= 40:
            risk_level = RiskLevel.MEDIUM
        elif total_score >= 20:
            risk_level = RiskLevel.LOW
        else:
            risk_level = RiskLevel.MINIMAL

        risk_score = RiskScore(
            entity_id=entity_id,
            entity_type=entity_type,
            total_score=total_score,
            risk_level=risk_level,
            vulnerability_score=category_scores["vulnerability"],
            malware_score=category_scores["malware"],
            behavioral_score=category_scores["behavioral"],
            compliance_score=category_scores["compliance"],
            threat_intel_score=category_scores["threat_intel"],
            risk_factors=risk_factors,
        )

        # Cache score
        self.risk_scores[entity_id] = risk_score

        logger.info(
            f"Risk score calculated for {entity_id}: {total_score:.1f} ({risk_level.value})"
        )

        return risk_score

    def _calculate_risk_score_backend(
        self,
        entity_id: str,
        entity_type: str,
        risk_factors: List[RiskFactor],
    ) -> RiskScore:
        """
        Calcula via backend (com histórico e trending)

        Args:
            entity_id: Entity ID
            entity_type: Entity type
            risk_factors: Risk factors

        Returns:
            RiskScore from backend
        """
        import httpx

        try:
            # Serialize risk factors
            factors_data = [
                {
                    "name": f.name,
                    "category": f.category,
                    "score_impact": f.score_impact,
                    "weight": f.weight,
                    "description": f.description,
                    "evidence": f.evidence,
                }
                for f in risk_factors
            ]

            with httpx.Client(timeout=15.0) as client:
                response = client.post(
                    f"{self.backend_url}/api/risk/calculate",
                    json={
                        "entity_id": entity_id,
                        "entity_type": entity_type,
                        "risk_factors": factors_data,
                        "category_weights": self.weights,
                    }
                )
                response.raise_for_status()

                data = response.json()

                risk_score = RiskScore(
                    entity_id=entity_id,
                    entity_type=entity_type,
                    total_score=data.get("total_score", 0.0),
                    risk_level=RiskLevel(data.get("risk_level", "minimal")),
                    vulnerability_score=data.get("vulnerability_score", 0.0),
                    malware_score=data.get("malware_score", 0.0),
                    behavioral_score=data.get("behavioral_score", 0.0),
                    compliance_score=data.get("compliance_score", 0.0),
                    threat_intel_score=data.get("threat_intel_score", 0.0),
                    risk_factors=risk_factors,
                    score_change_7d=data.get("score_change_7d", 0.0),
                    score_change_30d=data.get("score_change_30d", 0.0),
                    confidence=data.get("confidence", 1.0),
                )

                self.risk_scores[entity_id] = risk_score

                return risk_score

        except Exception as e:
            logger.error(f"Backend risk calculation failed: {e}")
            raise

    def aggregate_risk_factors(
        self,
        entity_id: str,
        entity_type: str,
        # Data sources
        vulnerabilities: Optional[List[Dict[str, Any]]] = None,
        detections: Optional[List[Any]] = None,  # Detection objects
        anomalies: Optional[List[Any]] = None,  # Anomaly objects
        compliance_violations: Optional[List[Dict[str, Any]]] = None,
        threat_intel_matches: Optional[List[Any]] = None,  # IOC objects
    ) -> List[RiskFactor]:
        """
        Agrega fatores de risco de múltiplas fontes

        Args:
            entity_id: Entity ID
            entity_type: Entity type
            vulnerabilities: Lista de vulnerabilities
            detections: Lista de Detection objects
            anomalies: Lista de Anomaly objects
            compliance_violations: Lista de compliance violations
            threat_intel_matches: Lista de IOC matches

        Returns:
            Lista de RiskFactor
        """
        risk_factors = []

        # Process vulnerabilities
        if vulnerabilities:
            for vuln in vulnerabilities:
                severity = vuln.get("severity", "medium")

                # Map CVSS score to risk impact
                cvss_score = vuln.get("cvss_score", 5.0)
                impact = (cvss_score / 10.0) * 100  # 0-100

                factor = RiskFactor(
                    name=f"Vulnerability: {vuln.get('cve_id', 'Unknown')}",
                    category="vulnerability",
                    score_impact=impact,
                    weight=1.0,
                    description=vuln.get("description", ""),
                    evidence=vuln,
                )
                risk_factors.append(factor)

        # Process malware detections
        if detections:
            for detection in detections:
                severity_map = {
                    "critical": 100,
                    "high": 75,
                    "medium": 50,
                    "low": 25,
                    "info": 10,
                }

                impact = severity_map.get(detection.severity.value, 50)

                factor = RiskFactor(
                    name=f"Detection: {detection.rule_name}",
                    category="malware",
                    score_impact=impact,
                    weight=1.0,
                    description=detection.description,
                    evidence={
                        "detection_type": detection.detection_type.value,
                        "matched_data": detection.matched_data,
                    },
                )
                risk_factors.append(factor)

        # Process behavioral anomalies
        if anomalies:
            for anomaly in anomalies:
                # Impact baseado em deviation score
                impact = min(anomaly.deviation_score * 20, 100)  # Cap at 100

                severity_map = {
                    "critical": 1.2,
                    "high": 1.0,
                    "medium": 0.8,
                    "low": 0.6,
                }

                weight = severity_map.get(anomaly.severity, 0.8)

                factor = RiskFactor(
                    name=f"Anomaly: {anomaly.anomaly_type.value}",
                    category="behavioral",
                    score_impact=impact,
                    weight=weight,
                    description=anomaly.description,
                    evidence={
                        "observed_value": anomaly.observed_value,
                        "baseline_value": anomaly.baseline_value,
                        "deviation_score": anomaly.deviation_score,
                    },
                )
                risk_factors.append(factor)

        # Process compliance violations
        if compliance_violations:
            for violation in compliance_violations:
                severity_map = {
                    "critical": 90,
                    "high": 70,
                    "medium": 50,
                    "low": 30,
                }

                impact = severity_map.get(violation.get("severity", "medium"), 50)

                factor = RiskFactor(
                    name=f"Compliance: {violation.get('policy', 'Unknown')}",
                    category="compliance",
                    score_impact=impact,
                    weight=1.0,
                    description=violation.get("description", ""),
                    evidence=violation,
                )
                risk_factors.append(factor)

        # Process threat intel matches
        if threat_intel_matches:
            for ioc in threat_intel_matches:
                threat_level_map = {
                    "critical": 95,
                    "high": 80,
                    "medium": 60,
                    "low": 40,
                    "unknown": 30,
                }

                impact = threat_level_map.get(ioc.threat_level, 30)

                # Weight by confidence
                weight = ioc.confidence

                factor = RiskFactor(
                    name=f"Threat Intel: {ioc.ioc_type.value}",
                    category="threat_intel",
                    score_impact=impact,
                    weight=weight,
                    description=f"IOC match: {ioc.value}",
                    evidence={
                        "ioc_value": ioc.value,
                        "threat_actors": ioc.threat_actors,
                        "campaigns": ioc.campaigns,
                        "sources": ioc.sources,
                    },
                )
                risk_factors.append(factor)

        return risk_factors

    def get_risk_score(self, entity_id: str) -> Optional[RiskScore]:
        """
        Retorna risk score de entity

        Args:
            entity_id: Entity ID

        Returns:
            RiskScore ou None
        """
        # Check cache
        if entity_id in self.risk_scores:
            return self.risk_scores[entity_id]

        # Try backend
        if self.use_backend:
            try:
                return self._get_risk_score_backend(entity_id)
            except Exception as e:
                logger.warning(f"Backend score retrieval failed: {e}")

        return None

    def _get_risk_score_backend(self, entity_id: str) -> Optional[RiskScore]:
        """
        Busca risk score no backend

        Args:
            entity_id: Entity ID

        Returns:
            RiskScore ou None
        """
        import httpx

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    f"{self.backend_url}/api/risk/scores/{entity_id}"
                )

                if response.status_code == 404:
                    return None

                response.raise_for_status()

                data = response.json()

                # Parse response to RiskScore
                # TODO: Full implementation

                return None  # Placeholder

        except Exception as e:
            logger.error(f"Backend risk score retrieval failed: {e}")
            raise

    def get_high_risk_entities(
        self,
        entity_type: Optional[str] = None,
        min_risk_level: RiskLevel = RiskLevel.HIGH,
        limit: int = 100,
    ) -> List[RiskScore]:
        """
        Retorna entities com alto risco

        Args:
            entity_type: Filter by type
            min_risk_level: Minimum risk level
            limit: Max entities

        Returns:
            List of RiskScore
        """
        scores = list(self.risk_scores.values())

        if entity_type:
            scores = [s for s in scores if s.entity_type == entity_type]

        # Filter by risk level
        level_order = {
            RiskLevel.CRITICAL: 5,
            RiskLevel.HIGH: 4,
            RiskLevel.MEDIUM: 3,
            RiskLevel.LOW: 2,
            RiskLevel.MINIMAL: 1,
        }

        min_level_value = level_order[min_risk_level]
        scores = [s for s in scores if level_order[s.risk_level] >= min_level_value]

        # Sort by score (highest first)
        scores = sorted(scores, key=lambda s: s.total_score, reverse=True)

        return scores[:limit]
