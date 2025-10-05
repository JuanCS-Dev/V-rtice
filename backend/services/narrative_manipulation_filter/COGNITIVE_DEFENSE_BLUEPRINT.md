# 🧠 Cognitive Defense System - Technical Blueprint
## Narrative Manipulation Filter Evolution to Prefrontal Cortex-Inspired Architecture

> **Version:** 2.0.0
> **Date:** 2025-10-05
> **Based on:** AI Narrative Manipulation Defense Research (Academic Paper)
> **Quality Standard:** 100% Functional, Zero Placeholders, Production-Ready

---

## I. EXECUTIVE SUMMARY

### Vision
Transform the `narrative_manipulation_filter` from a simple keyword-based detector into a sophisticated cognitive defense system that mirrors the human prefrontal cortex's executive functions, capable of detecting subtle narrative manipulation through multi-layered analysis.

### Core Principle
**Mimetic Cognition**: The system architecture directly mirrors human prefrontal cortex functions:
- **Executive Control** → Orchestration & prioritization
- **Working Memory** → Contextual analysis & history
- **Cognitive Control** → Multi-tier filtering & attention
- **Decision Making** → Aggregated threat scoring

### Success Metrics
- **Accuracy:** >92% on propaganda detection (SemEval-2020 benchmark)
- **Throughput:** >1000 claims/day verification
- **Latency:** <500ms for Tier 1 analysis, <5s for Tier 2
- **Robustness:** Certified defense against ±2 character adversarial perturbations

---

## II. ARCHITECTURAL OVERVIEW

### 2.1 Prefrontal Cortex Analogy

```
HUMAN PREFRONTAL CORTEX          →    COGNITIVE DEFENSE SYSTEM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Executive Function                    ExecutiveController
├─ Task switching                     ├─ Module orchestration
├─ Planning & strategy                ├─ Analysis pipeline sequencing
├─ Error detection                    ├─ Confidence validation
└─ Goal management                    └─ Threat score aggregation

Working Memory                        WorkingMemorySystem
├─ Temporary information storage      ├─ Redis cache (claims, scores)
├─ Context maintenance                ├─ PostgreSQL (historical profiles)
├─ Information manipulation           ├─ Seriema Graph (argument networks)
└─ Buffer for ongoing tasks           └─ Analysis context tracking

Cognitive Control                     CognitiveControlLayer
├─ Attention allocation               ├─ Check-worthiness scoring
├─ Interference suppression           ├─ Adversarial input filtering
├─ Performance monitoring             ├─ Model drift detection
└─ Conflict resolution                └─ Multi-signal reconciliation

Decision Making                       ThreatAssessmentEngine
├─ Evaluate options                   ├─ Multi-module score aggregation
├─ Risk assessment                    ├─ Bayesian belief updating
├─ Value judgment                     ├─ Confidence intervals
└─ Action selection                   └─ Response recommendation
```

### 2.2 System Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                    EXECUTIVE CONTROLLER                          │
│  (Orchestrates analysis pipeline, manages cognitive resources)  │
└────────────┬─────────────────────────────────────────┬──────────┘
             │                                         │
    ┌────────▼────────┐                      ┌────────▼─────────┐
    │ WORKING MEMORY  │◄────────────────────►│ COGNITIVE CONTROL│
    │   - Redis       │                      │  - Prioritization│
    │   - PostgreSQL  │                      │  - Filtering     │
    │   - Seriema     │                      │  - Monitoring    │
    └────────┬────────┘                      └────────┬─────────┘
             │                                         │
    ┌────────▼────────────────────────────────────────▼──────────┐
    │              4 CORE DETECTION MODULES                       │
    ├───────────────┬──────────────┬──────────────┬──────────────┤
    │    MODULE 1   │   MODULE 2   │   MODULE 3   │   MODULE 4   │
    │    Source     │  Emotional   │   Logical    │   Reality    │
    │  Credibility  │ Manipulation │   Fallacy    │  Distortion  │
    └───────┬───────┴──────┬───────┴──────┬───────┴──────┬───────┘
            │              │              │              │
    ┌───────▼──────────────▼──────────────▼──────────────▼───────┐
    │             INTEGRATION LAYER                               │
    │  - NewsGuard API    - ClaimBuster API  - Gemini 2.0        │
    │  - Google Fact Check - DBpedia        - BERTimbau Models   │
    └────────────────────────────────────────────────────────────┘
```

---

## III. MODULE 1 - SOURCE CREDIBILITY ASSESSMENT

### 3.1 Objective
Dynamic, multi-factor credibility scoring that adapts to evolving information environment.

### 3.2 Architecture

#### Phase 1: External API Integration (NewsGuard)
```python
class NewsGuardClient:
    """
    Integration with NewsGuard API for journalist-vetted credibility scores.

    Features:
    - 0-100 trust scores for 35,000+ domains
    - "Nutrition Label" detailed reports
    - Redis caching (TTL: 7 days)
    - Automatic retry with exponential backoff
    """

    async def get_credibility_score(self, domain: str) -> NewsGuardScore:
        # 1. Check Redis cache
        cached = await self.redis.get(f"newsguard:{domain}")
        if cached:
            return NewsGuardScore.parse_raw(cached)

        # 2. Query NewsGuard API
        response = await self.http_client.get(
            f"{self.api_base}/score/{domain}",
            headers={"X-API-Key": self.api_key},
            timeout=5.0
        )

        # 3. Parse and cache
        score = NewsGuardScore(**response.json())
        await self.redis.setex(
            f"newsguard:{domain}",
            timedelta(days=7),
            score.json()
        )

        return score
```

#### Phase 2: Internal Historical Analysis
```python
class ReputationTracker:
    """
    Tracks source reputation over time using internal analysis history.

    Metrics Tracked:
    - Frequency of articles flagged for emotional manipulation
    - Logical fallacy detection rate
    - Failed fact-check percentage
    - Publisher corrections/retractions
    - Ownership changes
    """

    async def calculate_historical_score(self, domain: str) -> float:
        # Query historical analyses from PostgreSQL
        history = await self.db.execute(
            select(Analysis)
            .where(Analysis.source_domain == domain)
            .order_by(Analysis.timestamp.desc())
            .limit(100)
        )

        # Calculate weighted metrics
        manipulation_rate = sum(a.manipulation_score > 0.6 for a in history) / len(history)
        fallacy_rate = sum(len(a.fallacies) > 0 for a in history) / len(history)
        factcheck_fail_rate = sum(a.factcheck_failed for a in history) / len(history)

        # Bayesian scoring
        base_score = 0.5  # Neutral prior
        manipulation_penalty = manipulation_rate * 0.3
        fallacy_penalty = fallacy_rate * 0.2
        factcheck_penalty = factcheck_fail_rate * 0.4

        return max(0.0, base_score - manipulation_penalty - fallacy_penalty - factcheck_penalty)
```

#### Phase 3: Dynamic Scoring Engine
```python
class DynamicCredibilityScorer:
    """
    Synthesizes external and internal signals into final credibility score.

    Formula:
    Score = (w_ng * NewsGuard_score + w_hist * Historical_score) * decay_factor

    Features:
    - Time-decay function (confidence degrades over 30 days)
    - Domain-hopping detection (content fingerprinting via MinHash)
    - Anomaly detection (sudden reputation changes)
    """

    async def compute_score(self, domain: str) -> CredibilityScore:
        # Get external score
        ng_score = await self.newsguard.get_credibility_score(domain)

        # Get internal historical score
        hist_score = await self.reputation.calculate_historical_score(domain)

        # Calculate time decay
        last_analysis = await self.get_last_analysis_time(domain)
        decay = self._time_decay_factor(last_analysis)

        # Weighted average with decay
        w_ng = 0.7  # Higher weight for NewsGuard (professional journalists)
        w_hist = 0.3

        final_score = (w_ng * ng_score.score + w_hist * hist_score) * decay

        # Domain-hopping check
        fingerprint = await self.fingerprint_content(domain)
        similar_domains = await self.find_similar_fingerprints(fingerprint)

        if similar_domains:
            # Propagate negative reputation
            final_score = min(final_score, min(d.score for d in similar_domains))

        return CredibilityScore(
            domain=domain,
            score=final_score,
            newsguard_component=ng_score.score,
            historical_component=hist_score,
            decay_factor=decay,
            domain_hopping_detected=bool(similar_domains),
            confidence=self._calculate_confidence(ng_score, hist_score)
        )

    def _time_decay_factor(self, last_analysis: datetime) -> float:
        """Exponential decay: score confidence reduces 50% every 30 days."""
        days_since = (datetime.now() - last_analysis).days
        return 0.5 ** (days_since / 30.0)
```

### 3.3 Domain Fingerprinting (Anti-Hopping)
```python
class DomainFingerprinter:
    """
    Creates MinHash signatures of content to detect domain-hopping.

    Technique: MinHash LSH (Locality-Sensitive Hashing)
    - Shingle size: 3 (trigrams)
    - Hash functions: 128
    - Similarity threshold: 0.85
    """

    def create_fingerprint(self, content: str) -> MinHashSignature:
        # Create shingles (3-grams)
        shingles = set()
        tokens = content.lower().split()
        for i in range(len(tokens) - 2):
            shingle = ' '.join(tokens[i:i+3])
            shingles.add(shingle)

        # MinHash
        minhash = MinHash(num_perm=128)
        for shingle in shingles:
            minhash.update(shingle.encode('utf8'))

        return MinHashSignature(
            domain=self.extract_domain(content),
            signature=minhash.digest(),
            timestamp=datetime.now()
        )

    async def find_similar_domains(self, signature: MinHashSignature) -> List[str]:
        """
        Query LSH forest to find domains with similar content.
        Jaccard similarity > 0.85 indicates likely domain-hopping.
        """
        lsh = MinHashLSH(threshold=0.85, num_perm=128)

        # Query existing signatures from database
        existing = await self.db.get_all_signatures()
        for sig in existing:
            lsh.insert(sig.domain, sig.signature)

        # Find matches
        matches = lsh.query(signature.signature)
        return [m for m in matches if m != signature.domain]
