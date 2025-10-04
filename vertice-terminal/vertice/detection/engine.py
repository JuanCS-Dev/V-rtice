"""
🔍 Detection Engine - Orquestra detecção de ameaças

Pipeline:
1. Recebe eventos (file scan, log entry, network traffic)
2. Aplica regras (YARA, Sigma)
3. Gera detecções
4. Triggera policies se configurado
5. Cria alertas
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DetectionSeverity(Enum):
    """Severidade da detecção"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DetectionType(Enum):
    """Tipo de detecção"""
    YARA = "yara"  # Malware signature
    SIGMA = "sigma"  # Log pattern
    BEHAVIORAL = "behavioral"  # Comportamento suspeito
    IOC = "ioc"  # Indicator of Compromise
    CUSTOM = "custom"  # Custom rule


@dataclass
class Detection:
    """
    Detecção de ameaça
    """
    id: str
    rule_name: str
    detection_type: DetectionType
    severity: DetectionSeverity
    timestamp: datetime
    source: str  # Endpoint ID, log source, etc
    description: str

    # Dados específicos da detecção
    matched_data: Dict[str, Any] = field(default_factory=dict)

    # Contexto adicional
    iocs: List[str] = field(default_factory=list)  # IPs, hashes, domains
    mitre_tactics: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    # Metadados
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Se foi auto-respondida
    auto_responded: bool = False
    response_actions: List[str] = field(default_factory=list)


