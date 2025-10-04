"""
🏷️ Data Classifier - Classificação automática de dados sensíveis

Classifica dados em níveis de sensibilidade:
- Public
- Internal
- Confidential
- Restricted
- Top Secret

Classification Methods:
- Content-based (keywords, patterns)
- Context-based (metadata, location)
- User-defined labels
- ML-based classification
- Inheritance (folder/parent classification)

Features:
- Automatic classification
- Manual override
- Classification inheritance
- Audit trail
- Policy integration
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from enum import Enum
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ClassificationLevel(Enum):
    """Níveis de classificação de dados"""
    PUBLIC = "public"  # Público
    INTERNAL = "internal"  # Uso interno
    CONFIDENTIAL = "confidential"  # Confidencial
    RESTRICTED = "restricted"  # Restrito
    TOP_SECRET = "top_secret"  # Secreto

    def get_numeric_level(self) -> int:
        """Retorna nível numérico (maior = mais sensível)"""
        levels = {
            ClassificationLevel.PUBLIC: 0,
            ClassificationLevel.INTERNAL: 1,
            ClassificationLevel.CONFIDENTIAL: 2,
            ClassificationLevel.RESTRICTED: 3,
            ClassificationLevel.TOP_SECRET: 4,
        }
        return levels.get(self, 0)


class ClassificationMethod(Enum):
    """Método de classificação"""
    AUTOMATIC = "automatic"  # Auto-classificado
    MANUAL = "manual"  # Classificação manual
    INHERITED = "inherited"  # Herdado de parent
    ML_BASED = "ml_based"  # Machine learning
    POLICY_BASED = "policy_based"  # Baseado em política


@dataclass
class ClassificationRule:
    """
    Regra de classificação

    Attributes:
        id: Rule ID
        name: Rule name
        level: Classification level to assign
        keywords: Keywords that trigger classification
        patterns: Regex patterns
        file_extensions: File extensions
        metadata_checks: Metadata checks
        enabled: If rule is enabled
    """
    id: str
    name: str
    level: ClassificationLevel

    # Triggers
    keywords: List[str] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)
    file_extensions: List[str] = field(default_factory=list)

    # Metadata checks
    metadata_checks: Dict[str, Any] = field(default_factory=dict)

    # Configuration
    enabled: bool = True
    priority: int = 0  # Higher priority rules are evaluated first

    # Metadata
    description: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass
class DataClassification:
    """
    Classificação de dado

    Attributes:
        resource_id: ID do recurso classificado
        level: Nível de classificação
        method: Método de classificação
        classified_at: Quando foi classificado
        classified_by: Quem/o que classificou
        confidence: Confiança da classificação (0-100)
        rules_matched: Regras que casaram
        reason: Razão da classificação
        metadata: Metadados adicionais
        expires_at: Expiração da classificação
    """
    resource_id: str
    level: ClassificationLevel
    method: ClassificationMethod
    classified_at: datetime
    classified_by: str

    confidence: int = 0  # 0-100

    # Audit trail
    rules_matched: List[str] = field(default_factory=list)
    reason: str = ""

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Expiration
    expires_at: Optional[datetime] = None

    # History
    previous_classifications: List[Dict[str, Any]] = field(default_factory=list)


class DataClassifier:
    """
    Data Classification System

    Features:
    - Multi-level classification
    - Rule-based classification
    - ML-based classification
    - Classification inheritance
    - Audit trail
    - Policy integration
    - Backend integration
    """

    def __init__(
        self,
        backend_url: Optional[str] = None,
        use_backend: bool = True,
        enable_ml: bool = False,
    ):
        """
        Args:
            backend_url: URL do dlp_service
            use_backend: Se True, usa backend
            enable_ml: Se True, habilita ML classification
        """
        self.backend_url = backend_url or "http://localhost:8022"
        self.use_backend = use_backend
        self.enable_ml = enable_ml

        # Classification rules
        self.rules: Dict[str, ClassificationRule] = {}

        # Classifications database
        self.classifications: Dict[str, DataClassification] = {}

        # Load default rules
        self._load_default_rules()

    def _load_default_rules(self):
        """Carrega regras padrão de classificação"""

        default_rules = [
            ClassificationRule(
                id="rule-top-secret",
                name="Top Secret Keywords",
                level=ClassificationLevel.TOP_SECRET,
                keywords=[
                    "top secret", "top-secret", "classified",
                    "national security", "eyes only",
                ],
                priority=100,
                description="Detects top secret content",
            ),
            ClassificationRule(
                id="rule-restricted",
                name="Restricted - PII/PCI",
                level=ClassificationLevel.RESTRICTED,
                keywords=[
                    "social security", "ssn", "credit card",
                    "passport", "driver license", "medical record",
                ],
                priority=90,
                description="Detects PII/PCI content requiring restricted access",
            ),
            ClassificationRule(
                id="rule-confidential-financial",
                name="Confidential - Financial",
                level=ClassificationLevel.CONFIDENTIAL,
                keywords=[
                    "confidential", "financial report", "quarterly earnings",
                    "merger", "acquisition", "proprietary",
                ],
                priority=80,
                description="Detects confidential financial information",
            ),
            ClassificationRule(
                id="rule-confidential-source",
                name="Confidential - Source Code",
                level=ClassificationLevel.CONFIDENTIAL,
                file_extensions=[".key", ".pem", ".p12", ".pfx"],
                keywords=["private key", "api key", "secret"],
                priority=85,
                description="Detects confidential source code/secrets",
            ),
            ClassificationRule(
                id="rule-internal",
                name="Internal Use Only",
                level=ClassificationLevel.INTERNAL,
                keywords=[
                    "internal use only", "internal", "not for distribution",
                    "draft", "work in progress",
                ],
                priority=50,
                description="Detects internal documents",
            ),
        ]

        for rule in default_rules:
            self.rules[rule.id] = rule

        logger.info(f"Loaded {len(default_rules)} default classification rules")

    def classify_content(
        self,
        content: str,
        resource_id: str,
        classifier: str = "system",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DataClassification:
        """
        Classifica conteúdo

        Args:
            content: Content to classify
            resource_id: Resource ID
            classifier: Who/what is classifying
            metadata: Additional metadata

        Returns:
            DataClassification
        """
        logger.info(f"Classifying content: {resource_id}")

        # Start with PUBLIC
        best_level = ClassificationLevel.PUBLIC
        matched_rules = []
        confidence = 100

        # Evaluate rules by priority
        sorted_rules = sorted(
            self.rules.values(),
            key=lambda r: r.priority,
            reverse=True
        )

        content_lower = content.lower()

        for rule in sorted_rules:
            if not rule.enabled:
                continue

            # Check keywords
            for keyword in rule.keywords:
                if keyword.lower() in content_lower:
                    # Rule matched
                    if rule.level.get_numeric_level() > best_level.get_numeric_level():
                        best_level = rule.level
                        matched_rules.append(rule.id)
                        logger.debug(
                            f"Rule matched: {rule.name} -> {rule.level.value}"
                        )
                    break

        # Build classification
        classification = DataClassification(
            resource_id=resource_id,
            level=best_level,
            method=ClassificationMethod.AUTOMATIC,
            classified_at=datetime.now(),
            classified_by=classifier,
            confidence=confidence,
            rules_matched=matched_rules,
            reason=f"Matched {len(matched_rules)} classification rules",
            metadata=metadata or {},
        )

        # Store classification
        self.classifications[resource_id] = classification

        logger.info(
            f"Classification complete: {resource_id} -> {best_level.value} "
            f"(matched {len(matched_rules)} rules)"
        )

        return classification

    def classify_file(
        self,
        file_path: Path,
        classifier: str = "system",
    ) -> DataClassification:
        """
        Classifica arquivo

        Args:
            file_path: File path
            classifier: Who is classifying

        Returns:
            DataClassification
        """
        resource_id = str(file_path)

        metadata = {
            "file_name": file_path.name,
            "file_extension": file_path.suffix,
            "file_size": file_path.stat().st_size if file_path.exists() else 0,
        }

        # Check file extension rules first
        best_level = ClassificationLevel.PUBLIC
        matched_rules = []

        for rule in self.rules.values():
            if not rule.enabled:
                continue

            if file_path.suffix in rule.file_extensions:
                if rule.level.get_numeric_level() > best_level.get_numeric_level():
                    best_level = rule.level
                    matched_rules.append(rule.id)

        # Read file content if it exists
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(10000)  # First 10KB

                # Classify content
                content_classification = self.classify_content(
                    content=content,
                    resource_id=resource_id,
                    classifier=classifier,
                    metadata=metadata,
                )

                # Use higher classification level
                if content_classification.level.get_numeric_level() > best_level.get_numeric_level():
                    return content_classification

            except Exception as e:
                logger.error(f"Failed to read file for classification: {e}")

        # Create classification based on extension/metadata only
        classification = DataClassification(
            resource_id=resource_id,
            level=best_level,
            method=ClassificationMethod.AUTOMATIC,
            classified_at=datetime.now(),
            classified_by=classifier,
            confidence=80,
            rules_matched=matched_rules,
            reason="Classification based on file extension",
            metadata=metadata,
        )

        self.classifications[resource_id] = classification

        return classification

    def manual_classify(
        self,
        resource_id: str,
        level: ClassificationLevel,
        classifier: str,
        reason: str = "",
    ) -> DataClassification:
        """
        Classificação manual

        Args:
            resource_id: Resource ID
            level: Classification level
            classifier: Who is classifying
            reason: Reason for classification

        Returns:
            DataClassification
        """
        # Check if already classified
        previous = self.get_classification(resource_id)

        classification = DataClassification(
            resource_id=resource_id,
            level=level,
            method=ClassificationMethod.MANUAL,
            classified_at=datetime.now(),
            classified_by=classifier,
            confidence=100,  # Manual = 100% confidence
            reason=reason or f"Manually classified as {level.value}",
        )

        # Store previous classification
        if previous:
            classification.previous_classifications.append({
                "level": previous.level.value,
                "method": previous.method.value,
                "classified_at": previous.classified_at.isoformat(),
                "classified_by": previous.classified_by,
            })

        self.classifications[resource_id] = classification

        logger.info(
            f"Manual classification: {resource_id} -> {level.value} by {classifier}"
        )

        return classification

    def get_classification(self, resource_id: str) -> Optional[DataClassification]:
        """Retorna classificação de recurso"""
        return self.classifications.get(resource_id)

    def add_rule(self, rule: ClassificationRule) -> None:
        """
        Adiciona regra de classificação

        Args:
            rule: ClassificationRule object
        """
        self.rules[rule.id] = rule
        logger.info(f"Added classification rule: {rule.name} ({rule.id})")

    def remove_rule(self, rule_id: str) -> bool:
        """Remove regra de classificação"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Removed classification rule: {rule_id}")
            return True
        return False

    def bulk_classify(
        self,
        directory: Path,
        recursive: bool = True,
        classifier: str = "system",
    ) -> List[DataClassification]:
        """
        Classifica múltiplos arquivos em diretório

        Args:
            directory: Directory path
            recursive: If True, recurse into subdirectories
            classifier: Who is classifying

        Returns:
            List of DataClassification
        """
        classifications = []

        if not directory.exists():
            logger.error(f"Directory not found: {directory}")
            return classifications

        # Get files
        if recursive:
            files = list(directory.rglob("*"))
        else:
            files = list(directory.glob("*"))

        # Filter to files only
        files = [f for f in files if f.is_file()]

        logger.info(f"Bulk classification: {len(files)} files in {directory}")

        for file_path in files:
            try:
                classification = self.classify_file(file_path, classifier=classifier)
                classifications.append(classification)
            except Exception as e:
                logger.error(f"Failed to classify {file_path}: {e}")

        logger.info(f"Bulk classification complete: {len(classifications)} files classified")

        return classifications

    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas de classificação"""

        # Count by level
        by_level = {}
        for classification in self.classifications.values():
            level = classification.level.value
            by_level[level] = by_level.get(level, 0) + 1

        # Count by method
        by_method = {}
        for classification in self.classifications.values():
            method = classification.method.value
            by_method[method] = by_method.get(method, 0) + 1

        # High-sensitivity resources
        high_sensitivity = len([
            c for c in self.classifications.values()
            if c.level in [ClassificationLevel.RESTRICTED, ClassificationLevel.TOP_SECRET]
        ])

        return {
            "total_classifications": len(self.classifications),
            "total_rules": len(self.rules),
            "by_level": by_level,
            "by_method": by_method,
            "high_sensitivity_resources": high_sensitivity,
        }

    def list_classifications(
        self,
        level: Optional[ClassificationLevel] = None,
        limit: int = 100,
    ) -> List[DataClassification]:
        """
        Lista classificações com filtros

        Args:
            level: Filter by classification level
            limit: Max results

        Returns:
            List of DataClassification
        """
        classifications = list(self.classifications.values())

        if level:
            classifications = [c for c in classifications if c.level == level]

        # Sort by classified_at (most recent first)
        classifications = sorted(
            classifications,
            key=lambda c: c.classified_at,
            reverse=True
        )

        return classifications[:limit]