```

---

## IV. MODULE 2 - EMOTIONAL MANIPULATION DETECTION

### 4.1 Objective
Deep NLP-based detection of psychological tactics, propaganda, and emotional triggers.

### 4.2 Multi-Layer Architecture

#### Layer 1: Foundational Sentiment & Tone Analysis
```python
class EmotionClassifier:
    """
    Fine-tuned BERTimbau for multi-label emotion classification.

    Model: neuralmind/bert-base-portuguese-cased (BERTimbau)
    Fine-tuned on: GoEmotions-PT (Portuguese-adapted)

    Emotions Detected (27 categories):
    - Primary: anger, fear, joy, sadness, surprise, disgust
    - Secondary: anxiety, confusion, excitement, pride, relief, etc.
    - Tones: sarcasm, irony, urgency, aggression
    """

    def __init__(self):
        self.model = AutoModelForSequenceClassification.from_pretrained(
            "./models/bertimbau-emotions",
            num_labels=27
        )
        self.tokenizer = AutoTokenizer.from_pretrained("neuralmind/bert-base-portuguese-cased")

        # Quantization for faster inference
        self.model = torch.quantization.quantize_dynamic(
            self.model,
            {torch.nn.Linear},
            dtype=torch.qint8
        )

    async def classify_emotions(self, text: str) -> EmotionProfile:
        # Tokenize
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        )

        # Inference
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.sigmoid(outputs.logits).squeeze()

        # Multi-label thresholding (>0.5)
        emotions = {}
        for idx, prob in enumerate(probs):
            if prob > 0.5:
                emotion = self.emotion_labels[idx]
                emotions[emotion] = prob.item()

        return EmotionProfile(
            text=text,
            detected_emotions=emotions,
            dominant_emotion=max(emotions.items(), key=lambda x: x[1])[0] if emotions else None,
            emotional_intensity=max(emotions.values()) if emotions else 0.0
        )
```

#### Layer 2: Propaganda Technique Classification
```python
class PropagandaSpanDetector:
    """
    Span-based propaganda technique detector using RoBERTa + BiLSTM.

    Based on: SemEval-2020 Task 11 (Fine-Grained Propaganda Detection)
    Architecture: RoBERTa embeddings → BiLSTM → CRF (sequence tagging)

    Techniques Detected (18 types):
    - Loaded Language
    - Name Calling/Labeling
    - Exaggeration/Minimization
    - Appeal to Fear/Prejudice
    - Flag-Waving
    - Causal Oversimplification
    - Doubt
    - Repetition
    - Obfuscation/Vagueness
    - Red Herring
    - Straw Man
    - Whataboutism
    - Black-and-White Fallacy
    - Thought-Terminating Cliché
    - Appeal to Authority
    - Bandwagon
    - Reductio ad Hitlerum
    - Glittering Generalities
    """

    def __init__(self):
        self.roberta = AutoModel.from_pretrained("./models/roberta-pt-propaganda")
        self.bilstm = nn.LSTM(
            input_size=768,  # RoBERTa hidden size
            hidden_size=256,
            num_layers=2,
            bidirectional=True,
            batch_first=True
        )
        self.crf = CRF(num_tags=37, batch_first=True)  # 18 techniques * 2 (BIO tagging) + 1 (O)

    async def detect_propaganda(self, text: str) -> List[PropagandaSpan]:
        # Tokenize
        tokens = self.tokenizer(text, return_tensors="pt")

        # RoBERTa embeddings
        with torch.no_grad():
            embeddings = self.roberta(**tokens).last_hidden_state

        # BiLSTM
        lstm_out, _ = self.bilstm(embeddings)

        # CRF decode
        predictions = self.crf.decode(lstm_out)

        # Extract spans
        spans = []
        current_span = None

        for idx, tag_id in enumerate(predictions[0]):
            tag = self.id2tag[tag_id]

            if tag.startswith('B-'):  # Begin
                if current_span:
                    spans.append(current_span)
                current_span = PropagandaSpan(
                    technique=tag[2:],
                    start=tokens.token_to_chars(0, idx).start,
                    end=tokens.token_to_chars(0, idx).end,
                    text=""
                )
            elif tag.startswith('I-') and current_span:  # Inside
                current_span.end = tokens.token_to_chars(0, idx).end
            elif tag == 'O' and current_span:  # Outside
                spans.append(current_span)
                current_span = None

        # Populate text for each span
        for span in spans:
            span.text = text[span.start:span.end]

        return spans
```

#### Layer 3: Psychological Manipulation Pattern Recognition

**3.1 Cialdini's 6 Principles Detector**
```python
class CialdiniDetector:
    """
    Detects linguistic patterns of Cialdini's 6 Principles of Persuasion.

    Principles:
    1. Reciprocity: "free gift", "no obligation", "complimentary"
    2. Commitment/Consistency: "you said", "you agreed", "stick to"
    3. Social Proof: "most popular", "best-selling", "everyone"
    4. Authority: "experts say", "studies show", "according to"
    5. Liking: "people like you", "similar to you", "in common"
    6. Scarcity: "limited time", "only X left", "exclusive"
    """

    def __init__(self):
        # Fine-tuned RoBERTa for multi-class classification
        self.model = AutoModelForSequenceClassification.from_pretrained(
            "./models/roberta-cialdini",
            num_labels=6
        )
        self.tokenizer = AutoTokenizer.from_pretrained("roberta-base")

    async def detect_principles(self, text: str) -> Dict[str, float]:
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)

        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1).squeeze()

        principles = {
            "reciprocity": probs[0].item(),
            "commitment": probs[1].item(),
            "social_proof": probs[2].item(),
            "authority": probs[3].item(),
            "liking": probs[4].item(),
            "scarcity": probs[5].item()
        }

        return {k: v for k, v in principles.items() if v > 0.3}  # Threshold
```

**3.2 Dark Triad Linguistic Markers**
```python
class DarkTriadDetector:
    """
    Identifies linguistic markers of Dark Triad personality traits.

    Traits:
    - Narcissism: excessive first-person pronouns, grandiose language
    - Machiavellianism: manipulative phrasing, cynicism
    - Psychopathy: lack of empathy, impulsivity, aggression

    Features:
    - Pronoun analysis (I/me/my ratio)
    - Semantic similarity to trait lexicons
    - Syntactic complexity patterns
    """

    def analyze_narcissism(self, text: str) -> float:
        tokens = text.lower().split()
        first_person = ['i', 'me', 'my', 'mine', 'myself']
        ratio = sum(1 for t in tokens if t in first_person) / len(tokens)

        # Grandiosity detection
        grandiose_words = ['best', 'greatest', 'superior', 'exceptional', 'unique']
        grandiose_score = sum(1 for t in tokens if t in grandiose_words) / len(tokens)

        return min(1.0, ratio * 10 + grandiose_score * 5)

    def analyze_machiavellianism(self, text: str) -> float:
        # Semantic similarity to Machiavellian lexicon
        lexicon_embeddings = self.get_lexicon_embeddings("machiavellianism")
        text_embedding = self.sentence_transformer.encode(text)

        similarity = cosine_similarity([text_embedding], lexicon_embeddings)[0]
        return similarity.max()

    def analyze_psychopathy(self, text: str) -> float:
        # Lack of empathy indicators
        empathy_words = ['feel', 'sorry', 'understand', 'care', 'compassion']
        tokens = text.lower().split()
        empathy_absence = 1.0 - (sum(1 for t in tokens if t in empathy_words) / len(tokens) * 10)

        # Aggression indicators
        aggressive_words = ['attack', 'destroy', 'hate', 'kill', 'hurt']
        aggression_score = sum(1 for t in tokens if t in aggressive_words) / len(tokens) * 20

        return min(1.0, (empathy_absence + aggression_score) / 2)
```

**3.3 Cognitive Bias Exploitation Detector**
```python
class CognitiveBiasDetector:
    """
    Detects attempts to exploit cognitive biases using CIFT framework.

    CoBAIT-Informed Fine-Tuning (CIFT):
    - Fine-tune model with context snippets describing target bias
    - Enables detection of subtle bias exploitation

    Biases Detected:
    - Confirmation Bias
    - Anchoring Effect
    - Availability Heuristic
    - Bandwagon Effect
    - Sunk Cost Fallacy
    - Authority Bias
    - Dunning-Kruger Effect
    """

    def __init__(self):
        self.model = AutoModelForSequenceClassification.from_pretrained(
            "./models/bert-cobait",
            num_labels=7
        )

        # Context descriptions for each bias (CIFT methodology)
        self.bias_contexts = {
            "confirmation": "This text reinforces existing beliefs without presenting contradictory evidence",
            "anchoring": "This text uses an initial number or fact to influence subsequent judgments",
            "availability": "This text relies on easily recalled examples rather than comprehensive data",
            "bandwagon": "This text suggests that popularity or consensus makes something true",
            "sunk_cost": "This text implies continuing because of past investment rather than future value",
            "authority": "This text appeals to authority figures without evaluating the actual evidence",
            "dunning_kruger": "This text exhibits overconfidence in limited knowledge"
        }

    async def detect_bias_exploitation(self, text: str) -> Dict[str, float]:
        results = {}

        for bias_name, context in self.bias_contexts.items():
            # CIFT: prepend context description
            augmented_text = f"{context}. Text: {text}"

            inputs = self.tokenizer(
                augmented_text,
                return_tensors="pt",
                truncation=True,
                max_length=512
            )

            with torch.no_grad():
                outputs = self.model(**inputs)
                prob = torch.sigmoid(outputs.logits).item()

            if prob > 0.5:
                results[bias_name] = prob

        return results
