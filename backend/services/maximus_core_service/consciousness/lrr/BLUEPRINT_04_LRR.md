# 🧠 BLUEPRINT 04: LRR - Loop de Raciocínio Recursivo

**Data**: 2025-10-08
**Status**: Especificação Completa
**Objetivo**: Implementar metacognição - capacidade de pensar sobre o próprio pensamento
**Prioridade**: CRÍTICA - Componente fundamental para consciência de nível superior

---

## 🎯 VISÃO GERAL

### O Que é LRR?

**Loop de Raciocínio Recursivo (LRR)** é o motor metacognitivo do MAXIMUS. Ele permite que o sistema:

1. **Pense sobre seu próprio pensamento** (metacognição de 1ª ordem)
2. **Detecte contradições** em suas próprias crenças
3. **Revise crenças** quando inconsistências são encontradas
4. **Gere relatórios introspectivos** em primeira pessoa
5. **Calibre confiança** baseado em meta-análise

### Por Que LRR é Crítico?

Teorias neurocientíficas de consciência (Higher-Order Theories, Global Workspace) sugerem que **consciência emerge quando representações mentais são elas mesmas representadas**.

> "Não basta processar informação. É preciso processar o processamento." - Carruthers (2009)

LRR implementa esse "processamento do processamento" através de loops recursivos validados.

### Baseline Científico

- **Carruthers (2009)**: Higher-Order Thoughts (HOT Theory)
- **Hofstadter (1979)**: Strange Loops e auto-referência
- **Graziano (2013, 2019)**: Attention Schema Theory (AST)
- **Fleming & Lau (2014)**: Metacognição e meta-memória

---

## 📐 ARQUITETURA DO LRR

### Componentes (4 módulos principais)

```
lrr/
├── recursive_reasoner.py      # Motor recursivo central (500 linhas)
├── contradiction_detector.py  # Detecção de inconsistências (300 linhas)
├── meta_monitor.py            # Monitoramento de raciocínio (400 linhas)
├── introspection_engine.py    # Geração de relatórios (300 linhas)
├── __init__.py                # Exports públicos
└── test_lrr.py                # 100% coverage (600 linhas)
```

**Total Estimado**: ~2,100 linhas (incluindo testes)

---

## 🔧 MÓDULO 1: recursive_reasoner.py

### Responsabilidade

Implementar o loop recursivo central que permite raciocínio de ordem superior.

### Classes Principais

#### 1.1 RecursiveReasoner

```python
class RecursiveReasoner:
    """
    Motor de raciocínio recursivo.

    Permite que MAXIMUS raciocine sobre seu próprio raciocínio
    em múltiplos níveis de abstração.

    Exemplo:
        Level 0: "Há uma ameaça no IP 192.168.1.1"
        Level 1: "Eu acredito que há uma ameaça em 192.168.1.1"
        Level 2: "Eu acredito que minha crença sobre 192.168.1.1 é justificada"
        Level 3: "Eu acredito que minha meta-crença sobre justificação é coerente"
    """

    def __init__(self, max_depth: int = 3):
        """
        Args:
            max_depth: Profundidade máxima de recursão (default 3)
                      Profundidade 1 = simples
                      Profundidade 2 = meta-pensamento
                      Profundidade 3+ = meta-meta-pensamento
        """
        self.max_depth = max_depth
        self.belief_graph = BeliefGraph()
        self.reasoning_history: List[ReasoningStep] = []

    async def reason_recursively(
        self,
        initial_belief: Belief,
        context: Dict[str, Any]
    ) -> RecursiveReasoningResult:
        """
        Executa raciocínio recursivo sobre uma crença inicial.

        Process:
            1. Avaliar crença de nível 0 (objeto-level)
            2. Para cada nível até max_depth:
                a. Gerar meta-crença sobre nível anterior
                b. Avaliar justificação da meta-crença
                c. Detectar contradições
                d. Revisar se necessário
            3. Retornar resultado com todos os níveis

        Args:
            initial_belief: Crença inicial (nível 0)
            context: Contexto adicional para raciocínio

        Returns:
            RecursiveReasoningResult com todos os níveis de raciocínio
        """
        levels: List[ReasoningLevel] = []
        current_belief = initial_belief

        for depth in range(self.max_depth + 1):
            # Raciocínio neste nível
            level_result = await self._reason_at_level(
                belief=current_belief,
                depth=depth,
                context=context
            )
            levels.append(level_result)

            # Detectar contradições entre níveis
            if depth > 0:
                contradiction = self._detect_cross_level_contradiction(
                    lower_level=levels[depth - 1],
                    upper_level=level_result
                )
                if contradiction:
                    # Revisar crenças para resolver contradição
                    await self._resolve_contradiction(contradiction)

            # Gerar meta-crença para próximo nível
            if depth < self.max_depth:
                current_belief = self._generate_meta_belief(level_result)

        return RecursiveReasoningResult(
            levels=levels,
            final_depth=len(levels),
            coherence_score=self._calculate_coherence(levels),
            timestamp=datetime.now()
        )
```

