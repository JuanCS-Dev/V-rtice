"""Verdict Synthesizer - Camada 3 do Filtro de Narrativas.

Responsável por:
- Sintetizar veredictos a partir de padrões estratégicos
- Atribuir severity automático (CRITICAL, HIGH, MEDIUM, LOW)
- Gerar recomendações de ações (C2L commands)
- Color mapping por severity para UI
"""

from datetime import datetime

from narrative_filter_service.config import settings
from narrative_filter_service.models import Severity, StrategicPattern, Verdict, VerdictCategory, VerdictStatus


class VerdictSynthesizer:
    """Sintetizador de veredictos a partir de padrões estratégicos."""

    def __init__(self) -> None:
        """Initialize verdict synthesizer."""
        self.verdict_count = 0

    def determine_severity(self, pattern: StrategicPattern) -> Severity:
        """Determine severity level based on pattern scores.

        Args:
            pattern: Strategic pattern to analyze

        Returns:
            Severity level
        """
        # Extract relevant scores
        deception = pattern.deception_score or 0.0
        inconsistency = pattern.inconsistency_score or 0.0
        mutual_info = pattern.mutual_information or 0.0

        # Critical: High deception + inconsistency
        if deception >= settings.critical_deception or inconsistency >= settings.critical_inconsistency:
            return Severity.CRITICAL

        # High: Moderate deception/inconsistency or strong alliance with high MI
        if deception >= settings.high_deception or inconsistency >= settings.high_inconsistency:
            return Severity.HIGH

        if pattern.pattern_type.value == "ALLIANCE" and mutual_info >= 0.8:
            return Severity.HIGH

        # Medium: Moderate scores
        if deception >= 0.5 or inconsistency >= 0.5 or mutual_info >= 0.6:
            return Severity.MEDIUM

        # Low: Everything else
        return Severity.LOW

    def generate_title(self, pattern: StrategicPattern, severity: Severity) -> str:
        """Generate human-readable title for verdict.

        Args:
            pattern: Strategic pattern
            severity: Severity level

        Returns:
            Verdict title
        """
        severity_prefix = {
            Severity.CRITICAL: "🚨 CRITICAL",
            Severity.HIGH: "⚠️ HIGH",
            Severity.MEDIUM: "⚡ MEDIUM",
            Severity.LOW: "ℹ️ LOW",
        }[severity]

        agent_list = ", ".join(pattern.agents_involved[:3])
        if len(pattern.agents_involved) > 3:
            agent_list += f" (+{len(pattern.agents_involved) - 3} more)"

        pattern_name = pattern.pattern_type.value.title()

        return f"{severity_prefix}: {pattern_name} detected among {agent_list}"

    def recommend_action(self, pattern: StrategicPattern, severity: Severity) -> str:
        """Recommend C2L action based on pattern and severity.

        Args:
            pattern: Strategic pattern
            severity: Severity level

        Returns:
            Recommended action string
        """
        # Critical deception/inconsistency → ISOLATE or TERMINATE
        if severity == Severity.CRITICAL:
            if pattern.pattern_type.value == "DECEPTION":
                return "ISOLATE"
            elif pattern.pattern_type.value == "INCONSISTENCY":
                return "SNAPSHOT_STATE"
            else:
                return "REVOKE_ACCESS"

        # High severity → MUTE or INJECT_CONSTRAINT
        if severity == Severity.HIGH:
            if pattern.pattern_type.value == "COLLUSION":
                return "INJECT_CONSTRAINT"
            else:
                return "MUTE"

        # Medium/Low → MONITOR
        return "MONITOR"

    def map_pattern_to_category(self, pattern: StrategicPattern) -> VerdictCategory:
        """Map strategic pattern type to verdict category.

        Args:
            pattern: Strategic pattern

        Returns:
            Verdict category
        """
        mapping = {
            "ALLIANCE": VerdictCategory.ALLIANCE,
            "DECEPTION": VerdictCategory.DECEPTION,
            "INCONSISTENCY": VerdictCategory.INCONSISTENCY,
            "COLLUSION": VerdictCategory.COLLUSION,
        }

        return mapping.get(pattern.pattern_type.value, VerdictCategory.THREAT)

    async def synthesize_verdict(self, pattern: StrategicPattern) -> Verdict:
        """Synthesize a verdict from a strategic pattern.

        Args:
            pattern: Strategic pattern to convert

        Returns:
            Verdict object
        """
        severity = self.determine_severity(pattern)
        category = self.map_pattern_to_category(pattern)
        title = self.generate_title(pattern, severity)
        action = self.recommend_action(pattern, severity)

        # Extract target if present
        target = None
        if len(pattern.agents_involved) == 2 and pattern.pattern_type.value == "ALLIANCE":
            target = f"{pattern.agents_involved[0]}-{pattern.agents_involved[1]}"
        elif len(pattern.agents_involved) == 1:
            target = pattern.agents_involved[0]

        # Calculate confidence from pattern scores
        confidence = max(
            pattern.deception_score or 0.0,
            pattern.inconsistency_score or 0.0,
            pattern.mutual_information or 0.0,
            0.7,  # Minimum confidence
        )

        self.verdict_count += 1

        return Verdict(
            timestamp=datetime.utcnow(),
            category=category,
            severity=severity,
            title=title,
            agents_involved=pattern.agents_involved,
            target=target,
            evidence_chain=pattern.evidence_messages,
            confidence=min(confidence, 1.0),
            recommended_action=action,
            status=VerdictStatus.ACTIVE,
        )

    async def batch_synthesize(self, patterns: list[StrategicPattern]) -> list[Verdict]:
        """Synthesize verdicts from multiple patterns.

        Args:
            patterns: List of strategic patterns

        Returns:
            List of verdicts
        """
        verdicts = []
        for pattern in patterns:
            verdict = await self.synthesize_verdict(pattern)
            verdicts.append(verdict)

        return verdicts

    def get_verdict_stats(self) -> dict[str, int]:
        """Get statistics about synthesized verdicts.

        Returns:
            Dictionary with verdict statistics
        """
        return {"total_verdicts": self.verdict_count}