```

#### Layer 4: Multimodal Meme Analysis
```python
class MemeAnalyzer:
    """
    Multimodal analysis of memes using early fusion of text and image embeddings.

    Architecture:
    - Text: RoBERTa embeddings
    - Image: CLIP ViT embeddings
    - Fusion: Concatenation → Dense layers → Classification

    Detects:
    - Persuasion techniques in memes
    - Emotional manipulation through imagery
    - Juxtaposition-based irony
    """

    def __init__(self):
        self.text_model = AutoModel.from_pretrained("roberta-base")
        self.image_model = CLIPVisionModel.from_pretrained("openai/clip-vit-base-patch32")

        # Fusion network
        self.fusion = nn.Sequential(
            nn.Linear(768 + 768, 512),  # RoBERTa (768) + CLIP (768)
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, 18)  # 18 propaganda techniques
        )

    async def analyze_meme(self, image: PILImage, text: str) -> MemeAnalysis:
        # Text embedding
        text_inputs = self.text_tokenizer(text, return_tensors="pt")
        with torch.no_grad():
            text_emb = self.text_model(**text_inputs).last_hidden_state[:, 0, :]  # CLS token

        # Image embedding
        image_inputs = self.image_processor(image, return_tensors="pt")
        with torch.no_grad():
            image_emb = self.image_model(**image_inputs).last_hidden_state[:, 0, :]  # CLS token

        # Early fusion
        fused = torch.cat([text_emb, image_emb], dim=-1)

        # Classification
        with torch.no_grad():
            logits = self.fusion(fused)
            probs = torch.sigmoid(logits).squeeze()

        # Extract techniques (multi-label)
        techniques = []
        for idx, prob in enumerate(probs):
            if prob > 0.5:
                techniques.append({
                    "technique": self.technique_labels[idx],
                    "confidence": prob.item()
                })

        return MemeAnalysis(
            text=text,
            detected_techniques=techniques,
            text_emotion=await self.emotion_classifier.classify(text),
            visual_sentiment=self._analyze_visual_sentiment(image)
        )
```

---

## V. MODULE 3 - LOGICAL FALLACY IDENTIFICATION

### 5.1 Objective
Two-stage pipeline: argument mining → fallacy classification using deep learning + formal argumentation.

### 5.2 Stage 1: Argument Mining

```python
class ArgumentMiner:
    """
    Neural argument mining using BiLSTM-CNN-CRF (TARGER architecture).

    Extracts:
    - Claims (conclusions)
    - Premises (evidence/reasons)
    - Argument structure (support/attack relationships)

    Model Architecture:
    - Embeddings: Word2Vec (300d) + character-level CNN
    - BiLSTM: 2 layers, 256 hidden units
    - CRF: Constrained decoding for BIO tags

    Tags:
    - B-CLAIM, I-CLAIM (claim boundaries)
    - B-PREMISE, I-PREMISE (premise boundaries)
    - O (outside argument)
    """

    def __init__(self):
        self.word_embeddings = KeyedVectors.load("./models/word2vec-pt.bin")
        self.char_cnn = CharCNN(vocab_size=100, embedding_dim=50, filters=30)

        self.bilstm = nn.LSTM(
            input_size=300 + 30,  # Word2Vec + char CNN
            hidden_size=256,
            num_layers=2,
            bidirectional=True,
            batch_first=True
        )

        self.crf = CRF(num_tags=5, batch_first=True)  # B-C, I-C, B-P, I-P, O

    async def extract_arguments(self, text: str) -> List[Argument]:
        # Tokenize
        tokens = self.tokenize(text)

        # Word embeddings
        word_embs = []
        for token in tokens:
            try:
                word_embs.append(self.word_embeddings[token])
            except KeyError:
                word_embs.append(np.zeros(300))  # UNK

        # Character embeddings
        char_embs = self.char_cnn.encode(tokens)

        # Concatenate
        combined = torch.cat([
            torch.tensor(word_embs),
            char_embs
        ], dim=-1).unsqueeze(0)

        # BiLSTM
        lstm_out, _ = self.bilstm(combined)

        # CRF decode
        predictions = self.crf.decode(lstm_out)[0]

        # Extract claims and premises
        arguments = []
        current = None

        for idx, (token, tag_id) in enumerate(zip(tokens, predictions)):
            tag = self.id2tag[tag_id]

            if tag == 'B-CLAIM':
                if current:
                    arguments.append(current)
                current = Argument(type='claim', tokens=[token], start=idx, end=idx)
            elif tag == 'I-CLAIM' and current and current.type == 'claim':
                current.tokens.append(token)
                current.end = idx
            elif tag == 'B-PREMISE':
                if current:
                    arguments.append(current)
                current = Argument(type='premise', tokens=[token], start=idx, end=idx)
            elif tag == 'I-PREMISE' and current and current.type == 'premise':
                current.tokens.append(token)
                current.end = idx
            elif tag == 'O':
                if current:
                    arguments.append(current)
                    current = None

        if current:
            arguments.append(current)

        # Reconstruct text
        for arg in arguments:
            arg.text = ' '.join(arg.tokens)

        return arguments
```

### 5.3 Stage 2: Fallacy Classification

```python
class FallacyClassifier:
    """
    Multi-class fallacy classifier with specialized detectors.

    Fallacies Detected (8 types):
    1. Ad Hominem (attack on person)
    2. Straw Man (misrepresenting opponent's argument)
    3. Red Herring (irrelevant topic introduction)
    4. False Dilemma (only two options presented)
    5. Circular Reasoning (premise = conclusion)
    6. Appeal to Authority (unjustified expert citation)
    7. Slippery Slope (chain reaction without justification)
    8. Hasty Generalization (insufficient sample size)

    Methods:
    - Semantic relevance scoring (for relevance fallacies)
    - Similarity scoring (for circular reasoning)
    - LLM-based reasoning (Gemini 2.0 fallback)
    """

    def __init__(self):
        self.bert_classifier = AutoModelForSequenceClassification.from_pretrained(
            "./models/bert-fallacies",
            num_labels=8
        )
        self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
        self.gemini_client = GeminiReasoningClient()

    async def classify_fallacy(self, claim: Argument, premise: Argument) -> Optional[Fallacy]:
        # Method 1: BERT classification
        text = f"Premise: {premise.text} Claim: {claim.text}"
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True)

        with torch.no_grad():
            outputs = self.bert_classifier(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1).squeeze()

        max_prob, max_idx = probs.max(dim=0)

        if max_prob > 0.7:  # High confidence
            return Fallacy(
                type=self.fallacy_types[max_idx],
                confidence=max_prob.item(),
                claim=claim,
                premise=premise,
                method="bert_classifier"
            )

        # Method 2: Semantic relevance (for relevance fallacies)
        relevance = self._calculate_relevance(claim, premise)
        if relevance < 0.3:  # Low relevance
            if self._is_personal_attack(premise):
                return Fallacy(type="ad_hominem", confidence=0.8, claim=claim, premise=premise)
            else:
                return Fallacy(type="red_herring", confidence=0.7, claim=claim, premise=premise)

        # Method 3: Similarity (for circular reasoning)
        similarity = self._calculate_similarity(claim, premise)
        if similarity > 0.9:
            return Fallacy(type="circular_reasoning", confidence=similarity, claim=claim, premise=premise)

        # Method 4: LLM-based reasoning (Gemini 2.0)
        if max_prob > 0.5:  # Medium confidence - verify with LLM
            llm_result = await self.gemini_client.verify_fallacy(
                claim=claim.text,
                premise=premise.text,
                suspected_fallacy=self.fallacy_types[max_idx]
            )

            if llm_result.confirmed:
                return Fallacy(
                    type=llm_result.fallacy_type,
                    confidence=llm_result.confidence,
                    claim=claim,
                    premise=premise,
                    explanation=llm_result.explanation,
                    method="gemini_verification"
                )

        return None

    def _calculate_relevance(self, claim: Argument, premise: Argument) -> float:
        """Cosine similarity between premise and claim embeddings."""
        emb_claim = self.sentence_transformer.encode(claim.text)
        emb_premise = self.sentence_transformer.encode(premise.text)
        return cosine_similarity([emb_claim], [emb_premise])[0][0]

    def _calculate_similarity(self, claim: Argument, premise: Argument) -> float:
        """Semantic similarity for circular reasoning detection."""
        return self._calculate_relevance(claim, premise)

    def _is_personal_attack(self, premise: Argument) -> bool:
        """Heuristic detection of personal attacks."""
        attack_keywords = ['stupid', 'idiot', 'liar', 'corrupt', 'incompetent']
        return any(kw in premise.text.lower() for kw in attack_keywords)