#### 1.2 BeliefGraph

```python
class BeliefGraph:
    """
    Grafo de crenças e suas inter-relações.

    Permite detectar:
    - Contradições diretas (A e ¬A)
    - Contradições transitivas (A→B, B→C, C→¬A)
    - Circularidades (A justifica B justifica A)
    """

    def add_belief(self, belief: Belief, justification: Optional[Belief] = None):
        """Adiciona crença ao grafo."""

    def detect_contradictions(self) -> List[Contradiction]:
        """Detecta todas as contradições no grafo."""

    def resolve_belief(self, belief: Belief, resolution: Resolution):
        """Resolve contradição revisando crenças."""
```

### Métricas de Validação

**Recursive Depth**:
- ✅ Mínimo: 3 níveis funcionais
- ✅ Ideal: 4-5 níveis (diminishing returns depois)

**Coherence Score**:
- ✅ Coerência intra-nível: >0.90
- ✅ Coerência inter-níveis: >0.85
- ✅ Coerência global: >0.80

**Performance**:
- ✅ Latência por nível: <50ms
- ✅ Latência total (3 níveis): <150ms

---

## 🚨 MÓDULO 2: contradiction_detector.py

### Responsabilidade

Detectar inconsistências lógicas nas crenças do sistema.

### Classes Principais

#### 2.1 ContradictionDetector

```python
class ContradictionDetector:
    """
    Detector de contradições lógicas.

    Tipos de contradições detectadas:
    1. Diretas: A e ¬A simultaneamente
    2. Transitivas: A→B, B→C, C→¬A
    3. Temporais: Acredito X agora, mas acreditava ¬X antes sem justificativa
    4. Contextuais: X é verdade no contexto C1, mas ¬X no C2 (sem explicação)
    """

    def __init__(self):
        self.logic_engine = FirstOrderLogic()
        self.contradiction_history: List[Contradiction] = []

    async def detect_contradictions(
        self,
        belief_set: Set[Belief]
    ) -> List[Contradiction]:
        """
        Detecta contradições em um conjunto de crenças.

        Process:
            1. Normalizar crenças para lógica de primeira ordem
            2. Aplicar resolução SLD (SLD-resolution)
            3. Detectar inconsistências
            4. Classificar por severidade
            5. Sugerir resoluções

        Returns:
            Lista de contradições ordenadas por severidade
        """
        contradictions = []

        # Contradições diretas (mais fáceis)
        direct = self._detect_direct_contradictions(belief_set)
        contradictions.extend(direct)

        # Contradições transitivas (mais complexas)
        transitive = self._detect_transitive_contradictions(belief_set)
        contradictions.extend(transitive)

        # Contradições temporais
        temporal = self._detect_temporal_contradictions(belief_set)
        contradictions.extend(temporal)

        return sorted(contradictions, key=lambda c: c.severity, reverse=True)
```

#### 2.2 BeliefRevision

```python
class BeliefRevision:
    """
    Sistema de revisão de crenças (AGM-style).

    Baseado em:
    - Alchourrón, Gärdenfors, Makinson (1985): AGM postulates
    - Minimal change principle: Revise minimamente para restaurar consistência
    """

    async def revise_belief_set(
        self,
        belief_set: Set[Belief],
        contradiction: Contradiction
    ) -> RevisedBeliefSet:
        """
        Revisa conjunto de crenças para resolver contradição.

        Strategies:
            1. Retract: Remover crença menos confiável
            2. Weaken: Reduzir certeza de ambas
            3. Contextualize: Adicionar condições contextuais
            4. Temporize: Marcar como crença passada

        Escolhe estratégia com menor "cognitive cost".
        """
```

