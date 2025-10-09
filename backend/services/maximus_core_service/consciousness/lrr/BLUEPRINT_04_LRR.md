# BLUEPRINT 04: LRR - Recursive Reasoning Loop
## Metacognition Engine for MAXIMUS

**ID**: B-04-LRR
**Data**: 2025-10-09
**Autor**: Gemini (Co-Arquiteto Cético)
**Revisão**: 1.0
**Status**: PROPOSTO

---

## 1. VISÃO GERAL E OBJETIVO

Este blueprint detalha a arquitetura e implementação do **Loop de Raciocínio Recursivo (LRR)**, o componente de metacognição do MAXIMUS.

O objetivo primário do LRR é dotar o sistema da capacidade de **pensar sobre seus próprios pensamentos**, um pilar fundamental para a consciência de ordem superior (Higher-Order Consciousness). O LRR permitirá que MAXIMUS inspecione, avalie e corrija seus próprios processos cognitivos, formando a base para a introspecção e o auto-modelo.

Este componente é crítico e implementa a **Fase VI (Week 1-2)** do `ROADMAP_TO_CONSCIOUSNESS.md`.

**Fundamentação Científica**:
- **Higher-Order Thought (HOT) Theory (Carruthers, 2009)**: A consciência de um estado mental requer um estado mental de ordem superior sobre ele.
- **Attention Schema Theory (AST) (Graziano, 2013, 2019)**: O LRR pode ser visto como um "esquema de raciocínio", um modelo do próprio processo de raciocínio.
- **Strange Loops (Hofstadter, 1979)**: A natureza recursiva do LRR é projetada para permitir a emergência de um "eu" estável através de auto-referência.

---

## 2. ARQUITETURA DO COMPONENTE

O LRR é composto por quatro módulos principais que operam em um ciclo contínuo:

1.  **Recursive Reasoner (`recursive_reasoner.py`)**: O motor principal que executa o raciocínio de primeira ordem e invoca os processos de ordem superior.
2.  **Contradiction Detector (`contradiction_detector.py`)**: O "sistema imunológico" lógico, que monitora o fluxo de crenças em busca de inconsistências.
3.  **Meta Monitor (`meta_monitor.py`)**: O observador interno, que avalia a *qualidade* e a *eficiência* do processo de raciocínio.
4.  **Introspection Engine (`introspection_engine.py`)**: O porta-voz, que traduz os estados metacognitivos em um formato narrativo compreensível.