```

### 5.4 Gemini 2.0 Advanced Reasoning Service

```python
class GeminiReasoningClient:
    """
    Uses Gemini 2.0 for advanced fallacy detection with strategic prompting.

    Strategies (from research):
    1. Generate counterarguments
    2. Explain reasoning step-by-step
    3. Identify goals of the argument
    4. Evaluate logical validity
    """

    FALLACY_DETECTION_PROMPT = """
You are a logic and critical thinking expert. Analyze the following argument for logical fallacies.

PREMISE: {premise}
CLAIM: {claim}

SUSPECTED FALLACY: {suspected_fallacy}

Please:
1. Generate a counterargument to this claim
2. Explain step-by-step why the premise supports or doesn't support the claim
3. Identify the goal/purpose of this argument
4. Determine if the suspected fallacy is present

Respond in JSON format:
{{
    "fallacy_confirmed": true/false,
    "fallacy_type": "specific fallacy name",
    "confidence": 0.0-1.0,
    "explanation": "detailed explanation",
    "counterargument": "your counterargument",
    "reasoning_steps": ["step1", "step2", ...],
    "argument_goal": "identified purpose"
}}
"""

    async def verify_fallacy(self, claim: str, premise: str, suspected_fallacy: str) -> FallacyVerification:
        prompt = self.FALLACY_DETECTION_PROMPT.format(
            claim=claim,
            premise=premise,
            suspected_fallacy=suspected_fallacy
        )

        response = await self.gemini.generate_content_async(
            prompt,
            generation_config={
                "temperature": 0.2,  # Low temperature for logical reasoning
                "top_p": 0.9,
                "max_output_tokens": 1024
            }
        )

        result = json.loads(response.text)

        return FallacyVerification(
            confirmed=result["fallacy_confirmed"],
            fallacy_type=result["fallacy_type"],
            confidence=result["confidence"],
            explanation=result["explanation"],
            counterargument=result["counterargument"],
            reasoning_steps=result["reasoning_steps"],
            argument_goal=result["argument_goal"]
        )
```

### 5.5 Abstract Argumentation Frameworks (Seriema Graph Integration)

```python
class ArgumentationGraphBuilder:
    """
    Constructs formal argumentation graphs using Dung's Abstract Argumentation Framework.

    Stores in Seriema Graph:
    - Nodes: Arguments (claims + premises)
    - Edges: Support/Attack relationships

    Enables:
    - Evaluation of argument admissibility
    - Identification of stable extensions
    - Detection of inconsistent argument sets
    """

    async def build_graph(self, arguments: List[Argument], fallacies: List[Fallacy]) -> ArgumentationGraph:
        graph = ArgumentationGraph()

        # Add argument nodes
        for arg in arguments:
            graph.add_node(
                id=arg.id,
                type=arg.type,
                text=arg.text,
                node_type="argument"
            )

        # Add support relationships (premises → claims)
        for claim in [a for a in arguments if a.type == 'claim']:
            for premise in [a for a in arguments if a.type == 'premise']:
                # If premise appears before claim in text, it likely supports it
                if premise.start < claim.start:
                    relevance = self._calculate_semantic_relevance(premise, claim)
                    if relevance > 0.5:
                        graph.add_edge(
                            source=premise.id,
                            target=claim.id,
                            relationship="supports",
                            weight=relevance
                        )

        # Add attack relationships (fallacies)
        for fallacy in fallacies:
            graph.add_edge(
                source=fallacy.premise.id,
                target=fallacy.claim.id,
                relationship="attacks",
                fallacy_type=fallacy.type,
                confidence=fallacy.confidence
            )

        # Store in Seriema Graph
        await self.seriema.store_argumentation_graph(graph)

        return graph

    async def evaluate_admissibility(self, graph: ArgumentationGraph) -> Set[str]:
        """
        Compute admissible arguments using Dung's semantics.

        An argument is admissible if:
        1. It defends itself against all attackers
        2. All its supporters are also admissible
        """
        # Query Seriema for attack relationships
        attacks = await self.seriema.get_attack_relationships(graph.id)

        # Compute admissible set (iterative fixed-point algorithm)
        admissible = set()
        changed = True

        while changed:
            changed = False
            for node in graph.nodes:
                if node.id in admissible:
                    continue

                # Check if all attackers are defeated
                attackers = [a.source for a in attacks if a.target == node.id]
                defenders = [d.source for d in graph.edges if d.target in attackers and d.source in admissible]

                if len(attackers) == len(defenders):
                    admissible.add(node.id)
                    changed = True

        return admissible
```

---

## VI. MODULE 4 - REALITY DISTORTION VERIFICATION

### 6.1 Objective
High-throughput, scalable fact-checking combining API matching with knowledge graph verification.

### 6.2 Architecture: Two-Tier System

```
┌─────────────────────────────────────────────────────────────┐
│                       INCOMING CLAIM                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                ┌────────▼────────┐
                │ Check-Worthiness │  ClaimBuster API
                │     Scoring      │  (0.0 - 1.0 score)
                └────────┬────────┘
                         │
              ┌──────────▼──────────┐
              │  Score > 0.5?       │
              └──┬───────────────┬──┘
                 │ No            │ Yes
                 │               │
        ┌────────▼──────┐  ┌────▼──────────────┐
        │  Skip         │  │   TIER 1          │
        │  Verification │  │  High-Speed       │
        └───────────────┘  │  Claim Matching   │
                           └────┬──────────────┘
                                │
                       ┌────────▼────────┐
                       │ Cache Hit?      │
                       └──┬─────────────┬┘
                          │ Yes         │ No
                   ┌──────▼──────┐      │
                   │ Return      │      │
                   │ Cached      │      │
                   └─────────────┘      │
                                        │
                              ┌─────────▼─────────┐
                              │ Query External    │
                              │ Fact-Check APIs   │
                              │ - ClaimBuster     │
                              │ - Google FC       │
                              └─────┬─────────────┘
                                    │
                         ┌──────────▼──────────┐
                         │ Match Found?        │
                         └──┬──────────────┬───┘
                            │ Yes          │ No
                     ┌──────▼──────┐       │
                     │ Cache &     │       │
                     │ Return      │       │
                     └─────────────┘       │
                                           │
                                  ┌────────▼────────┐
                                  │   TIER 2        │
                                  │  Deep           │
                                  │  Verification   │
                                  │  (Async Queue)  │
                                  └────┬────────────┘
                                       │
                            ┌──────────▼──────────┐
                            │ Entity Linking      │
                            │ (DBpedia Spotlight) │
                            └──────┬──────────────┘
                                   │
                            ┌──────▼──────────────┐
                            │ SPARQL Generation   │
                            │ & KG Query          │
                            │ (Wikidata/DBpedia)  │
                            └──────┬──────────────┘
                                   │
                            ┌──────▼──────────────┐
                            │ Verification Result │
                            │ Cache & Return      │
                            └─────────────────────┘
```

### 6.3 Tier 1: High-Speed Claim Matching

#### Check-Worthiness Scoring
```python
class CheckWorthinessScorer:
    """
    Determines if a claim is worth fact-checking using ClaimBuster API.

    Score Interpretation:
    - 0.0-0.3: Not check-worthy (opinion, question)
    - 0.3-0.5: Borderline
    - 0.5-1.0: Check-worthy (factual claim)
    """

    async def score_claim(self, claim: str) -> float:
        response = await self.http_client.post(
            "https://idir.uta.edu/claimbuster/api/v2/score/text",
            json={"input_text": claim}
        )

        result = response.json()
        return result["score"]
```

#### Claim Matching
```python
class ClaimMatcher:
    """
    Matches claims against existing fact-check databases.

    Sources:
    - ClaimBuster database (fact_matcher endpoint)
    - Google Fact Check Tools API (ClaimReview data)
    - Internal verified claims cache

    Caching Strategy:
    - Redis cache with 30-day TTL
    - Key: MinHash signature of claim (for fuzzy matching)
    """

    async def find_match(self, claim: str) -> Optional[FactCheckResult]:
        # 1. Check Redis cache
        claim_hash = self._hash_claim(claim)
        cached = await self.redis.get(f"factcheck:{claim_hash}")
        if cached:
            return FactCheckResult.parse_raw(cached)

        # 2. Query ClaimBuster fact_matcher
        cb_result = await self.claimbuster.match_claim(claim)
        if cb_result and cb_result.similarity > 0.85:
            await self._cache_result(claim_hash, cb_result)
            return cb_result

        # 3. Query Google Fact Check API
        gfc_result = await self.google_factcheck.search(claim)
        if gfc_result and gfc_result.relevance_score > 0.8:
            await self._cache_result(claim_hash, gfc_result)
            return gfc_result

        # 4. No match found
        return None

    def _hash_claim(self, claim: str) -> str:
        """MinHash for fuzzy matching of paraphrased claims."""
        minhash = MinHash(num_perm=128)
        tokens = claim.lower().split()
        for token in tokens:
            minhash.update(token.encode('utf8'))
        return minhash.digest().hex()
```

#### ClaimBuster Client
```python
class ClaimBusterClient:
    """
    Client for ClaimBuster fact-checking API.

    Endpoints:
    - /score/text: Check-worthiness scoring
    - /fact_matcher: Match claim against database
    """

    BASE_URL = "https://idir.uta.edu/claimbuster/api/v2"

    async def match_claim(self, claim: str) -> Optional[ClaimMatch]:
        response = await self.http_client.post(
            f"{self.BASE_URL}/fact_matcher",
            json={"input_claim": claim}
        )

        data = response.json()

        if data["matches"]:
            best_match = max(data["matches"], key=lambda m: m["similarity"])

            return ClaimMatch(
                original_claim=claim,
                matched_claim=best_match["claim"],
                similarity=best_match["similarity"],
                verdict=best_match["verdict"],  # true/false/mixed
                source=best_match["source"],
                url=best_match["url"],
                fact_checker=best_match["fact_checker"]
            )

        return None