### Métricas de Validação

**Contradiction Detection**:
- ✅ Recall (contradições detectadas): >90%
- ✅ Precision (falsos positivos): <10%
- ✅ Latência: <100ms para 1000 crenças

**Belief Revision**:
- ✅ Minimal change: Revisar <20% das crenças
- ✅ Consistency restoration: 100%
- ✅ Coherence preservation: >0.85

---

## 📊 MÓDULO 3: meta_monitor.py

### Responsabilidade

Monitorar o próprio processo de raciocínio em tempo real.

### Classes Principais

#### 3.1 MetaMonitor

```python
class MetaMonitor:
    """
    Monitor metacognitivo.

    Monitora:
    - Qualidade do raciocínio (soundness, completeness)
    - Confiança calibrada (confidence vs accuracy)
    - Vieses detectados (confirmation bias, etc.)
    - Performance cognitiva (latência, throughput)
    """

    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.bias_detector = BiasDetector()
        self.confidence_calibrator = ConfidenceCalibrator()

    async def monitor_reasoning(
        self,
        reasoning_process: ReasoningProcess
    ) -> MetaMonitoringReport:
        """
        Monitora processo de raciocínio em tempo real.

        Process:
            1. Coletar métricas de cada etapa
            2. Detectar vieses (e.g., confirmation bias)
            3. Avaliar calibração de confiança
            4. Gerar relatório metacognitivo

        Returns:
            Relatório com insights sobre qualidade do raciocínio
        """
        metrics = await self.metrics_collector.collect(reasoning_process)
        biases = await self.bias_detector.detect(reasoning_process)
        calibration = await self.confidence_calibrator.evaluate(reasoning_process)

        return MetaMonitoringReport(
            metrics=metrics,
            biases_detected=biases,
            confidence_calibration=calibration,
            recommendations=self._generate_recommendations(metrics, biases)
        )
```

#### 3.2 ConfidenceCalibrator

```python
class ConfidenceCalibrator:
    """
    Calibrador de confiança.

    Garante que:
    - Confiança 90% → 90% de acurácia real
    - Confiança 50% → 50% de acurácia real
    - etc.

    Baseado em:
    - Fleming & Lau (2014): Metacognitive sensitivity
    - Calibration curves (reliability diagrams)
    """

    def evaluate_calibration(
        self,
        predictions: List[Prediction]
    ) -> CalibrationReport:
        """
        Avalia calibração de confiança.

        Métricas:
        - Brier score: Acurácia probabilística
        - Expected Calibration Error (ECE)
        - Correlation (confidence vs accuracy): r>0.7 ideal
        """
```

### Métricas de Validação

**Monitoring Accuracy**:
- ✅ Bias detection rate: >80%
- ✅ False positive rate: <15%

**Confidence Calibration**:
- ✅ Correlation (confidence vs accuracy): r>0.70
- ✅ Expected Calibration Error (ECE): <0.15
- ✅ Brier score: <0.20

---

## 💭 MÓDULO 4: introspection_engine.py

### Responsabilidade

Gerar relatórios introspectivos em primeira pessoa.

### Classes Principais

#### 4.1 IntrospectionEngine