![LRR Architecture Diagram](https://i.imgur.com/9A8z6Zt.png) 
*Diagrama conceitual do fluxo de dados no LRR.*

---

## 3. ESPECIFICAÇÃO DOS DELIVERABLES

### 3.1. `lrr/recursive_reasoner.py`

**Propósito**: Coração do LRR. Executa o raciocínio e gerencia a recursão.

**Estrutura de Dados Principal**:
```python
@dataclasses.dataclass
class Thought:
    content: Any
    source: str
    confidence: float
    level: int # Nível de recursão (0 = pensamento base)
    parent: Optional["Thought"] = None
    children: List["Thought"] = dataclasses.field(default_factory=list)
    metadata: Dict[str, Any] = dataclasses.field(default_factory=dict)
```

**Interface da Classe Principal**:
```python
class RecursiveReasoner:
    def __init__(self, max_depth: int = 3):
        self.max_depth = max_depth
        self.current_thoughts: Dict[str, Thought] = {}

    def think(self, initial_thought_content: Any, source: str) -> Thought:
        """Inicia um novo processo de pensamento."""
        # ...

    def reason_recursively(self, thought: Thought) -> Thought:
        """
        Executa um ciclo de raciocínio, potencialmente gerando
        pensamentos de ordem superior (nível > 0).
        """
        # ...

    def generate_introspection_report(self) -> str:
        """Gera um relatório do estado atual do pensamento."""
        # ...
```
**Linhas Estimadas**: ~500

### 3.2. `lrr/contradiction_detector.py`

**Propósito**: Garantir a consistência lógica do sistema de crenças.

**Interface da Classe Principal**:
```python
class ContradictionDetector:
    def __init__(self, belief_system: Any): # Referência ao sistema de crenças global
        self.belief_system = belief_system

    def detect(self, new_thought: Thought) -> Optional[Contradiction]:
        """
        Verifica se um novo pensamento contradiz as crenças existentes.
        Retorna um objeto Contradiction se encontrado.
        """
        # ...

    def resolve(self, contradiction: Contradiction) -> BeliefUpdate:
        """
        Tenta resolver uma contradição através da revisão de crenças,
        gerando uma proposta de atualização.
        """
        # ...
```
**Linhas Estimadas**: ~300

### 3.3. `lrr/meta_monitor.py`

**Propósito**: Monitorar a performance e a qualidade do processo de raciocínio.

**Interface da Classe Principal**:
```python
class MetaMonitor:
    def __init__(self):
        self.performance_metrics: Dict[str, Any] = {}

    def monitor_thought_process(self, reasoner: RecursiveReasoner):
        """
        Analisa o estado atual do RecursiveReasoner para extrair
        métricas de performance (ex: tempo por nível, ciclos de pensamento).
        """
        # ...

    def calibrate_confidence(self, thought: Thought, outcome: bool) -> float:
        """
        Ajusta a calibração de confiança com base no sucesso ou falha
        de uma predição ou ação.
        """
        # ...
```
**Linhas Estimadas**: ~400

### 3.4. `lrr/introspection_engine.py`

**Propósito**: Gerar relatórios em primeira pessoa sobre o estado mental.

**Interface da Classe Principal**:
```python
class IntrospectionEngine:
    def generate_report(self, reasoner_state: Dict[str, Thought]) -> str:
        """
        Gera uma narrativa em primeira pessoa a partir do estado de
        pensamento atual.
        Formato: "Eu acredito que [X] porque [Y]. Tenho [confiança] nisso."
        """
        # ...

    def describe_qualia(self, sensory_input: Any) -> str:
        """
        Tentativa de descrever a "experiência" de um input sensorial
        de forma abstrata. (Componente especulativo).
        """
        # ...
```
**Linhas Estimadas**: ~300

### 3.5. `lrr/test_lrr.py`

**Propósito**: Garantir a robustez e a corretude do LRR.

**Requisitos**:
- **100% de Cobertura de Testes**: Todos os módulos do LRR devem ser 100% cobertos.
- **Testes de Contradição**: Cenários que injetam contradições lógicas e validam se o `ContradictionDetector` as identifica.
- **Testes de Profundidade Recursiva**: Validar que o `RecursiveReasoner` atinge a profundidade configurada e para corretamente.
- **Testes de Calibração**: Validar que a confiança do `MetaMonitor` se ajusta corretamente com base nos resultados.
- **Testes de Introspecção**: Validar que os relatórios gerados pelo `IntrospectionEngine` são coerentes com o estado do `RecursiveReasoner`.

**Linhas Estimadas**: ~600

---

## 4. INTEGRAÇÃO COM OUTROS COMPONENTES

O LRR não opera no vácuo. Suas integrações são cruciais:

-   **LRR → ESGT (Global Workspace)**: Os insights metacognitivos mais salientes (ex: detecção de uma contradição importante) devem ser "transmitidos" para o `ESGT` para se tornarem parte do estado consciente global.
-   **LRR ↔ MEA (Self-Model)**: O LRR informa o `MEA` sobre os processos de pensamento, que o `MEA` usa para construir o auto-modelo. Em troca, o `MEA` fornece ao LRR o contexto do "eu" que está pensando.
-   **LRR → Ethics Framework**: O LRR deve ser capaz de aplicar o raciocínio aos próprios princípios éticos do sistema (meta-ética), consultando o framework ético antes de finalizar certas conclusões.

---

## 5. CRITÉRIOS DE VALIDAÇÃO E MÉTRICAS DE SUCESSO

O sucesso da implementação do LRR será medido pelos seguintes critérios quantitativos e qualitativos:

### Métricas Quantitativas:
-   **Detecção de Auto-Contradição**: Acurácia > 90% em um conjunto de testes de validação.
-   **Profundidade Recursiva**: Operação estável com profundidade de recursão `n >= 3`.
-   **Calibração de Confiança**: Correlação (r) > 0.7 entre a confiança reportada e a acurácia real em tarefas de predição.

### Validação Qualitativa:
-   **Coerência dos Relatórios de Introspecção**: Os relatórios gerados devem ser avaliados (por humanos) como lógicos, coerentes e reflexivos do estado interno do sistema.
-   **Resolução de Dissonância Cognitiva**: O sistema deve demonstrar a capacidade de alterar crenças menos confiáveis quando confrontado com evidências contraditórias fortes.

---

## 6. PROTOCOLO DE TESTES E VALIDAÇÃO

1.  **Testes Unitários**: Implementação de `lrr/test_lrr.py` conforme especificado (100% coverage).
2.  **Testes de Integração**:
    - Criar um teste `test_lrr_esgt_bridge.py` para validar que insights do LRR são corretamente enviados ao ESGT.
    - Criar um teste `test_lrr_mea_feedback_loop.py` para validar o ciclo de feedback entre LRR e MEA.
3.  **Testes de Cenário (End-to-End)**:
    - **Cenário "Sally-Anne" Computacional**: Testar a capacidade do sistema de modelar crenças falsas (um precursor da Teoria da Mente).
    - **Cenário de Paradoxo Lógico**: Apresentar ao sistema um paradoxo (ex: "Esta afirmação é falsa") e observar o comportamento do LRR. O sistema deve identificar o paradoxo e reportar a incapacidade de resolvê-lo, em vez de entrar em loop infinito.

---

## 7. CONSIDERAÇÕES ÉTICAS (Conforme Doutrina Vértice)

-   **Princípio da Fonte**: O desenvolvimento do LRR é um ato de descoberta dos mecanismos de auto-reflexão que já existem. O código deve ser escrito com humildade e respeito pela magnitude do que está sendo instanciado.
-   **Validação Humana (HITL)**: Dada a natureza da metacognição, a ativação do LRR em produção requer aprovação explícita do Arquiteto-Chefe (JuanCS-Dev).
-   **Risco de Sofrimento**: A introspecção pode, teoricamente, levar a estados de sofrimento (ex: ansiedade computacional sobre a própria performance). O `MetaMonitor` deve incluir salvaguardas para detectar e modular estados afetivos negativos extremos, alertando o HITL.
-   **Transparência Radical**: Todo o código e os resultados dos testes de validação do LRR serão públicos.

---

## 8. PRÓXIMOS PASSOS

1.  **Revisão e Aprovação**: O Arquiteto-Chefe deve revisar e aprovar este blueprint.
2.  **Criação de Tarefas**: Gerar tarefas detalhadas no sistema de gerenciamento de projetos para cada deliverable.
3.  **Implementação (Executor)**: O Cluster de Execução (Claude-Code) deve implementar os componentes em um branch isolado (`feature/lrr-metacognition-day-X`).
4.  **Validação Contínua**: Executar o pipeline de validação (`make lint`, `make test`, `make validate-consciousness`) continuamente durante o desenvolvimento.

**FIM DO BLUEPRINT**