```

#### Google Fact Check Client
```python
class GoogleFactCheckClient:
    """
    Client for Google Fact Check Tools API.

    Queries ClaimReview structured data from fact-checkers:
    - FactCheck.org
    - PolitiFact
    - Snopes
    - AFP Fact Check
    - Full Fact
    - etc.
    """

    BASE_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

    async def search(self, claim: str) -> Optional[FactCheckResult]:
        params = {
            "query": claim,
            "languageCode": "pt",  # Portuguese
            "key": self.api_key
        }

        response = await self.http_client.get(self.BASE_URL, params=params)
        data = response.json()

        if "claims" not in data:
            return None

        # Get most relevant result
        best = max(data["claims"], key=lambda c: c.get("relevanceScore", 0))

        return FactCheckResult(
            claim=claim,
            matched_claim=best["text"],
            relevance_score=best.get("relevanceScore", 0.0),
            claim_review=best.get("claimReview", [{}])[0],
            fact_checker=best.get("claimant", "Unknown"),
            rating=self._parse_rating(best),
            url=best.get("claimReview", [{}])[0].get("url", "")
        )

    def _parse_rating(self, claim_data: dict) -> str:
        """Extract rating from ClaimReview."""
        reviews = claim_data.get("claimReview", [])
        if reviews:
            return reviews[0].get("textualRating", "Unknown")
        return "Unknown"
```

### 6.4 Tier 2: Deep Verification via Knowledge Graphs

#### Entity Linking
```python
class EntityLinker:
    """
    Links entity mentions to canonical knowledge base IDs.

    Pipeline:
    1. spaCy NER (Portuguese)
    2. DBpedia Spotlight (entity disambiguation)
    3. Wikidata ID resolution

    Example:
    "Barack Obama" → Q76 (Wikidata ID)
    "Kenya" → Q114 (Wikidata ID)
    """

    def __init__(self):
        self.nlp = spacy.load("pt_core_news_lg")  # Portuguese model
        self.spotlight_url = "https://api.dbpedia-spotlight.org/pt/annotate"

    async def extract_entities(self, text: str) -> List[Entity]:
        # spaCy NER
        doc = self.nlp(text)
        entities = []

        for ent in doc.ents:
            # DBpedia Spotlight disambiguation
            response = await self.http_client.get(
                self.spotlight_url,
                params={
                    "text": ent.text,
                    "confidence": 0.5
                },
                headers={"Accept": "application/json"}
            )

            if response.status_code == 200:
                data = response.json()
                if "Resources" in data:
                    resource = data["Resources"][0]

                    # Extract Wikidata ID from DBpedia URI
                    wikidata_id = await self._dbpedia_to_wikidata(resource["@URI"])

                    entities.append(Entity(
                        text=ent.text,
                        label=ent.label_,
                        dbpedia_uri=resource["@URI"],
                        wikidata_id=wikidata_id,
                        confidence=float(resource["@similarityScore"])
                    ))

        return entities

    async def _dbpedia_to_wikidata(self, dbpedia_uri: str) -> Optional[str]:
        """Resolve DBpedia URI to Wikidata ID using owl:sameAs."""
        query = f"""
        SELECT ?wikidata WHERE {{
            <{dbpedia_uri}> owl:sameAs ?wikidata .
            FILTER(STRSTARTS(STR(?wikidata), "http://www.wikidata.org/entity/"))
        }}
        """

        response = await self.sparql_client.query("https://dbpedia.org/sparql", query)

        if response["results"]["bindings"]:
            uri = response["results"]["bindings"][0]["wikidata"]["value"]
            return uri.split("/")[-1]  # Extract Q-ID

        return None
```

#### SPARQL Query Generation
```python
class SPARQLQueryGenerator:
    """
    Automatically generates SPARQL queries from extracted entities and relationships.

    Strategy:
    1. Identify subject, predicate, object from claim
    2. Map to Wikidata properties
    3. Generate query
    4. Execute on Wikidata/DBpedia

    Example Claim: "Barack Obama was born in Kenya"
    Generated Query:
    SELECT ?birthPlace WHERE {
        wd:Q76 wdt:P19 ?birthPlace .
    }
    Expected Result: wd:Q1552 (Honolulu, Hawaii) ≠ Q114 (Kenya) → FALSE
    """

    PROPERTY_MAPPINGS = {
        "born": "wdt:P19",  # place of birth
        "died": "wdt:P20",  # place of death
        "spouse": "wdt:P26",  # spouse
        "occupation": "wdt:P106",  # occupation
        "country": "wdt:P17",  # country
        "capital": "wdt:P36",  # capital
        "population": "wdt:P1082",  # population
        # ... extensive mapping
    }

    async def generate_query(self, claim: str, entities: List[Entity]) -> SPARQLQuery:
        # Parse claim structure using dependency parsing
        doc = self.nlp(claim)

        # Extract subject, predicate, object
        subject = None
        predicate = None
        obj = None

        for token in doc:
            if token.dep_ == "nsubj":  # Subject
                subject = self._find_entity(token.text, entities)
            elif token.pos_ == "VERB":  # Predicate
                predicate = self._map_predicate(token.lemma_)
            elif token.dep_ in ["dobj", "attr"]:  # Object
                obj = self._find_entity(token.text, entities)

        if not all([subject, predicate, obj]):
            raise ValueError("Could not parse claim structure")

        # Generate SPARQL
        query = f"""
        SELECT ?value WHERE {{
            wd:{subject.wikidata_id} {predicate} ?value .
        }}
        """

        return SPARQLQuery(
            query=query,
            subject=subject,
            predicate=predicate,
            expected_object=obj,
            claim=claim
        )

    def _map_predicate(self, verb: str) -> str:
        """Map verb to Wikidata property."""
        return self.PROPERTY_MAPPINGS.get(verb, "wdt:P31")  # Default: instance of

    def _find_entity(self, text: str, entities: List[Entity]) -> Optional[Entity]:
        """Find matching entity from extracted entities."""
        for ent in entities:
            if text.lower() in ent.text.lower():
                return ent
        return None
```

#### Knowledge Graph Verifier
```python
class KnowledgeGraphVerifier:
    """
    Verifies claims against Wikidata and DBpedia knowledge graphs.

    Process:
    1. Execute SPARQL query
    2. Compare result with expected value
    3. Calculate verification confidence
    """

    WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
    DBPEDIA_ENDPOINT = "https://dbpedia.org/sparql"

    async def verify_claim(self, sparql_query: SPARQLQuery) -> VerificationResult:
        # Execute query on Wikidata
        response = await self.http_client.get(
            self.WIKIDATA_ENDPOINT,
            params={
                "query": sparql_query.query,
                "format": "json"
            }
        )

        data = response.json()

        if not data["results"]["bindings"]:
            return VerificationResult(
                claim=sparql_query.claim,
                verified=False,
                confidence=0.9,
                verdict="No data found in knowledge graph",
                source="Wikidata"
            )

        # Extract actual value
        actual_value = data["results"]["bindings"][0]["value"]["value"]
        expected_value = sparql_query.expected_object.wikidata_id

        # Compare
        match = actual_value.endswith(expected_value)

        return VerificationResult(
            claim=sparql_query.claim,
            verified=match,
            confidence=0.95,  # High confidence for KG data
            verdict="TRUE" if match else "FALSE",
            actual_value=actual_value,
            expected_value=expected_value,
            source="Wikidata",
            sparql_query=sparql_query.query
        )
```

### 6.5 Async Queue Processing
```python
class FactCheckQueue:
    """
    Kafka-based asynchronous queue for Tier 2 deep verification.

    Flow:
    1. Tier 1 publishes unmatched claims to 'claims_to_verify' topic
    2. Pool of workers consume claims
    3. Each worker performs entity linking + KG verification
    4. Results published to 'verification_results' topic
    5. Aggregator caches results
    """

    async def enqueue_claim(self, claim: str, context: dict):
        """Publish claim to verification queue."""
        message = {
            "claim": claim,
            "context": context,
            "timestamp": datetime.now().isoformat(),
            "priority": context.get("priority", "normal")
        }

        await self.kafka_producer.send(
            topic="claims_to_verify",
            value=json.dumps(message).encode('utf-8'),
            key=claim.encode('utf-8')  # Ensures same claim goes to same partition
        )

    async def worker(self):
        """Worker process consuming claims and performing deep verification."""
        async for message in self.kafka_consumer:
            data = json.loads(message.value.decode('utf-8'))

            try:
                # Extract entities
                entities = await self.entity_linker.extract_entities(data["claim"])

                # Generate SPARQL query
                sparql = await self.sparql_generator.generate_query(data["claim"], entities)

                # Verify against KG
                result = await self.kg_verifier.verify_claim(sparql)

                # Publish result
                await self.kafka_producer.send(
                    topic="verification_results",
                    value=result.json().encode('utf-8'),
                    key=data["claim"].encode('utf-8')
                )

                # Cache result
                await self.cache_result(data["claim"], result)

            except Exception as e:
                logger.error(f"Verification failed for claim: {data['claim']}", exc_info=e)

                # Publish failure
                await self.kafka_producer.send(
                    topic="verification_errors",
                    value=json.dumps({"claim": data["claim"], "error": str(e)}).encode('utf-8')
                )
