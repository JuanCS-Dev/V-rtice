"""
Dark Triad Personality Markers Detector for Cognitive Defense System.

Detects linguistic markers of Dark Triad personality traits:
1. Narcissism (narcisismo) - Grandiosity, self-focus, entitlement
2. Machiavellianism (maquiavelismo) - Manipulation, cynicism, strategic
3. Psychopathy (psicopatia) - Callousness, impulsivity, lack of empathy
"""

import logging
import re
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

from models import DarkTriadMarkers
from config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class DarkTriadDetector:
    """
    Detector for Dark Triad personality markers in text.

    Based on linguistic research correlating text patterns with
    Dark Triad assessment scales (NPI, MACH-IV, SRP).
    """

    # Narcissism linguistic markers
    NARCISSISM_PATTERNS = {
        "grandiosity": [
            r"\beu sou (o melhor|superior|especial|único|extraordinário)\b",
            r"\bninguém (como|igual a) (mim|eu)\b",
            r"\b(meu|minha) (grandeza|superioridade|excelência)\b",
            r"\bmerecedor de (admiração|respeito|reconhecimento)\b",
            r"\bdestinado a (grandeza|sucesso|liderança)\b"
        ],
        "self_focus": [
            r"\b(eu|meu|minha|comigo)\b",  # Excessive first-person
            r"\bminha (visão|ideia|projeto|conquista)\b",
            r"\bsó eu (posso|consigo|sei)\b"
        ],
        "entitlement": [
            r"\bmerecedor?\b", r"\btenho direito a\b", r"\bdevo receber\b",
            r"\bnada menos que\b", r"\bexijo\b", r"\bdemando\b"
        ],
        "superiority": [
            r"\bmais inteligente que\b", r"\bacima (de|dos|das)\b",
            r"\binferiores?\b", r"\bcomuns\b", r"\bmediocres?\b",
            r"\bvocês não entendem\b"
        ],
        "admiration_seeking": [
            r"\badmirem\b", r"\breconheçam\b", r"\bapreciem\b",
            r"\bvejam o que (fiz|consegui)\b", r"\bsou incrível\b"
        ]
    }

    # Machiavellianism linguistic markers
    MACHIAVELLIANISM_PATTERNS = {
        "manipulation": [
            r"\b(manipular|controlar|usar) (pessoas|outros)\b",
            r"\b(estratégia|tática) para (conseguir|obter)\b",
            r"\bfazer eles (pensarem|acreditarem|agirem)\b",
            r"\bjogar com\b", r"\binstrumentalizar\b"
        ],
        "cynicism": [
            r"\btodos (são|estão) (egoístas|interesseiros)\b",
            r"\bninguém (faz|age) (por|sem) (interesse|benefício)\b",
            r"\bmundo cruel\b", r"\bconfiar em ninguém\b",
            r"\bpessoas são (fracas|tolas|ingênuas)\b"
        ],
        "strategic_thinking": [
            r"\b(plano|estratégia) (para|de) (longo prazo|controle)\b",
            r"\b(calcular|planejar) (cada|todos) (passo|movimento)\b",
            r"\bxadrez\b.*\bpeças\b", r"\bjogo de poder\b"
        ],
        "amorality": [
            r"\bfins justificam os meios\b",
            r"\b(moral|ética) (é|são) (relativa|flexível|fraca)\b",
            r"\bfazer o (que|necessário) for (preciso|necessário)\b",
            r"\bprincípios (atrapalham|são limitantes)\b"
        ],
        "exploitation": [
            r"\baproveitar(-se)? (da|de|dos)\b",
            r"\bexplorar (fraquezas?|vulnerabilidades?)\b",
            r"\busar (contra|a favor)\b",
            r"\btirar vantagem\b"
        ]
    }

    # Psychopathy linguistic markers
    PSYCHOPATHY_PATTERNS = {
        "callousness": [
            r"\bnão (me )?import(a|o) (com|se)\b",
            r"\btanto faz\b", r"\bque se (dane|lixe|foda)\b",
            r"\bproblema (deles|dela|dele)\b",
            r"\bfrio e calculista\b", r"\bsem sentimentos\b"
        ],
        "lack_empathy": [
            r"\bnão consigo (sentir|me importar)\b",
            r"\bfraqueza (emocional|sentimental)\b",
            r"\bempatia (é|serve para) (fraqueza|nada)\b",
            r"\bchoro (é|dos) fracos?\b"
        ],
        "impulsivity": [
            r"\b(faço|fiz) sem pensar\b", r"\bimpulso\b",
            r"\bnão (planejo|calculo)\b", r"\bação imediata\b",
            r"\bagir (rápido|já|agora)\b"
        ],
        "thrill_seeking": [
            r"\badrenalina\b", r"\brisco\b", r"\bperigo\b",
            r"\bemoção (forte|intensa)\b", r"\bentediado com\b",
            r"\bpreciso de (ação|emoção)\b"
        ],
        "superficial_charm": [
            r"\bfacilmente (convenço|seduzo|persuado)\b",
            r"\bcharme\b", r"\bcarismático\b",
            r"\bconsigo (o que|qualquer) (quero|coisa)\b"
        ],
        "blame_externalization": [
            r"\bnão foi culpa minha\b", r"\beles (me fizeram|provocaram)\b",
            r"\bcircunstâncias\b", r"\bvítima das\b",
            r"\bnão tenho responsabilidade\b"
        ]
    }

    def __init__(self):
        """Initialize Dark Triad detector."""
        pass

    def detect_narcissism(self, text: str) -> float:
        """
        Detect narcissism markers.

        Args:
            text: Input text

        Returns:
            Narcissism score (0-1)
        """
        text_lower = text.lower()
        score = 0.0
        total_weight = 0.0

        # Category weights
        weights = {
            "grandiosity": 0.30,
            "self_focus": 0.20,
            "entitlement": 0.25,
            "superiority": 0.15,
            "admiration_seeking": 0.10
        }

        for category, patterns in self.NARCISSISM_PATTERNS.items():
            matches = sum(
                1 for pattern in patterns
                if re.search(pattern, text_lower, re.IGNORECASE)
            )

            # Normalize by pattern count
            category_score = min(1.0, matches / len(patterns))
            score += category_score * weights[category]
            total_weight += weights[category]

        # Check first-person pronoun density (narcissism correlate)
        words = text_lower.split()
        first_person_count = sum(
            1 for word in words
            if word in ["eu", "meu", "minha", "meus", "minhas", "comigo", "me"]
        )
        first_person_ratio = first_person_count / len(words) if words else 0

        # Excessive self-reference (>10% is high)
        if first_person_ratio > 0.10:
            score += 0.2
        elif first_person_ratio > 0.15:
            score += 0.3

        return min(1.0, score)

    def detect_machiavellianism(self, text: str) -> float:
        """
        Detect Machiavellianism markers.

        Args:
            text: Input text

        Returns:
            Machiavellianism score (0-1)
        """
        text_lower = text.lower()
        score = 0.0

        weights = {
            "manipulation": 0.30,
            "cynicism": 0.25,
            "strategic_thinking": 0.20,
            "amorality": 0.15,
            "exploitation": 0.10
        }

        for category, patterns in self.MACHIAVELLIANISM_PATTERNS.items():
            matches = sum(
                1 for pattern in patterns
                if re.search(pattern, text_lower, re.IGNORECASE)
            )

            category_score = min(1.0, matches / len(patterns))
            score += category_score * weights[category]

        return min(1.0, score)

    def detect_psychopathy(self, text: str) -> float:
        """
        Detect psychopathy markers.

        Args:
            text: Input text

        Returns:
            Psychopathy score (0-1)
        """
        text_lower = text.lower()
        score = 0.0

        weights = {
            "callousness": 0.25,
            "lack_empathy": 0.25,
            "impulsivity": 0.15,
            "thrill_seeking": 0.10,
            "superficial_charm": 0.15,
            "blame_externalization": 0.10
        }

        for category, patterns in self.PSYCHOPATHY_PATTERNS.items():
            matches = sum(
                1 for pattern in patterns
                if re.search(pattern, text_lower, re.IGNORECASE)
            )

            category_score = min(1.0, matches / len(patterns))
            score += category_score * weights[category]

        return min(1.0, score)

    def analyze_dark_triad(self, text: str) -> DarkTriadMarkers:
        """
        Analyze all Dark Triad dimensions.

        Args:
            text: Input text

        Returns:
            DarkTriadMarkers with all scores
        """
        narcissism = self.detect_narcissism(text)
        machiavellianism = self.detect_machiavellianism(text)
        psychopathy = self.detect_psychopathy(text)

        return DarkTriadMarkers(
            narcissism=narcissism,
            machiavellianism=machiavellianism,
            psychopathy=psychopathy
        )

    def get_dominant_trait(
        self,
        markers: DarkTriadMarkers
    ) -> Tuple[str, float]:
        """
        Get dominant Dark Triad trait.

        Args:
            markers: DarkTriadMarkers

        Returns:
            (trait_name, score) tuple
        """
        traits = {
            "narcissism": markers.narcissism,
            "machiavellianism": markers.machiavellianism,
            "psychopathy": markers.psychopathy
        }

        dominant = max(traits.items(), key=lambda x: x[1])
        return dominant

    def detect_dark_tetrad(self, text: str) -> Dict[str, float]:
        """
        Detect Dark Tetrad (Dark Triad + Sadism).

        Args:
            text: Input text

        Returns:
            Dict with 4 trait scores
        """
        markers = self.analyze_dark_triad(text)

        # Sadism markers (additional)
        sadism_patterns = [
            r"\b(prazer|gozo) (em|com) (sofrimento|dor|humilhação)\b",
            r"\b(adorar|amar) ver (sofrer|chorar|implorar)\b",
            r"\b(crueldade|tortura) (é|como) (divertida|prazerosa)\b",
            r"\bmerecido sofrimento\b"
        ]

        text_lower = text.lower()
        sadism_matches = sum(
            1 for pattern in sadism_patterns
            if re.search(pattern, text_lower)
        )
        sadism_score = min(1.0, sadism_matches / len(sadism_patterns))

        return {
            "narcissism": markers.narcissism,
            "machiavellianism": markers.machiavellianism,
            "psychopathy": markers.psychopathy,
            "sadism": sadism_score
        }

    def assess_manipulation_risk(
        self,
        markers: DarkTriadMarkers
    ) -> Dict[str, any]:
        """
        Assess manipulation risk based on Dark Triad profile.

        Args:
            markers: DarkTriadMarkers

        Returns:
            Risk assessment dict
        """
        aggregate = markers.aggregate_score

        # Risk thresholds
        if aggregate >= 0.7:
            risk_level = "critical"
            risk_description = "High Dark Triad traits - severe manipulation risk"
        elif aggregate >= 0.5:
            risk_level = "high"
            risk_description = "Moderate-high Dark Triad traits - significant manipulation risk"
        elif aggregate >= 0.3:
            risk_level = "medium"
            risk_description = "Some Dark Triad traits present - moderate manipulation risk"
        else:
            risk_level = "low"
            risk_description = "Low Dark Triad traits - minimal manipulation risk"

        # Specific combinations (more dangerous)
        if markers.machiavellianism > 0.6 and markers.psychopathy > 0.6:
            risk_level = "critical"
            risk_description += " | Mach + Psychopathy combo detected (predatory)"

        if markers.narcissism > 0.7 and markers.machiavellianism > 0.5:
            risk_level = "critical"
            risk_description += " | Narc + Mach combo detected (exploitative leader)"

        return {
            "risk_level": risk_level,
            "aggregate_score": aggregate,
            "description": risk_description,
            "dominant_trait": self.get_dominant_trait(markers)[0],
            "recommended_action": self._recommend_action(risk_level)
        }

    @staticmethod
    def _recommend_action(risk_level: str) -> str:
        """Recommend action based on risk level."""
        actions = {
            "critical": "BLOCK - High manipulation risk, potentially harmful content",
            "high": "WARN - Flag for review, alert users to manipulation tactics",
            "medium": "FLAG - Monitor and log, inform users of persuasion attempts",
            "low": "ALLOW - Low risk, normal processing"
        }
        return actions.get(risk_level, "ALLOW")


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

dark_triad_detector = DarkTriadDetector()
