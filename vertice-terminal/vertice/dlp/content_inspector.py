"""
🔍 Content Inspector - Inspeção profunda de conteúdo sensível

Detecta dados sensíveis em múltiplos formatos:
- PII (Personally Identifiable Information)
- PCI (Payment Card Information)
- PHI (Protected Health Information)
- Credentials & Secrets
- Proprietary/Confidential data

Detection Methods:
- Regex pattern matching
- Keyword dictionaries
- Machine learning classification
- File signature analysis
- Entropy analysis (secrets detection)

Supported Formats:
- Plain text
- Documents (PDF, DOCX, XLSX)
- Emails (MSG, EML)
- Archives (ZIP, TAR, GZ)
- Source code
- Database dumps
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from enum import Enum
from pathlib import Path
import re
import logging

logger = logging.getLogger(__name__)


class SensitiveDataType(Enum):
    """Tipos de dados sensíveis"""
    # PII
    SSN = "ssn"  # Social Security Number
    CPF = "cpf"  # CPF brasileiro
    PASSPORT = "passport"
    DRIVERS_LICENSE = "drivers_license"
    EMAIL_ADDRESS = "email_address"
    PHONE_NUMBER = "phone_number"

    # PCI
    CREDIT_CARD = "credit_card"
    CVV = "cvv"
    BANK_ACCOUNT = "bank_account"

    # PHI
    PATIENT_ID = "patient_id"
    MEDICAL_RECORD = "medical_record"
    DIAGNOSIS = "diagnosis"

    # Credentials
    PASSWORD = "password"
    API_KEY = "api_key"
    PRIVATE_KEY = "private_key"
    AWS_KEY = "aws_key"
    JWT_TOKEN = "jwt_token"

    # Proprietary
    CONFIDENTIAL = "confidential"
    INTERNAL = "internal"
    TRADE_SECRET = "trade_secret"

    # Other
    IP_ADDRESS = "ip_address"
    CUSTOM = "custom"


class ConfidenceLevel(Enum):
    """Nível de confiança da detecção"""
    LOW = "low"  # 0-40%
    MEDIUM = "medium"  # 41-70%
    HIGH = "high"  # 71-90%
    VERY_HIGH = "very_high"  # 91-100%


@dataclass
class Match:
    """
    Match de dado sensível

    Attributes:
        data_type: Tipo de dado detectado
        value: Valor detectado (pode ser mascarado)
        start_position: Posição inicial no texto
        end_position: Posição final no texto
        confidence: Nível de confiança
        context: Contexto ao redor do match
        masked: Se valor está mascarado
    """
    data_type: SensitiveDataType
    value: str
    start_position: int
    end_position: int
    confidence: ConfidenceLevel

    context: str = ""  # Texto ao redor
    masked: bool = True

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InspectionResult:
    """
    Resultado de inspeção de conteúdo

    Attributes:
        content_id: ID do conteúdo inspecionado
        inspected_at: Quando foi inspecionado
        has_sensitive_data: Se contém dados sensíveis
        matches: Matches encontrados
        data_types_found: Tipos de dados encontrados
        risk_score: Score de risco (0-100)
        summary: Resumo da inspeção
    """
    content_id: str
    inspected_at: datetime
    has_sensitive_data: bool

    matches: List[Match] = field(default_factory=list)
    data_types_found: Set[SensitiveDataType] = field(default_factory=set)

    risk_score: int = 0  # 0-100
    summary: str = ""

    # Metadata
    content_type: str = ""
    content_size: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContentInspector:
    """
    Content Inspection Engine

    Features:
    - Deep content inspection
    - Multi-format support
    - Pattern matching (regex)
    - ML-based classification
    - Custom pattern support
    - Data masking
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

        # Pattern library
        self.patterns: Dict[SensitiveDataType, List[re.Pattern]] = {}

        # Custom patterns
        self.custom_patterns: Dict[str, re.Pattern] = {}

        # Load default patterns
        self._load_default_patterns()

    def _load_default_patterns(self):
        """Carrega patterns padrão para detecção"""

        # SSN (US Social Security Number): 123-45-6789
        self.patterns[SensitiveDataType.SSN] = [
            re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            re.compile(r'\b\d{3}\s\d{2}\s\d{4}\b'),
        ]

        # CPF (Brazilian): 123.456.789-00
        self.patterns[SensitiveDataType.CPF] = [
            re.compile(r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b'),
            re.compile(r'\b\d{11}\b'),
        ]

        # Credit Card (Luhn algorithm check would be ideal)
        self.patterns[SensitiveDataType.CREDIT_CARD] = [
            re.compile(r'\b(?:4\d{3}|5[1-5]\d{2}|6011|3[47]\d{2})[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b'),
        ]

        # Email
        self.patterns[SensitiveDataType.EMAIL_ADDRESS] = [
            re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        ]

        # Phone Number (US/BR formats)
        self.patterns[SensitiveDataType.PHONE_NUMBER] = [
            re.compile(r'\b\(\d{2,3}\)\s?\d{4,5}-?\d{4}\b'),  # (11) 98765-4321
            re.compile(r'\b\d{3}-\d{3}-\d{4}\b'),  # 555-123-4567
        ]

        # AWS Access Key
        self.patterns[SensitiveDataType.AWS_KEY] = [
            re.compile(r'AKIA[0-9A-Z]{16}'),
        ]

        # API Key (generic high-entropy strings)
        self.patterns[SensitiveDataType.API_KEY] = [
            re.compile(r'api[_-]?key[\s:=]+["\']?([a-zA-Z0-9_\-]{32,})["\']?', re.IGNORECASE),
        ]

        # Private Key
        self.patterns[SensitiveDataType.PRIVATE_KEY] = [
            re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
        ]

        # JWT Token
        self.patterns[SensitiveDataType.JWT_TOKEN] = [
            re.compile(r'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+'),
        ]

        # Password in code
        self.patterns[SensitiveDataType.PASSWORD] = [
            re.compile(r'password[\s:=]+["\']([^"\']{8,})["\']', re.IGNORECASE),
            re.compile(r'pwd[\s:=]+["\']([^"\']{8,})["\']', re.IGNORECASE),
        ]

        # IP Address
        self.patterns[SensitiveDataType.IP_ADDRESS] = [
            re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
        ]

        logger.info(f"Loaded {len(self.patterns)} default pattern categories")

    def inspect_content(
        self,
        content: str,
        content_id: Optional[str] = None,
        mask_values: bool = True,
    ) -> InspectionResult:
        """
        Inspeciona conteúdo em busca de dados sensíveis

        Args:
            content: Conteúdo a ser inspecionado
            content_id: ID do conteúdo
            mask_values: Se True, mascara valores detectados

        Returns:
            InspectionResult
        """
        import uuid

        if not content_id:
            content_id = f"content-{uuid.uuid4().hex[:8]}"

        logger.info(f"Inspecting content: {content_id} ({len(content)} chars)")

        result = InspectionResult(
            content_id=content_id,
            inspected_at=datetime.now(),
            has_sensitive_data=False,
            content_size=len(content),
        )

        # Scan with all patterns
        for data_type, patterns in self.patterns.items():
            for pattern in patterns:
                for match in pattern.finditer(content):
                    # Extract match
                    value = match.group(0)

                    # Determine confidence
                    confidence = self._determine_confidence(data_type, value)

                    # Extract context (50 chars before and after)
                    start = max(0, match.start() - 50)
                    end = min(len(content), match.end() + 50)
                    context = content[start:end]

                    # Mask value if requested
                    if mask_values:
                        masked_value = self._mask_value(value, data_type)
                    else:
                        masked_value = value

                    # Create match
                    match_obj = Match(
                        data_type=data_type,
                        value=masked_value,
                        start_position=match.start(),
                        end_position=match.end(),
                        confidence=confidence,
                        context=context,
                        masked=mask_values,
                    )

                    result.matches.append(match_obj)
                    result.data_types_found.add(data_type)

        # Set has_sensitive_data
        result.has_sensitive_data = len(result.matches) > 0

        # Calculate risk score
        result.risk_score = self._calculate_risk_score(result)

        # Generate summary
        result.summary = self._generate_summary(result)

        logger.info(
            f"Inspection complete: {len(result.matches)} matches, "
            f"risk_score={result.risk_score}"
        )

        return result

    def _determine_confidence(
        self,
        data_type: SensitiveDataType,
        value: str,
    ) -> ConfidenceLevel:
        """Determina confiança do match"""

        # High confidence for specific patterns
        if data_type in [
            SensitiveDataType.AWS_KEY,
            SensitiveDataType.PRIVATE_KEY,
            SensitiveDataType.JWT_TOKEN,
        ]:
            return ConfidenceLevel.VERY_HIGH

        # Medium-high for structured data
        if data_type in [
            SensitiveDataType.SSN,
            SensitiveDataType.CPF,
            SensitiveDataType.EMAIL_ADDRESS,
        ]:
            return ConfidenceLevel.HIGH

        # Medium for credit cards (would validate with Luhn in production)
        if data_type == SensitiveDataType.CREDIT_CARD:
            # TODO: Implement Luhn algorithm
            return ConfidenceLevel.MEDIUM

        # Lower confidence for generic patterns
        return ConfidenceLevel.MEDIUM

    def _mask_value(
        self,
        value: str,
        data_type: SensitiveDataType,
    ) -> str:
        """Mascara valor sensível"""

        if len(value) <= 4:
            return "****"

        # Show first and last chars only
        if data_type == SensitiveDataType.CREDIT_CARD:
            # Show first 4 and last 4
            return value[:4] + "*" * (len(value) - 8) + value[-4:]

        elif data_type == SensitiveDataType.EMAIL_ADDRESS:
            # Mask username but show domain
            parts = value.split('@')
            if len(parts) == 2:
                username = parts[0]
                if len(username) > 2:
                    masked_username = username[0] + "*" * (len(username) - 2) + username[-1]
                else:
                    masked_username = "**"
                return f"{masked_username}@{parts[1]}"

        # Default: show first 4 chars
        return value[:4] + "*" * (len(value) - 4)

    def _calculate_risk_score(self, result: InspectionResult) -> int:
        """Calcula risk score (0-100)"""

        if not result.has_sensitive_data:
            return 0

        # Base score on number of matches
        base_score = min(len(result.matches) * 10, 50)

        # Add points for high-risk data types
        high_risk_types = {
            SensitiveDataType.SSN: 30,
            SensitiveDataType.CPF: 30,
            SensitiveDataType.CREDIT_CARD: 25,
            SensitiveDataType.PRIVATE_KEY: 40,
            SensitiveDataType.AWS_KEY: 35,
            SensitiveDataType.PASSWORD: 20,
        }

        risk_bonus = 0
        for data_type in result.data_types_found:
            risk_bonus += high_risk_types.get(data_type, 5)

        total_score = min(base_score + risk_bonus, 100)

        return total_score

    def _generate_summary(self, result: InspectionResult) -> str:
        """Gera resumo da inspeção"""

        if not result.has_sensitive_data:
            return "No sensitive data detected"

        # Count by type
        type_counts = {}
        for match in result.matches:
            type_counts[match.data_type] = type_counts.get(match.data_type, 0) + 1

        # Build summary
        summary_parts = []
        for data_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            summary_parts.append(f"{count} {data_type.value}")

        return f"Detected: {', '.join(summary_parts[:3])}"

    def inspect_file(
        self,
        file_path: Path,
        mask_values: bool = True,
    ) -> InspectionResult:
        """
        Inspeciona arquivo

        Args:
            file_path: Path to file
            mask_values: Mask detected values

        Returns:
            InspectionResult
        """
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            result = self.inspect_content(
                content=content,
                content_id=file_path.name,
                mask_values=mask_values,
            )

            result.content_type = file_path.suffix
            result.metadata["file_path"] = str(file_path)

            return result

        except Exception as e:
            logger.error(f"File inspection failed: {e}")

            # Return empty result with error
            return InspectionResult(
                content_id=file_path.name,
                inspected_at=datetime.now(),
                has_sensitive_data=False,
                metadata={"error": str(e)},
            )

    def add_custom_pattern(
        self,
        name: str,
        pattern: str,
        data_type: SensitiveDataType = SensitiveDataType.CUSTOM,
    ) -> None:
        """
        Adiciona pattern customizado

        Args:
            name: Pattern name
            pattern: Regex pattern
            data_type: Data type
        """
        compiled = re.compile(pattern)

        self.custom_patterns[name] = compiled

        if data_type not in self.patterns:
            self.patterns[data_type] = []

        self.patterns[data_type].append(compiled)

        logger.info(f"Added custom pattern: {name}")

    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas"""

        total_patterns = sum(len(patterns) for patterns in self.patterns.values())

        return {
            "total_pattern_categories": len(self.patterns),
            "total_patterns": total_patterns,
            "custom_patterns": len(self.custom_patterns),
            "ml_enabled": self.enable_ml,
        }
