"""
Logical Fallacy Classifier for Cognitive Defense System.

Detects 21 types of logical fallacies using:
1. Transformer-based classification
2. Pattern matching for specific fallacies
3. Argument structure analysis
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Tuple

from cache_manager import cache_manager, CacheCategory
from config import get_settings
from models import Argument, ArgumentRole, Fallacy, FallacyType
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from utils import hash_text

logger = logging.getLogger(__name__)

settings = get_settings()


class FallacyClassifier:
    """
    Multi-class fallacy classifier.

    Detects 21 types of logical fallacies in arguments.
    """

    # Fallacy pattern indicators (Portuguese)
    FALLACY_PATTERNS = {
        FallacyType.AD_HOMINEM: {
            "keywords": [
                r"\bvocê (é|está) (idiota|burro|ignorante)\b",
                r"\bataque pessoal\b",
                r"\bcontra a pessoa\b",
                r"\bdesqualificar\b",
                r"\binsulto\b",
            ],
            "phrases": ["você não entende", "típico de", "esperado de alguém como"],
        },
        FallacyType.STRAW_MAN: {
            "keywords": [
                r"\bvocê (diz|afirma|defende) que\b.*\b(mas na verdade|porém)\b",
                r"\bdistorcer\b",
                r"\bdeturpar\b",
                r"\bexagerar posição\b",
            ],
            "phrases": [
                "então você está dizendo",
                "você quer dizer que",
                "basicamente você defende",
            ],
        },
        FallacyType.FALSE_DILEMMA: {
            "keywords": [
                r"\bou\s+\w+\s+ou\s+\w+\b",
                r"\bsó (há|existe) (duas|2) opções\b",
                r"\b(é|são) (isso|aquilo) ou nada\b",
                r"\bnão há meio termo\b",
            ],
            "phrases": [
                "ou você está comigo ou contra mim",
                "ou aceita ou",
                "apenas duas escolhas",
            ],
        },
        FallacyType.SLIPPERY_SLOPE: {
            "keywords": [
                r"\bse (permitirmos|aceitarmos)\b.*\bentão\b.*\b(em breve|logo|depois)\b",
                r"\blevar[áa] (inevitavelmente)?\s*(a|à)\b",
                r"\bcadeia de eventos\b",
                r"\bconsequências catastróficas\b",
            ],
            "phrases": [
                "se começarmos",
                "isso vai levar a",
                "o próximo passo será",
                "daqui a pouco",
            ],
        },
        FallacyType.APPEAL_TO_AUTHORITY: {
            "keywords": [
                r"\b(especialistas?|cientistas?|médicos?) (dizem|afirmam)\b",
                r"\b(segundo|conforme) (dr\.|doutor|professor)\b",
                r"\bautoridade no assunto\b",
            ],
            "phrases": ["fulano disse", "especialistas concordam", "a ciência prova"],
        },
        FallacyType.AD_POPULUM: {
            "keywords": [
                r"\btod(os|as) (pensam|acreditam|sabem)\b",
                r"\ba maioria (diz|afirma)\b",
                r"\bsenso comum\b",
                r"\b(todo mundo|todos) (fazem|sabem)\b",
            ],
            "phrases": ["todo mundo sabe", "a maioria concorda", "é óbvio para todos"],
        },
        FallacyType.HASTY_GENERALIZATION: {
            "keywords": [
                r"\btodos os \w+ (são|estão)\b",
                r"\bnenhum \w+ (é|está)\b",
                r"\bsempre\b.*\bnunca\b",
                r"\bem todos os casos\b",
            ],
            "phrases": [
                "todos são assim",
                "nenhum é",
                "sempre foi assim",
                "nunca muda",
            ],
        },
        FallacyType.FALSE_CAUSALITY: {
            "keywords": [
                r"\bpor causa (de|disso)\b",
                r"\bdevido a\b",
                r"\b(causa|provocou|gerou)\b",
                r"\bcorrelação (é|implica) causalidade\b",
            ],
            "phrases": ["isso causou", "por conta disso", "foi o motivo de"],
        },
        FallacyType.CIRCULAR_REASONING: {
            "keywords": [
                r"\bporque (é|sim)\b",
                r"\bé verdade porque é\b",
                r"\bmesma (premissa|conclusão)\b",
            ],
            "phrases": ["é assim porque é", "porque sim", "está certo porque está"],
        },
        FallacyType.BEGGING_THE_QUESTION: {
            "keywords": [
                r"\bpressupõe que\b",
                r"\bassume-se que\b",
                r"\b(óbvio|evidente) que\b",
            ],
            "phrases": ["é óbvio que", "claramente", "naturalmente"],
        },
    }

    # Counter-argument templates
    COUNTER_TEMPLATES = {
        FallacyType.AD_HOMINEM: "Atacar a pessoa não invalida o argumento. Foque nos fatos apresentados.",
        FallacyType.STRAW_MAN: "Isso distorce a posição original. O argumento real é diferente.",
        FallacyType.FALSE_DILEMMA: "Existem mais alternativas além dessas duas opções apresentadas.",
        FallacyType.SLIPPERY_SLOPE: "Essa cadeia de consequências não é inevitável. Faltam evidências da progressão.",
        FallacyType.APPEAL_TO_AUTHORITY: "A autoridade citada precisa ser verificada. Argumente pelos méritos, não pela fonte.",
        FallacyType.AD_POPULUM: "A popularidade não determina a verdade. A maioria já esteve errada.",
        FallacyType.HASTY_GENERALIZATION: "Generalização baseada em evidência insuficiente. Casos específicos não representam o todo.",
        FallacyType.FALSE_CAUSALITY: "Correlação não implica causalidade. Outros fatores podem estar envolvidos.",
        FallacyType.CIRCULAR_REASONING: "O argumento é circular - a conclusão está nas premissas.",
        FallacyType.BEGGING_THE_QUESTION: "Isso assume como verdade o que deveria ser provado.",
    }

    def __init__(
        self,
        model_name: str = "neuralmind/bert-base-portuguese-cased",
        device: str = "cpu",
    ):
        """
        Initialize fallacy classifier.

        Args:
            model_name: HuggingFace model
            device: 'cpu' or 'cuda'
        """
        self.model_name = model_name
        self.device = device

        self.tokenizer: Optional[AutoTokenizer] = None
        self.model: Optional[AutoModelForSequenceClassification] = None

        self._initialized = False

    async def initialize(self) -> None:
        """Load model and tokenizer."""
        if self._initialized:
            logger.warning("Fallacy classifier already initialized")
            return

        try:
            logger.info(f"Loading fallacy classifier: {self.model_name}")

            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name, use_fast=True
            )

            # Multi-class classification (21 fallacies)
            num_labels = len(FallacyType)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name,
                num_labels=num_labels,
                problem_type="single_label_classification",
            )

            self.model.to(self.device)
            self.model.eval()

            # Quantization
            if self.device == "cpu":
                self.model = torch.quantization.quantize_dynamic(
                    self.model, {torch.nn.Linear}, dtype=torch.qint8
                )

            self._initialized = True
            logger.info("✅ Fallacy classifier initialized")

        except Exception as e:
            logger.error(
                f"❌ Failed to initialize fallacy classifier: {e}", exc_info=True
            )
            raise

    @torch.no_grad()
    def classify_fallacy(
        self, argument: Argument, min_confidence: float = 0.6, use_cache: bool = True
    ) -> Optional[Fallacy]:
        """
        Classify fallacy in argument.

        Args:
            argument: Argument to analyze
            min_confidence: Minimum confidence
            use_cache: Use cache

        Returns:
            Fallacy or None
        """
        if not self._initialized:
            raise RuntimeError("Model not initialized")

        text = argument.text

        # Check cache
        if use_cache:
            cache_key = f"fallacy:{hash_text(text)}"
            cached = asyncio.get_event_loop().run_until_complete(
                cache_manager.get(CacheCategory.MODEL_CACHE, cache_key)
            )
            if cached:
                return Fallacy(**cached) if cached else None

        # Tokenize
        inputs = self.tokenizer(
            text, return_tensors="pt", truncation=True, max_length=512, padding=True
        ).to(self.device)

        # Forward pass
        outputs = self.model(**inputs)
        logits = outputs.logits[0].cpu()

        # Get prediction
        probs = torch.softmax(logits, dim=0).numpy()
        pred_idx = int(probs.argmax())
        confidence = float(probs[pred_idx])

        if confidence < min_confidence:
            return None

        # Map to FallacyType
        fallacy_types = list(FallacyType)
        fallacy_type = fallacy_types[pred_idx]

        # Create Fallacy object
        fallacy = Fallacy(
            fallacy_type=fallacy_type,
            argument_id=argument.id,
            description=self._generate_description(fallacy_type, text),
            severity=self._calculate_severity(fallacy_type, confidence),
            evidence=text,
            counter_argument=self.COUNTER_TEMPLATES.get(
                fallacy_type, "Este argumento contém uma falácia lógica."
            ),
        )

        # Cache
        if use_cache:
            cache_key = f"fallacy:{hash_text(text)}"
            asyncio.get_event_loop().run_until_complete(
                cache_manager.set(
                    CacheCategory.MODEL_CACHE,
                    cache_key,
                    fallacy.model_dump(),
                    ttl_override=3600,
                )
            )

        return fallacy

    def detect_fallacies_by_patterns(self, argument: Argument) -> List[Fallacy]:
        """
        Detect fallacies using pattern matching.

        Args:
            argument: Argument to analyze

        Returns:
            List of detected fallacies
        """
        fallacies = []
        text_lower = argument.text.lower()

        for fallacy_type, patterns in self.FALLACY_PATTERNS.items():
            # Check keywords
            keyword_matches = sum(
                1
                for pattern in patterns.get("keywords", [])
                if re.search(pattern, text_lower, re.IGNORECASE)
            )

            # Check phrases
            phrase_matches = sum(
                1
                for phrase in patterns.get("phrases", [])
                if phrase.lower() in text_lower
            )

            total_matches = keyword_matches + phrase_matches

            if total_matches > 0:
                confidence = min(0.9, total_matches * 0.3)

                fallacy = Fallacy(
                    fallacy_type=fallacy_type,
                    argument_id=argument.id,
                    description=self._generate_description(fallacy_type, argument.text),
                    severity=self._calculate_severity(fallacy_type, confidence),
                    evidence=argument.text,
                    counter_argument=self.COUNTER_TEMPLATES.get(
                        fallacy_type, "Falácia detectada."
                    ),
                )
                fallacies.append(fallacy)

        return fallacies

    def analyze_argument_for_fallacies(
        self, argument: Argument, use_ml: bool = True, use_patterns: bool = True
    ) -> List[Fallacy]:
        """
        Comprehensive fallacy detection (ML + patterns).

        Args:
            argument: Argument to analyze
            use_ml: Use ML model
            use_patterns: Use pattern matching

        Returns:
            List of detected fallacies
        """
        fallacies = []

        # ML-based detection
        if use_ml:
            ml_fallacy = self.classify_fallacy(argument)
            if ml_fallacy:
                fallacies.append(ml_fallacy)

        # Pattern-based detection
        if use_patterns:
            pattern_fallacies = self.detect_fallacies_by_patterns(argument)
            fallacies.extend(pattern_fallacies)

        # Deduplicate by type
        seen_types = set()
        unique_fallacies = []

        for fallacy in fallacies:
            if fallacy.fallacy_type not in seen_types:
                unique_fallacies.append(fallacy)
                seen_types.add(fallacy.fallacy_type)

        return unique_fallacies

    @staticmethod
    def _generate_description(fallacy_type: FallacyType, text: str) -> str:
        """Generate human-readable description."""
        descriptions = {
            FallacyType.AD_HOMINEM: f"Ataque pessoal ao invés de refutar o argumento: '{text[:100]}...'",
            FallacyType.STRAW_MAN: f"Distorção da posição original: '{text[:100]}...'",
            FallacyType.FALSE_DILEMMA: f"Apresenta apenas duas opções quando há mais: '{text[:100]}...'",
            FallacyType.SLIPPERY_SLOPE: f"Assume cadeia de consequências sem evidência: '{text[:100]}...'",
            FallacyType.APPEAL_TO_AUTHORITY: f"Apela à autoridade sem justificativa: '{text[:100]}...'",
            FallacyType.AD_POPULUM: f"Apela à popularidade ao invés de evidência: '{text[:100]}...'",
            FallacyType.HASTY_GENERALIZATION: f"Generalização precipitada: '{text[:100]}...'",
            FallacyType.FALSE_CAUSALITY: f"Assume causalidade sem evidência: '{text[:100]}...'",
            FallacyType.CIRCULAR_REASONING: f"Raciocínio circular - conclusão nas premissas: '{text[:100]}...'",
            FallacyType.BEGGING_THE_QUESTION: f"Assume como verdade o que deveria provar: '{text[:100]}...'",
        }

        return descriptions.get(
            fallacy_type, f"Falácia {fallacy_type.value} detectada: '{text[:100]}...'"
        )

    @staticmethod
    def _calculate_severity(fallacy_type: FallacyType, confidence: float) -> float:
        """
        Calculate fallacy severity.

        Args:
            fallacy_type: Type of fallacy
            confidence: Detection confidence

        Returns:
            Severity score (0-1)
        """
        # Base severity by type
        SEVERITY_WEIGHTS = {
            FallacyType.AD_HOMINEM: 0.8,  # High - personal attacks
            FallacyType.STRAW_MAN: 0.9,  # Very high - deliberate distortion
            FallacyType.FALSE_DILEMMA: 0.7,
            FallacyType.SLIPPERY_SLOPE: 0.6,
            FallacyType.APPEAL_TO_AUTHORITY: 0.5,
            FallacyType.AD_POPULUM: 0.6,
            FallacyType.HASTY_GENERALIZATION: 0.7,
            FallacyType.FALSE_CAUSALITY: 0.8,
            FallacyType.CIRCULAR_REASONING: 0.9,  # Very high
            FallacyType.BEGGING_THE_QUESTION: 0.8,
        }

        base_severity = SEVERITY_WEIGHTS.get(fallacy_type, 0.5)
        severity = base_severity * confidence

        return min(1.0, severity)

    def batch_classify(
        self, arguments: List[Argument], batch_size: int = 16
    ) -> List[Optional[Fallacy]]:
        """
        Batch fallacy classification.

        Args:
            arguments: List of arguments
            batch_size: Batch size

        Returns:
            List of fallacies (or None)
        """
        results = []

        for i in range(0, len(arguments), batch_size):
            batch = arguments[i : i + batch_size]
            texts = [arg.text for arg in batch]

            # Tokenize
            inputs = self.tokenizer(
                texts,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True,
            ).to(self.device)

            # Forward pass
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits.cpu()

            # Process each
            for arg, logit in zip(batch, logits):
                probs = torch.softmax(logit, dim=0).numpy()
                pred_idx = int(probs.argmax())
                confidence = float(probs[pred_idx])

                if confidence < 0.6:
                    results.append(None)
                    continue

                fallacy_types = list(FallacyType)
                fallacy_type = fallacy_types[pred_idx]

                fallacy = Fallacy(
                    fallacy_type=fallacy_type,
                    argument_id=arg.id,
                    description=self._generate_description(fallacy_type, arg.text),
                    severity=self._calculate_severity(fallacy_type, confidence),
                    evidence=arg.text,
                    counter_argument=self.COUNTER_TEMPLATES.get(
                        fallacy_type, "Falácia detectada."
                    ),
                )

                results.append(fallacy)

        return results


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

fallacy_classifier = FallacyClassifier(
    device="cuda" if torch.cuda.is_available() else "cpu"
)