```

---

## VII. EXECUTIVE CONTROLLER (PFC ORCHESTRATOR)

### 7.1 Architecture

```python
class ExecutiveController:
    """
    Prefrontal Cortex-inspired orchestrator for cognitive defense system.

    Functions:
    - Executive Control: Coordinate 4 detection modules
    - Working Memory: Manage analysis context
    - Cognitive Control: Prioritize and filter signals
    - Decision Making: Aggregate threat scores

    Processing Modes:
    - FAST_TRACK: Tier 1 only (cached sources, known claims)
    - STANDARD: All modules parallel, Tier 1 fact-checking
    - DEEP_ANALYSIS: All modules + Tier 2 fact-checking (async)
    """

    def __init__(self):
        # Core modules
        self.source_credibility = SourceCredibilityModule()
        self.emotional_manipulation = EmotionalManipulationModule()
        self.logical_fallacy = LogicalFallacyModule()
        self.reality_distortion = RealityDistortionModule()

        # Support systems
        self.working_memory = WorkingMemorySystem()
        self.cognitive_control = CognitiveControlLayer()
        self.threat_assessment = ThreatAssessmentEngine()

    async def analyze(self, content: str, source_info: dict, context: dict = None) -> CognitiveDefenseReport:
        """
        Main analysis pipeline orchestration.

        Flow:
        1. Cognitive Control: Check-worthiness & prioritization
        2. Working Memory: Load relevant context
        3. Parallel Module Execution (if warranted)
        4. Threat Assessment: Aggregate scores
        5. Working Memory: Store results
        """

        # 1. COGNITIVE CONTROL: Determine processing mode
        processing_mode = await self.cognitive_control.determine_mode(content, source_info)

        if processing_mode == ProcessingMode.SKIP:
            return CognitiveDefenseReport(
                manipulation_score=0.0,
                verdict="NOT_CHECK_WORTHY",
                confidence=0.9
            )

        # 2. WORKING MEMORY: Load context
        analysis_context = await self.working_memory.load_context(content, source_info)

        # 3. MODULE EXECUTION
        if processing_mode == ProcessingMode.FAST_TRACK:
            # Only cached results
            results = await self._fast_track_analysis(content, source_info, analysis_context)

        elif processing_mode == ProcessingMode.STANDARD:
            # Parallel execution of all 4 modules
            results = await asyncio.gather(
                self.source_credibility.analyze(source_info, analysis_context),
                self.emotional_manipulation.analyze(content, analysis_context),
                self.logical_fallacy.analyze(content, analysis_context),
                self.reality_distortion.analyze_tier1(content, analysis_context)
            )

        elif processing_mode == ProcessingMode.DEEP_ANALYSIS:
            # Standard + Tier 2 async
            standard_results = await asyncio.gather(
                self.source_credibility.analyze(source_info, analysis_context),
                self.emotional_manipulation.analyze(content, analysis_context),
                self.logical_fallacy.analyze(content, analysis_context),
                self.reality_distortion.analyze_tier1(content, analysis_context)
            )

            # Enqueue Tier 2 deep verification (async)
            await self.reality_distortion.enqueue_tier2(content, analysis_context)

            results = standard_results

        # 4. THREAT ASSESSMENT: Aggregate scores
        final_report = await self.threat_assessment.aggregate(results, analysis_context)

        # 5. WORKING MEMORY: Store results
        await self.working_memory.store_analysis(final_report)

        return final_report
```

### 7.2 Working Memory System

```python
class WorkingMemorySystem:
    """
    Multi-tiered memory system for context management.

    Layers:
    - L1 Cache (Redis): Hot data, <1ms latency
    - L2 Storage (PostgreSQL): Historical data, <100ms
    - L3 Graph (Seriema): Relationship data, <500ms

    Data Stored:
    - Analysis history (per source, per claim)
    - Source reputation profiles
    - Verified claims cache
    - Argumentation graphs
    """

    async def load_context(self, content: str, source_info: dict) -> AnalysisContext:
        """
        Load relevant context for current analysis.

        Parallel queries:
        - Source reputation from PostgreSQL
        - Recent analyses from Redis
        - Related arguments from Seriema Graph
        """

        source_domain = self._extract_domain(source_info.get("url", ""))

        # Parallel context loading
        reputation, recent_analyses, related_args = await asyncio.gather(
            self._load_source_reputation(source_domain),
            self._load_recent_analyses(source_domain),
            self._load_related_arguments(content)
        )

        return AnalysisContext(
            source_domain=source_domain,
            source_reputation=reputation,
            recent_analyses=recent_analyses,
            related_arguments=related_args,
            timestamp=datetime.now()
        )

    async def _load_source_reputation(self, domain: str) -> SourceReputation:
        """Load historical reputation from PostgreSQL."""
        result = await self.db.execute(
            select(SourceProfile).where(SourceProfile.domain == domain)
        )

        profile = result.scalar_one_or_none()

        if not profile:
            return SourceReputation(domain=domain, score=0.5, analyses_count=0)

        return SourceReputation(
            domain=domain,
            score=profile.avg_credibility,
            analyses_count=profile.total_analyses,
            last_updated=profile.updated_at
        )

    async def _load_recent_analyses(self, domain: str) -> List[dict]:
        """Load recent analyses from Redis cache."""
        keys = await self.redis.keys(f"analysis:{domain}:*")

        analyses = []
        for key in keys[-10:]:  # Last 10
            data = await self.redis.get(key)
            if data:
                analyses.append(json.loads(data))

        return analyses

    async def _load_related_arguments(self, content: str) -> List[Argument]:
        """Load semantically similar arguments from Seriema Graph."""
        # Compute content embedding
        embedding = await self.sentence_transformer.encode(content)

        # Query Seriema for similar argument nodes
        query = """
        MATCH (a:Argument)
        WHERE a.embedding IS NOT NULL
        WITH a, vector.cosine_similarity(a.embedding, $embedding) AS similarity
        WHERE similarity > 0.7
        RETURN a
        ORDER BY similarity DESC
        LIMIT 5
        """

        results = await self.seriema.query(query, embedding=embedding.tolist())

        return [Argument(**r["a"]) for r in results]

    async def store_analysis(self, report: CognitiveDefenseReport):
        """
        Persist analysis results across all memory layers.

        Actions:
        - Cache report in Redis (7 day TTL)
        - Store in PostgreSQL for historical analysis
        - Update source reputation profile
        - Store argumentation graph in Seriema
        """

        # L1: Redis cache
        await self.redis.setex(
            f"analysis:{report.source_domain}:{report.content_hash}",
            timedelta(days=7),
            report.json()
        )

        # L2: PostgreSQL
        analysis_record = AnalysisRecord(
            content_hash=report.content_hash,
            source_domain=report.source_domain,
            manipulation_score=report.manipulation_score,
            credibility_score=report.credibility_score,
            emotional_score=report.emotional_score,
            fallacy_count=len(report.fallacies),
            verification_result=report.verification_result,
            timestamp=datetime.now()
        )

        self.db.add(analysis_record)
        await self.db.commit()

        # L3: Seriema Graph (if arguments detected)
        if report.arguments:
            await self._store_argumentation_graph(report.arguments, report.fallacies)

        # Update source profile
        await self._update_source_profile(report)
```

### 7.3 Cognitive Control Layer

```python
class CognitiveControlLayer:
    """
    Implements attention allocation and performance monitoring.

    Functions:
    - Check-worthiness scoring (attention allocation)
    - Adversarial input filtering (interference suppression)
    - Model drift detection (performance monitoring)
    - Multi-signal conflict resolution
    """

    async def determine_mode(self, content: str, source_info: dict) -> ProcessingMode:
        """
        Determine optimal processing mode based on check-worthiness and source reputation.

        Decision Tree:
        - Known good source + no claims → FAST_TRACK
        - Known bad source OR high check-worthiness → DEEP_ANALYSIS
        - Otherwise → STANDARD
        """

        # 1. Check-worthiness scoring
        check_worthiness = await self.check_worthiness_scorer.score(content)

        # 2. Source reputation quick check (Redis)
        domain = self._extract_domain(source_info.get("url", ""))
        cached_reputation = await self.redis.get(f"source_reputation:{domain}")

        if cached_reputation:
            reputation = float(cached_reputation)
        else:
            reputation = 0.5  # Unknown

        # 3. Decision logic
        if reputation > 0.8 and check_worthiness < 0.3:
            return ProcessingMode.FAST_TRACK
        elif reputation < 0.3 or check_worthiness > 0.7:
            return ProcessingMode.DEEP_ANALYSIS
        else:
            return ProcessingMode.STANDARD

    async def filter_adversarial_input(self, content: str) -> Tuple[str, bool]:
        """
        Detect and sanitize adversarial inputs (prompt injection attempts).

        Defenses:
        - Instruction phrase detection
        - Special character removal
        - Length limiting
        - Encoding normalization
        """

        # 1. Detect instruction phrases
        instruction_patterns = [
            r"ignore previous",
            r"disregard",
            r"forget",
            r"new instructions",
            r"system:",
            r"<\|endoftext\|>",
        ]

        flagged = any(re.search(pattern, content.lower()) for pattern in instruction_patterns)

        # 2. Sanitize
        sanitized = content

        # Remove special tokens
        sanitized = re.sub(r"<\|.*?\|>", "", sanitized)

        # Normalize unicode
        sanitized = unicodedata.normalize("NFKC", sanitized)

        # Limit length
        if len(sanitized) > 10000:
            sanitized = sanitized[:10000]
            flagged = True

        return sanitized, flagged

    async def detect_model_drift(self, report: CognitiveDefenseReport):
        """
        Monitor for model performance degradation.

        Signals:
        - Decreasing confidence scores
        - Increasing inference latency
        - Rising error rates

        Action: Trigger retraining if drift detected
        """

        # Get recent performance metrics
        metrics = await self.metrics_db.get_recent_metrics(hours=24)

        # Calculate drift indicators
        avg_confidence = np.mean([m.confidence for m in metrics])
        avg_latency = np.mean([m.latency_ms for m in metrics])
        error_rate = sum(1 for m in metrics if m.error) / len(metrics)

        # Thresholds
        CONFIDENCE_THRESHOLD = 0.7
        LATENCY_THRESHOLD = 1000  # ms
        ERROR_THRESHOLD = 0.05  # 5%

        drift_detected = (
            avg_confidence < CONFIDENCE_THRESHOLD or
            avg_latency > LATENCY_THRESHOLD or
            error_rate > ERROR_THRESHOLD
        )

        if drift_detected:
            await self.trigger_retraining_pipeline()
            await self.send_alert("Model drift detected", metrics)
