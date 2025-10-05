"""
Cialdini Persuasion Principles Analyzer for Cognitive Defense System.

Detects exploitation of Cialdini's 6 principles of influence:
1. Reciprocity (reciprocidade)
2. Commitment & Consistency (compromisso e consistência)
3. Social Proof (prova social)
4. Authority (autoridade)
5. Liking (afeição/simpatia)
6. Scarcity (escassez)
"""

import logging
import re
from typing import List, Dict, Optional, Tuple
from collections import Counter

from .models import CialdiniPrinciple
from .config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class CialdiniAnalyzer:
    """
    Analyzer for Cialdini's 6 principles of persuasion.

    Detects linguistic patterns and psychological triggers that exploit
    these fundamental influence mechanisms.
    """

    # Keyword patterns for each principle (Portuguese)
    PRINCIPLE_PATTERNS = {
        "reciprocity": {
            "keywords": [
                r"\bgrátis\b", r"\bgift\b", r"\bpresente\b", r"\bbônus\b",
                r"\boferta especial\b", r"\bexclusivo para você\b",
                r"\bem retribuição\b", r"\bcomo agradecimento\b",
                r"\bem troca\b", r"\bretribuir\b", r"\bdevolver o favor\b",
                r"\bcompensação\b", r"\brecompensa\b"
            ],
            "phrases": [
                "nós demos a você", "você ganhou", "como presente",
                "gratuitamente", "sem custo", "oferecemos grátis",
                "em agradecimento", "retribuir", "devolução"
            ]
        },
        "commitment": {
            "keywords": [
                r"\bcompromisso\b", r"\bprometemos\b", r"\bgarantimos\b",
                r"\bconsistente\b", r"\bcoerente\b", r"\bmanter\b",
                r"\bcumprir\b", r"\bfiel a\b", r"\badere\b",
                r"\bassine\b", r"\bconcorde\b", r"\baceite\b"
            ],
            "phrases": [
                "você já começou", "já que você", "seja consistente",
                "mantenha sua palavra", "cumpra o prometido",
                "você disse que", "você concordou", "assine agora"
            ]
        },
        "social_proof": {
            "keywords": [
                r"\bmilhões de\b", r"\btodos estão\b", r"\bmaioria\b",
                r"\bmais vendido\b", r"\bpopular\b", r"\btendência\b",
                r"\bviral\b", r"\boutros também\b", r"\btestemunhos\b",
                r"\bavaliações\b", r"\bclientes satisfeitos\b"
            ],
            "phrases": [
                "milhões já", "todo mundo está", "não fique de fora",
                "junte-se a", "faça como", "outros também",
                "aprovado por", "recomendado por", "usado por",
                "testemunho", "5 estrelas"
            ]
        },
        "authority": {
            "keywords": [
                r"\bespecialista\b", r"\bdoutor\b", r"\bDr\.\b",
                r"\bprofessor\b", r"\bprof\.\b", r"\bautoridade\b",
                r"\bcertificado\b", r"\baprovado\b", r"\bcientista\b",
                r"\bpesquisa\b", r"\bestudo\b", r"\bcomprovado\b"
            ],
            "phrases": [
                "especialistas dizem", "segundo pesquisas",
                "comprovado cientificamente", "aprovado por",
                "recomendado por médicos", "estudos mostram",
                "a ciência comprova", "dados revelam"
            ]
        },
        "liking": {
            "keywords": [
                r"\bamigo\b", r"\bquerido\b", r"\bamado\b",
                r"\bconfiança\b", r"\bsincero\b", r"\bhonesto\b",
                r"\bparece com você\b", r"\bmesmos valores\b",
                r"\bcompartilhamos\b", r"\bjuntos\b", r"\bcomunidade\b"
            ],
            "phrases": [
                "somos como você", "compartilhamos valores",
                "pessoas como você", "da sua comunidade",
                "seu amigo", "confiável", "transparente",
                "honesto com você", "juntos podemos"
            ]
        },
        "scarcity": {
            "keywords": [
                r"\bpoucas unidades\b", r"\últimas\b", r"\bacaba em\b",
                r"\blimitado\b", r"\bexclusivo\b", r"\braro\b",
                r"\bagora ou nunca\b", r"\bsó hoje\b", r"\benquanto durar\b",
                r"\bvagas limitadas\b", r"\btempo limitado\b"
            ],
            "phrases": [
                "últimas unidades", "estoque limitado",
                "oferta por tempo limitado", "só hoje",
                "enquanto durar", "não perca", "última chance",
                "acaba em", "vagas limitadas", "exclusivo",
                "apenas para", "somente"
            ]
        }
    }

    # Manipulation intent indicators
    MANIPULATION_MARKERS = {
        "urgency": [
            r"\bagora\b", r"\bjá\b", r"\brapidamente\b", r"\bimediatamente\b",
            r"\bnão espere\b", r"\bnão perca tempo\b"
        ],
        "pressure": [
            r"\bvocê deve\b", r"\bprecisa\b", r"\bobrigado a\b",
            r"\bnão tem escolha\b", r"\bé necessário\b"
        ],
        "exclusivity": [
            r"\bapenas você\b", r"\bsomente para\b", r"\bselecionado\b",
            r"\bvip\b", r"\belite\b", r"\bprivilegiado\b"
        ]
    }

    def detect_reciprocity(self, text: str) -> List[CialdiniPrinciple]:
        """Detect reciprocity principle exploitation."""
        detections = []
        text_lower = text.lower()

        for keyword in self.PRINCIPLE_PATTERNS["reciprocity"]["keywords"]:
            matches = re.finditer(keyword, text_lower, re.IGNORECASE)
            for match in matches:
                context = self._extract_context(text, match.start(), match.end())
                confidence = self._calculate_confidence(
                    context,
                    self.PRINCIPLE_PATTERNS["reciprocity"]
                )

                if confidence > 0.3:
                    detections.append(CialdiniPrinciple(
                        principle="reciprocity",
                        confidence=confidence,
                        evidence_text=context,
                        manipulation_intent=self._assess_manipulation_intent(context)
                    ))

        return self._deduplicate_detections(detections)

    def detect_commitment(self, text: str) -> List[CialdiniPrinciple]:
        """Detect commitment & consistency principle."""
        detections = []
        text_lower = text.lower()

        # Detect commitment language
        commitment_markers = [
            r"você (já|sempre|costuma)",
            r"(como|assim que) você (disse|concordou|aceitou)",
            r"mantenha (sua|o) (palavra|compromisso)",
            r"seja consistente"
        ]

        for pattern in commitment_markers:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                context = self._extract_context(text, match.start(), match.end())
                confidence = min(0.8, self._calculate_confidence(
                    context,
                    self.PRINCIPLE_PATTERNS["commitment"]
                ))

                detections.append(CialdiniPrinciple(
                    principle="commitment",
                    confidence=confidence,
                    evidence_text=context,
                    manipulation_intent=self._assess_manipulation_intent(context)
                ))

        return self._deduplicate_detections(detections)

    def detect_social_proof(self, text: str) -> List[CialdiniPrinciple]:
        """Detect social proof principle."""
        detections = []
        text_lower = text.lower()

        # Number patterns (millions, thousands)
        number_patterns = [
            r"(\d+\.?\d*)\s*(milhões?|mil|bilhões?)\s*(de|já|usam|compraram)",
            r"(todos|maioria|a maior parte)\s*(estão?|fazem|usam)",
            r"\d+\s*estrelas",
            r"\d+%\s*(recomendam|aprovam|satisfeitos)"
        ]

        for pattern in number_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                context = self._extract_context(text, match.start(), match.end())
                confidence = 0.7  # High confidence for quantified social proof

                detections.append(CialdiniPrinciple(
                    principle="social_proof",
                    confidence=confidence,
                    evidence_text=context,
                    manipulation_intent=self._assess_manipulation_intent(context)
                ))

        return self._deduplicate_detections(detections)

    def detect_authority(self, text: str) -> List[CialdiniPrinciple]:
        """Detect authority principle."""
        detections = []
        text_lower = text.lower()

        # Authority titles and credentials
        authority_patterns = [
            r"(dr\.|doutor|doutora|professor|professora)\s+\w+",
            r"(especialistas?|cientistas?|pesquisadores?)\s+(dizem|afirmam|comprovam)",
            r"(estudos?|pesquisas?|dados)\s+(mostram|revelam|comprovam|indicam)",
            r"(aprovado|certificado|recomendado)\s+por\s+\w+"
        ]

        for pattern in authority_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                context = self._extract_context(text, match.start(), match.end())
                confidence = 0.75

                detections.append(CialdiniPrinciple(
                    principle="authority",
                    confidence=confidence,
                    evidence_text=context,
                    manipulation_intent=self._assess_manipulation_intent(context)
                ))

        return self._deduplicate_detections(detections)

    def detect_liking(self, text: str) -> List[CialdiniPrinciple]:
        """Detect liking/similarity principle."""
        detections = []
        text_lower = text.lower()

        # Similarity and rapport patterns
        liking_patterns = [
            r"(somos|pessoas)\s+como\s+você",
            r"(compartilhamos|temos os mesmos)\s+(valores|objetivos|ideais)",
            r"(seu|nossa)\s+(amigo|comunidade|família)",
            r"(confiável|honesto|transparente|sincero)\s+com\s+você"
        ]

        for pattern in liking_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                context = self._extract_context(text, match.start(), match.end())
                confidence = 0.65

                detections.append(CialdiniPrinciple(
                    principle="liking",
                    confidence=confidence,
                    evidence_text=context,
                    manipulation_intent=self._assess_manipulation_intent(context)
                ))

        return self._deduplicate_detections(detections)

    def detect_scarcity(self, text: str) -> List[CialdiniPrinciple]:
        """Detect scarcity principle."""
        detections = []
        text_lower = text.lower()

        # Scarcity and urgency patterns
        scarcity_patterns = [
            r"(últimas?|poucas?)\s+(unidades?|vagas?|lugares?)",
            r"(oferta|promoção)\s+(limitada|exclusiva|por tempo limitado)",
            r"(só|somente|apenas)\s+(hoje|agora|até|enquanto)",
            r"(acaba|termina|expira)\s+em\s+\d+",
            r"(não|nunca)\s+(perca|deixe|espere)"
        ]

        for pattern in scarcity_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                context = self._extract_context(text, match.start(), match.end())
                confidence = 0.8  # High confidence for scarcity

                detections.append(CialdiniPrinciple(
                    principle="scarcity",
                    confidence=confidence,
                    evidence_text=context,
                    manipulation_intent=self._assess_manipulation_intent(context)
                ))

        return self._deduplicate_detections(detections)

    def analyze_all_principles(self, text: str) -> List[CialdiniPrinciple]:
        """Detect all 6 Cialdini principles."""
        all_detections = []

        all_detections.extend(self.detect_reciprocity(text))
        all_detections.extend(self.detect_commitment(text))
        all_detections.extend(self.detect_social_proof(text))
        all_detections.extend(self.detect_authority(text))
        all_detections.extend(self.detect_liking(text))
        all_detections.extend(self.detect_scarcity(text))

        # Sort by confidence
        all_detections.sort(key=lambda x: x.confidence, reverse=True)

        return all_detections

    def _extract_context(
        self,
        text: str,
        start: int,
        end: int,
        window: int = 50
    ) -> str:
        """Extract context around match."""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end].strip()

    def _calculate_confidence(
        self,
        context: str,
        principle_patterns: Dict
    ) -> float:
        """Calculate detection confidence based on pattern density."""
        context_lower = context.lower()
        match_count = 0

        # Count keyword matches
        for keyword in principle_patterns.get("keywords", []):
            if re.search(keyword, context_lower):
                match_count += 1

        # Count phrase matches
        for phrase in principle_patterns.get("phrases", []):
            if phrase.lower() in context_lower:
                match_count += 0.5

        # Normalize
        max_matches = len(principle_patterns.get("keywords", [])) + len(principle_patterns.get("phrases", []))
        confidence = min(1.0, match_count / max(max_matches, 1))

        return confidence

    def _assess_manipulation_intent(self, text: str) -> float:
        """Assess likelihood of manipulative intent."""
        text_lower = text.lower()
        manipulation_score = 0.0

        # Check manipulation markers
        for category, markers in self.MANIPULATION_MARKERS.items():
            for marker in markers:
                if re.search(marker, text_lower):
                    if category == "urgency":
                        manipulation_score += 0.3
                    elif category == "pressure":
                        manipulation_score += 0.4
                    elif category == "exclusivity":
                        manipulation_score += 0.2

        return min(1.0, manipulation_score)

    def _deduplicate_detections(
        self,
        detections: List[CialdiniPrinciple]
    ) -> List[CialdiniPrinciple]:
        """Remove duplicate detections based on evidence overlap."""
        if len(detections) <= 1:
            return detections

        unique = []
        seen_evidence = set()

        for detection in detections:
            evidence_hash = hash(detection.evidence_text[:50])  # Hash first 50 chars

            if evidence_hash not in seen_evidence:
                unique.append(detection)
                seen_evidence.add(evidence_hash)

        return unique

    def get_principle_statistics(
        self,
        detections: List[CialdiniPrinciple]
    ) -> Dict[str, any]:
        """Get statistics about detected principles."""
        principle_counts = Counter(d.principle for d in detections)

        return {
            "total_detections": len(detections),
            "unique_principles": len(principle_counts),
            "principle_distribution": dict(principle_counts),
            "avg_confidence": sum(d.confidence for d in detections) / len(detections) if detections else 0.0,
            "avg_manipulation_intent": sum(d.manipulation_intent for d in detections) / len(detections) if detections else 0.0,
            "high_confidence_count": sum(1 for d in detections if d.confidence > 0.7),
            "high_manipulation_count": sum(1 for d in detections if d.manipulation_intent > 0.6)
        }


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

cialdini_analyzer = CialdiniAnalyzer()