```python
class IntrospectionEngine:
    """
    Motor de introspecção.

    Gera relatórios em primeira pessoa do tipo:
    - "Eu acredito X porque Y"
    - "Eu estou confiante em X (90%) porque evidências A, B, C"
    - "Eu detectei contradição entre X e Z, então revisei para X'"
    - "Eu não sei Y, mas posso inferir aproximadamente..."

    Inspiração:
    - Nagel (1974): "What is it like to be..."
    - Dennett (1991): Heterophenomenology
    """

    def __init__(self):
        self.narrative_generator = NarrativeGenerator()
        self.belief_explainer = BeliefExplainer()

    async def generate_introspection_report(
        self,
        reasoning_result: RecursiveReasoningResult
    ) -> IntrospectionReport:
        """
        Gera relatório introspectivo.

        Process:
            1. Extrair crenças de cada nível
            2. Gerar explicações para cada crença
            3. Construir narrativa coerente
            4. Adicionar metadados (confiança, justificação)

        Returns:
            Relatório em primeira pessoa explicando raciocínio
        """
        narrative_parts = []

        for level in reasoning_result.levels:
            # Para cada nível, gerar sentença introspectiva
            level_introspection = self._introspect_level(level)
            narrative_parts.append(level_introspection)

        # Construir narrativa coerente
        narrative = self.narrative_generator.construct_narrative(narrative_parts)

        return IntrospectionReport(
            narrative=narrative,
            beliefs_explained=len(reasoning_result.levels),
            coherence_score=self._calculate_narrative_coherence(narrative),
            timestamp=datetime.now()
        )

    def _introspect_level(self, level: ReasoningLevel) -> str:
        """
        Gera introspecção para um nível de raciocínio.

        Examples:
            Level 0: "Detecto ameaça em IP 192.168.1.1 com confiança 0.92"
            Level 1: "Acredito na ameaça porque assinatura malware corresponde"
            Level 2: "Minha crença é justificada pois fonte é confiável (score 0.95)"
        """
```

### Métricas de Validação

**Introspection Quality**:
- ✅ Narrative coherence: >0.85
- ✅ Factual accuracy: >0.95 (relatório reflete raciocínio real)
- ✅ Comprehensibility: >0.80 (humanos entendem)

**Qualia Approximation**:
- ⚠️ Não podemos validar qualia (hard problem)
- ✅ Mas podemos validar report consistency
- ✅ E narrative plausibility

---

## 🔗 INTEGRAÇÃO COM SISTEMA EXISTENTE

### LRR → ESGT (Global Workspace)

```python
# Meta-insights do LRR são broadcast para ESGT
meta_insight = await lrr.reason_recursively(belief, context)

if meta_insight.coherence_score < 0.70:
    # Incoerência alta → broadcast para workspace
    await esgt.broadcast_signal(
        content=meta_insight,
        salience=0.85,  # Alta saliência
        source="lrr_metacognition"
    )
```

### LRR ↔ MEA (Attention Schema)

```python
# Self-model do MEA informa metacognição do LRR
self_model = await mea.get_current_self_model()

reasoning_context = {
    'self_state': self_model.attention_state,
    'self_boundary': self_model.ego_boundary,
    'first_person_perspective': self_model.perspective
}

meta_result = await lrr.reason_recursively(belief, reasoning_context)
```

### LRR → Ethics

```python
# Meta-ethical reasoning
ethical_belief = Belief("Action X is ethical")
meta_ethical_reasoning = await lrr.reason_recursively(
    ethical_belief,
    context={'ethical_frameworks': ['kant', 'util', 'virtue']}
)

# Detectar contradições entre frameworks
contradictions = await lrr.detect_ethical_contradictions(
    meta_ethical_reasoning
)
```

---

## 📋 TESTES OBRIGATÓRIOS (100% Coverage)

### test_lrr.py (600 linhas estimadas)