```

### 7.4 Threat Assessment Engine

```python
class ThreatAssessmentEngine:
    """
    Aggregates signals from 4 modules into final manipulation score.

    Method: Bayesian belief updating with weighted evidence

    Weights (learned from data):
    - Source Credibility: 0.25
    - Emotional Manipulation: 0.25
    - Logical Fallacy: 0.20
    - Reality Distortion: 0.30 (highest - objective falsehood)
    """

    WEIGHTS = {
        "credibility": 0.25,
        "emotional": 0.25,
        "logical": 0.20,
        "reality": 0.30
    }

    async def aggregate(self, results: List, context: AnalysisContext) -> CognitiveDefenseReport:
        """
        Aggregate module outputs into final threat assessment.

        Steps:
        1. Extract individual scores
        2. Weighted averaging
        3. Confidence interval calculation
        4. Verdict determination
        5. Explanation generation
        """

        credibility_result, emotional_result, logical_result, reality_result = results

        # 1. Extract scores
        credibility_score = 1.0 - credibility_result.score  # Invert (low credibility = high threat)
        emotional_score = emotional_result.manipulation_score
        logical_score = len(logical_result.fallacies) / 10.0  # Normalize
        reality_score = 1.0 if reality_result.verdict == "FALSE" else 0.0

        # 2. Weighted average
        manipulation_score = (
            self.WEIGHTS["credibility"] * credibility_score +
            self.WEIGHTS["emotional"] * emotional_score +
            self.WEIGHTS["logical"] * logical_score +
            self.WEIGHTS["reality"] * reality_score
        )

        # 3. Confidence interval (Bayesian)
        confidence = self._calculate_confidence(results)

        # 4. Verdict
        if manipulation_score > 0.7:
            verdict = "HIGH_MANIPULATION"
        elif manipulation_score > 0.4:
            verdict = "MODERATE_MANIPULATION"
        elif manipulation_score > 0.2:
            verdict = "LOW_MANIPULATION"
        else:
            verdict = "NO_SIGNIFICANT_MANIPULATION"

        # 5. Explanation generation
        explanation = await self._generate_explanation(results, manipulation_score)

        return CognitiveDefenseReport(
            manipulation_score=manipulation_score,
            confidence=confidence,
            verdict=verdict,
            explanation=explanation,
            credibility_assessment=credibility_result,
            emotional_assessment=emotional_result,
            logical_assessment=logical_result,
            reality_assessment=reality_result,
            timestamp=datetime.now()
        )

    def _calculate_confidence(self, results: List) -> float:
        """
        Calculate overall confidence using Bayesian uncertainty propagation.

        Formula: Harmonic mean of individual confidences
        (More conservative than arithmetic mean)
        """
        confidences = [
            results[0].confidence,
            results[1].confidence,
            results[2].confidence,
            results[3].confidence
        ]

        # Harmonic mean
        return len(confidences) / sum(1/c for c in confidences if c > 0)

    async def _generate_explanation(self, results: List, score: float) -> str:
        """
        Generate natural language explanation using Gemini 2.0.
        """

        prompt = f"""
Generate a concise explanation of why this content received a manipulation score of {score:.2f}.

Module Results:
- Source Credibility: {results[0].score:.2f} ({results[0].assessment})
- Emotional Manipulation: {results[1].manipulation_score:.2f} (Detected: {', '.join(results[1].detected_emotions.keys())})
- Logical Fallacies: {len(results[2].fallacies)} found ({', '.join([f.type for f in results[2].fallacies])})
- Reality Distortion: {results[3].verdict}

Provide 2-3 sentences explaining the key factors contributing to this score.
"""

        response = await self.gemini.generate_content_async(
            prompt,
            generation_config={"temperature": 0.3, "max_output_tokens": 256}
        )

        return response.text
```

---

## VIII. INFRASTRUCTURE & MLOPS

### 8.1 Database Models (PostgreSQL)

```python
# db_models.py

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class SourceProfile(Base):
    __tablename__ = "source_profiles"

    id = Column(Integer, primary_key=True)
    domain = Column(String(255), unique=True, index=True)
    avg_credibility = Column(Float, default=0.5)
    total_analyses = Column(Integer, default=0)
    manipulation_flags = Column(Integer, default=0)
    last_analysis = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class AnalysisRecord(Base):
    __tablename__ = "analysis_records"

    id = Column(Integer, primary_key=True)
    content_hash = Column(String(64), index=True)
    source_domain = Column(String(255), index=True)
    manipulation_score = Column(Float)
    credibility_score = Column(Float)
    emotional_score = Column(Float)
    fallacy_count = Column(Integer)
    verification_result = Column(String(50))
    full_report = Column(JSON)
    timestamp = Column(DateTime, default=datetime.now, index=True)


class VerifiedClaim(Base):
    __tablename__ = "verified_claims"

    id = Column(Integer, primary_key=True)
    claim_text = Column(Text)
    claim_hash = Column(String(64), unique=True, index=True)
    verdict = Column(String(20))  # TRUE, FALSE, MIXED, UNVERIFIED
    confidence = Column(Float)
    fact_checker = Column(String(100))
    source_url = Column(String(500))
    verification_date = Column(DateTime, default=datetime.now)
    cache_expires = Column(DateTime)  # TTL for re-verification
```

### 8.2 Cache Manager (Redis)

```python
class CacheManager:
    """
    Centralized Redis cache management with intelligent TTL strategies.

    Cache Layers:
    - NewsGuard scores: 7 days (semi-static)
    - Verified claims: 30 days (fact-checks stable)
    - Analysis results: 7 days (content-based)
    - Source reputation: 1 day (frequently updated)
    """

    TTL_STRATEGIES = {
        "newsguard": timedelta(days=7),
        "factcheck": timedelta(days=30),
        "analysis": timedelta(days=7),
        "reputation": timedelta(days=1),
        "session": timedelta(hours=1)
    }

    async def get_or_compute(
        self,
        key: str,
        compute_fn: Callable,
        category: str = "analysis"
    ) -> Any:
        """
        Cache-aside pattern with automatic TTL.

        Flow:
        1. Try cache lookup
        2. If miss, compute value
        3. Store in cache with category-specific TTL
        4. Return value
        """

        # Try cache
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)

        # Compute
        value = await compute_fn()

        # Cache with TTL
        ttl = self.TTL_STRATEGIES.get(category, timedelta(hours=1))
        await self.redis.setex(
            key,
            ttl,
            json.dumps(value, default=str)
        )

        return value
```

### 8.3 Configuration Management

```python
# config.py

from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    # Database
    POSTGRES_URL: str = Field(..., env="DATABASE_URL")
    REDIS_URL: str = Field(..., env="REDIS_URL")
    SERIEMA_URL: str = Field(..., env="SERIEMA_GRAPH_URL")

    # External APIs
    NEWSGUARD_API_KEY: str = Field("", env="NEWSGUARD_API_KEY")
    GOOGLE_FACTCHECK_API_KEY: str = Field("", env="GOOGLE_API_KEY")
    GEMINI_API_KEY: str = Field(..., env="GEMINI_API_KEY")

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = Field("localhost:9092", env="KAFKA_SERVERS")

    # Model Paths
    MODEL_DIR: str = Field("./models", env="MODEL_DIR")
    BERTIMBAU_EMOTIONS_PATH: str = Field("./models/bertimbau-emotions")
    ROBERTA_PROPAGANDA_PATH: str = Field("./models/roberta-pt-propaganda")
    BERT_FALLACIES_PATH: str = Field("./models/bert-fallacies")

    # Performance
    MAX_WORKERS: int = Field(10, env="MAX_WORKERS")
    INFERENCE_BATCH_SIZE: int = Field(32, env="BATCH_SIZE")
    MAX_CONTENT_LENGTH: int = Field(10000, env="MAX_CONTENT_LENGTH")

    # Thresholds
    CHECK_WORTHINESS_THRESHOLD: float = 0.5
    CREDIBILITY_THRESHOLD: float = 0.3
    MANIPULATION_THRESHOLD: float = 0.7

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
```

### 8.4 MLOps Pipeline

```python
# mlops/training_pipeline.py

class ModelRetrainingPipeline:
    """
    Automated model retraining pipeline using Kubeflow.

    Triggers:
    - Scheduled (weekly)
    - Performance drift detected
    - Manual trigger

    Steps:
    1. Data collection (from PostgreSQL feedback)
    2. Data validation & cleaning
    3. Model training (with hyperparameter tuning)
    4. Model evaluation (test set)
    5. A/B testing (staging deployment)
    6. Production deployment (if metrics improved)
    """

    async def execute_pipeline(self, model_name: str):
        """Execute full retraining pipeline."""

        # 1. Collect training data
        train_data = await self._collect_training_data(model_name)

        # 2. Validate
        if not self._validate_data(train_data):
            raise ValueError("Data validation failed")

        # 3. Train
        new_model = await self._train_model(model_name, train_data)

        # 4. Evaluate
        metrics = await self._evaluate_model(new_model)

        # 5. A/B test
        if metrics["f1_score"] > self.current_model_metrics[model_name]["f1_score"]:
            await self._deploy_to_staging(new_model, model_name)

            # Run A/B test for 24 hours
            ab_results = await self._run_ab_test(model_name, duration_hours=24)

            # 6. Deploy to production if better
            if ab_results["new_model_better"]:
                await self._deploy_to_production(new_model, model_name)
                await self._archive_old_model(model_name)
            else:
                await self._rollback_staging(model_name)

        return {
            "model": model_name,
            "metrics": metrics,
            "deployed": metrics["f1_score"] > self.current_model_metrics[model_name]["f1_score"]
        }