@dataclass
class DetectionRule:
    """
    Regra de detecção genérica
    """
    name: str
    rule_type: DetectionType
    severity: DetectionSeverity
    enabled: bool
    rule_content: str  # YARA, Sigma YAML, etc
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DetectionEngine:
    """
    Engine principal de detecção

    Features:
    - Carrega regras YARA/Sigma
    - Escaneia eventos em tempo real
    - Integra com PolicyEngine para auto-response
    - Gerencia alertas via AlertManager
    """

    def __init__(
        self,
        auto_response: bool = False,
        policy_engine: Optional[Any] = None,
        alert_manager: Optional[Any] = None,
    ):
        """
        Args:
            auto_response: Se True, triggera policies automaticamente
            policy_engine: PolicyEngine para auto-response
            alert_manager: AlertManager para criar alertas
        """
        self.auto_response = auto_response
        self.policy_engine = policy_engine
        self.alert_manager = alert_manager

        # Regras carregadas
        self.rules: Dict[str, DetectionRule] = {}

        # Scanners especializados
        self.yara_scanner: Optional[Any] = None
        self.sigma_parser: Optional[Any] = None

        # Detecções recentes
        self.detections: List[Detection] = []

        # Callbacks para detecções
        self.detection_callbacks: List[Callable[[Detection], None]] = []

    def load_yara_rules(self, rules_path: Path) -> int:
        """
        Carrega regras YARA de arquivo ou diretório

        Args:
            rules_path: Path para .yar/.yara ou diretório

        Returns:
            Número de regras carregadas
        """
        from .yara_scanner import YARAScanner

        if self.yara_scanner is None:
            self.yara_scanner = YARAScanner()

        count = self.yara_scanner.load_rules(rules_path)
        logger.info(f"Loaded {count} YARA rules from {rules_path}")

        return count

    def load_sigma_rules(self, rules_path: Path) -> int:
        """
        Carrega regras Sigma de arquivo ou diretório

        Args:
            rules_path: Path para .yml/.yaml ou diretório

        Returns:
            Número de regras carregadas
        """
        from .sigma_parser import SigmaParser

        if self.sigma_parser is None:
            self.sigma_parser = SigmaParser()

        count = 0

        if rules_path.is_file():
            self.sigma_parser.load_rule(rules_path)
            count = 1
        else:
            # Diretório
            for rule_file in rules_path.glob("**/*.yml"):
                try:
                    self.sigma_parser.load_rule(rule_file)
                    count += 1
                except Exception as e:
                    logger.error(f"Failed to load Sigma rule {rule_file}: {e}")

        logger.info(f"Loaded {count} Sigma rules from {rules_path}")
        return count

    def scan_file(self, file_path: Path, endpoint_id: str = "local") -> List[Detection]:
        """
        Escaneia arquivo com regras YARA

        Args:
            file_path: Path do arquivo
            endpoint_id: ID do endpoint

        Returns:
            Lista de detecções
        """
        if not self.yara_scanner:
            logger.warning("No YARA scanner loaded")
            return []

        matches = self.yara_scanner.scan_file(file_path)

        detections = []
        for match in matches:
            detection = Detection(
                id=f"yara_{match.rule_name}_{datetime.now().timestamp()}",
                rule_name=match.rule_name,
                detection_type=DetectionType.YARA,
                severity=self._map_yara_severity(match),
                timestamp=datetime.now(),
                source=endpoint_id,
                description=f"YARA rule '{match.rule_name}' matched file {file_path}",
                matched_data={
                    "file_path": str(file_path),
                    "matches": match.strings,
                },
                tags=match.tags,
                metadata=match.metadata,
            )

            detections.append(detection)
            self._handle_detection(detection)

        return detections

    def analyze_log(
        self,
        log_entry: Dict[str, Any],
        source: str = "unknown"
    ) -> List[Detection]:
        """
        Analisa log entry com regras Sigma

        Args:
            log_entry: Dicionário com campos do log
            source: Source do log

        Returns:
            Lista de detecções
        """
        if not self.sigma_parser:
            logger.warning("No Sigma parser loaded")
            return []

        matches = self.sigma_parser.match(log_entry)

        detections = []
        for rule in matches:
            detection = Detection(
                id=f"sigma_{rule.name}_{datetime.now().timestamp()}",
                rule_name=rule.name,
                detection_type=DetectionType.SIGMA,
                severity=DetectionSeverity[rule.level.upper()],
                timestamp=datetime.now(),
                source=source,
                description=rule.description,
                matched_data=log_entry,
                tags=rule.tags,
                mitre_tactics=[tag for tag in rule.tags if tag.startswith("attack.t")],
            )

            detections.append(detection)
            self._handle_detection(detection)

        return detections

    def _handle_detection(self, detection: Detection) -> None:
        """
        Processa detecção:
        1. Adiciona ao histórico
        2. Chama callbacks
        3. Cria alerta
        4. Triggera policy se auto-response

        Args:
            detection: Detection object
        """
        # Adiciona ao histórico
        self.detections.append(detection)

        # Callbacks
        for callback in self.detection_callbacks:
            try:
                callback(detection)
            except Exception as e:
                logger.error(f"Detection callback failed: {e}")

        # Cria alerta
        if self.alert_manager:
            try:
                from .alert_manager import Alert, AlertStatus

                alert = Alert(
                    id=f"alert_{detection.id}",
                    title=f"{detection.rule_name} detected",
                    description=detection.description,
                    severity=detection.severity.value,
                    status=AlertStatus.NEW,
                    source=detection.source,
                    detection_ids=[detection.id],
                    tags=detection.tags,
                    iocs=detection.iocs,
                )

                self.alert_manager.create_alert(alert)

            except Exception as e:
                logger.error(f"Failed to create alert: {e}")

        # Auto-response via PolicyEngine
        if self.auto_response and self.policy_engine:
            try:
                # Converte detection para event
                event_name = f"{detection.detection_type.value}_detected"
                event_data = {
                    "detection": {
                        "rule_name": detection.rule_name,
                        "severity": detection.severity.value,
                        "source": detection.source,
                    },
                    **detection.matched_data,
                }

                executions = self.policy_engine.trigger_event(event_name, event_data)

                if executions:
                    detection.auto_responded = True
                    detection.response_actions = [
                        ex.policy_name for ex in executions
                    ]

                    logger.info(
                        f"Auto-response triggered: {len(executions)} policies executed"
                    )

            except Exception as e:
                logger.error(f"Auto-response failed: {e}")

    def _map_yara_severity(self, match: Any) -> DetectionSeverity:
        """
        Mapeia severidade de YARA match

        Args:
            match: YARAMatch object

        Returns:
            DetectionSeverity
        """
        # Tenta pegar do metadata da regra
        severity_str = match.metadata.get("severity", "medium")

        try:
            return DetectionSeverity[severity_str.upper()]
        except KeyError:
            return DetectionSeverity.MEDIUM

    def register_callback(self, callback: Callable[[Detection], None]) -> None:
        """
        Registra callback para notificação de detecções

        Args:
            callback: Função que recebe Detection
        """
        self.detection_callbacks.append(callback)

    def get_detections(
        self,
        severity: Optional[DetectionSeverity] = None,
        detection_type: Optional[DetectionType] = None,
        source: Optional[str] = None,
        limit: int = 100,
    ) -> List[Detection]:
        """
        Retorna detecções filtradas

        Args:
            severity: Filtrar por severidade
            detection_type: Filtrar por tipo
            source: Filtrar por source
            limit: Máximo de detecções

        Returns:
            Lista de Detection objects
        """
        detections = self.detections

        if severity:
            detections = [d for d in detections if d.severity == severity]

        if detection_type:
            detections = [d for d in detections if d.detection_type == detection_type]

        if source:
            detections = [d for d in detections if d.source == source]

        # Mais recentes primeiro
        detections = sorted(detections, key=lambda d: d.timestamp, reverse=True)

        return detections[:limit]

    def clear_detections(self) -> None:
        """Limpa histórico de detecções"""
        self.detections.clear()