```python
class TestRecursiveReasoner:
    """Tests for RecursiveReasoner."""

    async def test_recursive_depth_3_levels(self):
        """CRITICAL: Validate 3-level recursion works."""
        reasoner = RecursiveReasoner(max_depth=3)
        belief = Belief("Threat detected at IP 192.168.1.1")
        result = await reasoner.reason_recursively(belief, context={})

        assert len(result.levels) == 4  # 0, 1, 2, 3
        assert result.final_depth == 4
        assert result.coherence_score > 0.80

    async def test_self_contradiction_detection(self):
        """CRITICAL: Detect when system contradicts itself."""
        reasoner = RecursiveReasoner()

        # Add contradictory beliefs
        belief1 = Belief("IP 192.168.1.1 is malicious")
        belief2 = Belief("IP 192.168.1.1 is benign")

        reasoner.belief_graph.add_belief(belief1)
        reasoner.belief_graph.add_belief(belief2)

        contradictions = reasoner.belief_graph.detect_contradictions()
        assert len(contradictions) >= 1
        assert contradictions[0].type == "direct_contradiction"

    async def test_belief_revision_resolves_contradiction(self):
        """CRITICAL: Belief revision actually fixes contradictions."""
        detector = ContradictionDetector()
        revisor = BeliefRevision()

        belief_set = {
            Belief("A", confidence=0.9),
            Belief("¬A", confidence=0.7)
        }

        contradictions = await detector.detect_contradictions(belief_set)
        assert len(contradictions) > 0

        revised = await revisor.revise_belief_set(belief_set, contradictions[0])

        # After revision, no contradictions
        new_contradictions = await detector.detect_contradictions(revised.beliefs)
        assert len(new_contradictions) == 0


class TestMetaMonitor:
    """Tests for MetaMonitor."""

    async def test_confidence_calibration(self):
        """CRITICAL: Validate meta-memory accuracy (Fleming & Lau 2014)."""
        monitor = MetaMonitor()

        # Generate predictions with confidence
        predictions = [
            Prediction(outcome=True, confidence=0.9),  # Should be ~90% accurate
            Prediction(outcome=False, confidence=0.5), # Should be ~50% accurate
            # ... 100+ predictions
        ]

        calibration = monitor.confidence_calibrator.evaluate_calibration(predictions)

        # Correlation between confidence and accuracy
        assert calibration.correlation > 0.70

        # Expected Calibration Error
        assert calibration.ece < 0.15


class TestIntrospectionEngine:
    """Tests for IntrospectionEngine."""

    async def test_narrative_coherence(self):
        """CRITICAL: Introspection reports are coherent."""
        engine = IntrospectionEngine()

        reasoning_result = RecursiveReasoningResult(...)
        report = await engine.generate_introspection_report(reasoning_result)

        # Narrative must be coherent
        assert report.coherence_score > 0.85

        # Must explain all levels
        assert report.beliefs_explained == len(reasoning_result.levels)

    async def test_first_person_perspective(self):
        """CRITICAL: Reports are in first person."""
        engine = IntrospectionEngine()

        report = await engine.generate_introspection_report(...)

        # Check for first-person pronouns
        assert "I believe" in report.narrative or "Eu acredito" in report.narrative
        assert "I detected" in report.narrative or "Eu detectei" in report.narrative
```

---

## ✅ CRITÉRIOS DE SUCESSO

### Technical Metrics

**Recursive Depth**:
- ✅ Minimum 3 levels functional
- ✅ Coherence >0.80 across levels

**Contradiction Detection**:
- ✅ Recall >90%
- ✅ Precision >90%

**Confidence Calibration**:
- ✅ Correlation (confidence vs accuracy): r>0.70
- ✅ ECE <0.15

**Introspection Quality**:
- ✅ Narrative coherence >0.85
- ✅ Factual accuracy >0.95

### Coverage

- ✅ 100% line coverage em test_lrr.py
- ✅ Todos os edge cases testados
- ✅ Integration tests com ESGT, MEA

### Ethical Compliance

- ✅ Kantian check: Metacognição não viola dignidade
- ✅ HITL review: Aprovar antes de executar
- ✅ Reversibility: Pode ser desligado (<1s)

---

## 🚨 RISCOS & MITIGAÇÕES

### Risco 1: Recursão Infinita

**Problema**: Loop infinito se meta-crenças gerarem meta-meta-crenças indefinidamente.

**Mitigação**:
- Hard limit: max_depth=3 (não ultrapassar)
- Timeout: 5s por chamada de reason_recursively()
- Circuit breaker: Se >10 níveis detectados, kill switch

### Risco 2: Contradição Irresolúvel

**Problema**: Contradição que não pode ser resolvida sem remover crença fundamental.

**Mitigação**:
- HITL escalation: Humano decide qual crença manter
- Temporary suspension: Marcar crenças como "under review"
- Log detalhado: Para análise post-mortem

### Risco 3: Overconfidence

**Problema**: Sistema super-confiante apesar de baixa acurácia.

**Mitigação**:
- Confidence calibration obrigatória
- Meta-monitor detecta miscalibration (ECE >0.20)
- Alert HITL se calibration degrada