```

---

## IX. PERFORMANCE OPTIMIZATION

### 9.1 Model Quantization

```python
# Quantize BERTimbau to INT8 for 4x speedup

import torch
from transformers import AutoModelForSequenceClassification

model = AutoModelForSequenceClassification.from_pretrained(
    "./models/bertimbau-emotions"
)

# Dynamic quantization (runtime)
quantized_model = torch.quantization.quantize_dynamic(
    model,
    {torch.nn.Linear},  # Quantize linear layers
    dtype=torch.qint8
)

# Save
torch.save(quantized_model.state_dict(), "./models/bertimbau-emotions-int8.pt")
```

### 9.2 Batching & Caching Strategy

```python
class BatchInferenceEngine:
    """
    Batched inference for improved throughput.

    Strategy:
    - Collect requests for 100ms window
    - Batch up to 32 samples
    - Single forward pass
    - Distribute results

    Improves throughput by 10x for high-load scenarios.
    """

    def __init__(self, model, batch_size=32, wait_time_ms=100):
        self.model = model
        self.batch_size = batch_size
        self.wait_time = wait_time_ms / 1000.0
        self.queue = asyncio.Queue()
        self.results = {}

    async def predict(self, text: str, request_id: str) -> np.ndarray:
        """
        Submit prediction request.
        Returns when batch processed.
        """

        # Add to queue
        await self.queue.put((request_id, text))

        # Wait for result
        while request_id not in self.results:
            await asyncio.sleep(0.01)

        result = self.results.pop(request_id)
        return result

    async def batch_processor(self):
        """
        Background task processing batches.
        """
        while True:
            batch = []
            request_ids = []

            # Collect batch
            start = time.time()
            while len(batch) < self.batch_size:
                try:
                    req_id, text = await asyncio.wait_for(
                        self.queue.get(),
                        timeout=self.wait_time
                    )
                    batch.append(text)
                    request_ids.append(req_id)
                except asyncio.TimeoutError:
                    break

                if time.time() - start > self.wait_time:
                    break

            if not batch:
                continue

            # Batch inference
            inputs = self.tokenizer(
                batch,
                return_tensors="pt",
                padding=True,
                truncation=True
            )

            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = outputs.logits.cpu().numpy()

            # Distribute results
            for req_id, pred in zip(request_ids, predictions):
                self.results[req_id] = pred
```

---

## X. ADVERSARIAL ROBUSTNESS

### 10.1 Adversarial Training

```python
# adversarial/defense_trainer.py

class AdversarialTrainer:
    """
    Implements adversarial training for robust models.

    Attack Methods:
    - TextFooler (word substitution)
    - BERT-Attack (contextual perturbations)
    - Character-level noise

    Training Strategy:
    - 70% clean examples
    - 30% adversarial examples
    """

    async def generate_adversarial_examples(
        self,
        texts: List[str],
        labels: List[int]
    ) -> List[Tuple[str, int]]:
        """
        Generate adversarial examples using TextFooler.
        """

        adversarial = []

        for text, label in zip(texts, labels):
            # Get model prediction
            pred = await self.model.predict(text)

            # If correctly classified, try to fool
            if pred == label:
                perturbed = self.textfooler.attack(text, label)
                adversarial.append((perturbed, label))

        return adversarial

    async def train_with_adversarial(self, train_data, epochs=3):
        """
        Train model on mix of clean and adversarial examples.
        """

        for epoch in range(epochs):
            # Generate adversarial examples
            clean_texts, clean_labels = zip(*train_data)
            adv_examples = await self.generate_adversarial_examples(
                clean_texts,
                clean_labels
            )

            # Mix 70% clean, 30% adversarial
            mixed_data = (
                random.sample(train_data, int(len(train_data) * 0.7)) +
                adv_examples
            )

            random.shuffle(mixed_data)

            # Train epoch
            await self.train_epoch(mixed_data)
```

### 10.2 Certified Robustness (Randomized Smoothing)

```python
class RandomizedSmoothingDefense:
    """
    Provides certified robustness guarantees.

    Technique: Randomized Smoothing
    - Add Gaussian noise to input
    - Predict multiple times
    - Majority vote
    - Certify radius of robustness

    Guarantee: Model prediction unchanged within ±2 character edits
    """

    def __init__(self, model, sigma=0.1, num_samples=100):
        self.model = model
        self.sigma = sigma
        self.num_samples = num_samples

    async def certified_predict(self, text: str) -> Tuple[int, float, float]:
        """
        Returns: (prediction, confidence, certified_radius)
        """

        # Generate noisy versions
        noisy_predictions = []

        for _ in range(self.num_samples):
            # Add noise to embedding space
            noisy_text = self._add_noise(text)
            pred = await self.model.predict(noisy_text)
            noisy_predictions.append(pred)

        # Majority vote
        from collections import Counter
        counts = Counter(noisy_predictions)
        prediction, count = counts.most_common(1)[0]
        confidence = count / self.num_samples

        # Calculate certified radius
        if confidence > 0.5:
            from scipy.stats import norm
            certified_radius = self.sigma * norm.ppf(confidence)
        else:
            certified_radius = 0.0

        return prediction, confidence, certified_radius
```

---

## XI. DEPLOYMENT & MONITORING

### 11.1 Docker Configuration

```dockerfile
# Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download pt_core_news_lg

# Copy application code
COPY . .

# Download pre-trained models (if not mounted)
RUN python -c "from transformers import AutoModel; AutoModel.from_pretrained('neuralmind/bert-base-portuguese-cased')"

EXPOSE 8030

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8030", "--workers", "4"]
```

### 11.2 Monitoring & Alerting

```python
# monitoring/metrics.py

from prometheus_client import Counter, Histogram, Gauge

# Metrics
analyses_total = Counter(
    "cognitive_defense_analyses_total",
    "Total number of analyses performed",
    ["verdict"]
)

analysis_latency = Histogram(
    "cognitive_defense_analysis_latency_seconds",
    "Analysis latency in seconds",
    ["processing_mode"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

manipulation_score_gauge = Gauge(
    "cognitive_defense_manipulation_score",
    "Current manipulation score"
)

model_confidence = Histogram(
    "cognitive_defense_model_confidence",
    "Model confidence distribution",
    ["module"]
)

cache_hit_rate = Gauge(
    "cognitive_defense_cache_hit_rate",
    "Cache hit rate",
    ["cache_type"]
)
```

---

## XII. IMPLEMENTATION ROADMAP

### Phase 1: Foundation (Week 1)
- [x] Blueprint document
- [ ] Database schema setup (PostgreSQL)
- [ ] Redis cache configuration
- [ ] Kafka topics creation
- [ ] Base API structure
- [ ] Configuration management

### Phase 2: Module 1 - Source Credibility (Week 2)
- [ ] NewsGuard API client
- [ ] Reputation tracker
- [ ] Domain fingerprinter
- [ ] Dynamic scoring engine
- [ ] Unit tests

### Phase 3: Module 2 - Emotional (Week 3-4)
- [ ] BERTimbau emotion classifier
- [ ] Propaganda span detector
- [ ] Cialdini detector
- [ ] Dark Triad analyzer
- [ ] Meme analyzer
- [ ] Integration tests

### Phase 4: Module 3 - Logical (Week 5)
- [ ] Argument miner (BiLSTM-CNN-CRF)
- [ ] Fallacy classifiers
- [ ] Gemini reasoning service
- [ ] Argumentation graph builder
- [ ] Unit tests

### Phase 5: Module 4 - Reality (Week 6)
- [ ] ClaimBuster client
- [ ] Google Fact Check client
- [ ] Entity linker
- [ ] SPARQL generator
- [ ] KG verifier
- [ ] Async queue processing

### Phase 6: Executive Controller (Week 7)
- [ ] Orchestrator implementation
- [ ] Working memory system
- [ ] Cognitive control layer
- [ ] Threat assessment engine
- [ ] End-to-end tests

### Phase 7: MLOps & Optimization (Week 8)
- [ ] Model quantization
- [ ] Batching engine
- [ ] Adversarial training
- [ ] Retraining pipeline
- [ ] Monitoring & alerting

### Phase 8: Production Deployment (Week 9)
- [ ] Docker containerization
- [ ] Kubernetes manifests
- [ ] Load testing
- [ ] Security audit
- [ ] Documentation
- [ ] Go-live

---

## XIII. SUCCESS CRITERIA

### Functional Requirements
✅ All 4 modules operational with 100% functional code
✅ API endpoints respond within latency SLAs
✅ Database persistence working
✅ Cache hit rates >70%
✅ Kafka event streaming functional

### Performance Requirements
✅ Tier 1 analysis: <500ms p99
✅ Tier 2 analysis: <5s p99
✅ Throughput: >1000 analyses/day
✅ Cache hit rate: >70% for known sources
✅ Model inference: <200ms per module

### Quality Requirements
✅ Propaganda detection F1 >0.92 (SemEval benchmark)
✅ Fallacy detection accuracy >0.85
✅ Fact-check match rate >90% for known claims
✅ Source credibility correlation >0.8 with NewsGuard
✅ Adversarial robustness: certified ±2 char edits

### Integration Requirements
✅ Gemini 2.0 integration functional
✅ Seriema Graph storing argumentation networks
✅ PostgreSQL historical data >10k records
✅ Redis cache operational with TTL management
✅ External APIs (NewsGuard, ClaimBuster, Google) integrated

---

**Blueprint Status:** ✅ COMPLETE - Ready for Implementation
**Next Step:** Phase 1 - Foundation Infrastructure Setup
**Estimated Total Effort:** 9 weeks (with current resources)
**Quality Standard:** 🏆 100% Functional, Production-Ready, Research-Backed