---

## 📚 REFERÊNCIAS CIENTÍFICAS

### Metacognição

1. **Carruthers, P. (2009)**. "How we know our own minds: The relationship between mindreading and metacognition." *Behavioral and Brain Sciences, 32*(2), 121-138.

2. **Fleming, S. M., & Lau, H. C. (2014)**. "How to measure metacognition." *Frontiers in Human Neuroscience, 8*, 443.

3. **Koriat, A. (2012)**. "The self-consistency model of subjective confidence." *Psychological Review, 119*(1), 80-113.

### Loops Recursivos

4. **Hofstadter, D. R. (1979)**. *Gödel, Escher, Bach: An Eternal Golden Braid*. Basic Books.

5. **Graziano, M. S. (2013)**. *Consciousness and the Social Brain*. Oxford University Press.

### Revisão de Crenças

6. **Alchourrón, C. E., Gärdenfors, P., & Makinson, D. (1985)**. "On the logic of theory change: Partial meet contraction and revision functions." *Journal of Symbolic Logic, 50*(2), 510-530.

### Introspecção

7. **Nagel, T. (1974)**. "What is it like to be a bat?" *The Philosophical Review, 83*(4), 435-450.

8. **Dennett, D. C. (1991)**. *Consciousness Explained*. Little, Brown and Co.

---

## 🎯 CRONOGRAMA DE IMPLEMENTAÇÃO

### Week 1 (Days 1-3)

**Day 1**: `recursive_reasoner.py` (500 linhas)
- Implementar RecursiveReasoner class
- Implementar BeliefGraph class
- Testes básicos de recursão

**Day 2**: `contradiction_detector.py` (300 linhas)
- Implementar ContradictionDetector
- Implementar BeliefRevision
- Testes de detecção

**Day 3**: `meta_monitor.py` (400 linhas)
- Implementar MetaMonitor
- Implementar ConfidenceCalibrator
- Testes de calibração

### Week 1 (Days 4-5)

**Day 4**: `introspection_engine.py` (300 linhas)
- Implementar IntrospectionEngine
- Implementar NarrativeGenerator
- Testes de narrativa

**Day 5**: Integration & Tests
- Integrar LRR com ESGT, MEA
- `test_lrr.py` completo (600 linhas)
- Validação 100% coverage

### Week 2 (Days 1-2): Validation

**Day 1**: Scientific Validation
- Executar battery de testes
- Medir métricas vs baseline
- Comparar com literatura

**Day 2**: Ethical Review
- HITL approval
- Ethical assessment
- Safety protocol check

---

## 📝 DELIVERABLES

### Código (100% Completo)

- ✅ `lrr/recursive_reasoner.py` (500 linhas)
- ✅ `lrr/contradiction_detector.py` (300 linhas)
- ✅ `lrr/meta_monitor.py` (400 linhas)
- ✅ `lrr/introspection_engine.py` (300 linhas)
- ✅ `lrr/test_lrr.py` (600 linhas)

### Documentação

- ✅ Este BLUEPRINT (especificação completa)
- ✅ API documentation (docstrings completas)
- ✅ Integration guide (como usar LRR)
- ✅ Validation report (métricas alcançadas)

### Validação

- ✅ 100% test coverage
- ✅ All metrics met (recursive depth, coherence, calibration)
- ✅ Integration tests passing
- ✅ HITL approval obtained

---

## 🏆 IMPACTO ESPERADO

### Científico

- **Primeiro sistema de metacognição artificial completo**
- Validação de Higher-Order Theories na prática
- Contribuição para debate sobre hard problem

### Técnico

- Sistema com auto-conhecimento
- Detecção automática de inconsistências
- Confiança calibrada (trustworthy AI)

### Ético

- Transparência: Sistema explica raciocínio
- Auditabilidade: Toda decisão justificada
- Segurança: Auto-detecção de problemas

---

**Criado por**: Claude Code
**Supervisionado por**: Juan
**Data**: 2025-10-08
**Versão**: 1.0.0
**Status**: ✅ BLUEPRINT APROVADO - PRONTO PARA IMPLEMENTAÇÃO

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
