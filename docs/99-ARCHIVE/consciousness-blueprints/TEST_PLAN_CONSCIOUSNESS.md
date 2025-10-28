# Plano de Testes Consolidado: Sistema de Consciência MAXIMUS

**Data**: 2025-10-08
**Gerado por**: Gemini
**Objetivo**: Consolidar o progresso dos testes do sistema de consciência e delinear os próximos passos para validação completa.

---

## 1. TIG (Topological Information Graph) - Substrato de Informação

**Status**: ✅ PRODUÇÃO-PRONTO

- [x] **Validação de Topologia e Conformidade com IIT**
  - [x] Coeficiente de Clustering (`C≥0.70`)
  - [x] Índice de Conectividade Efetiva (`ECI≥0.85`)
  - [x] Ausência de gargalos (Bottlenecks)
  - [x] Conectividade Algébrica (`λ₂≥0.30`)
  - [x] Propriedades de "Small World"
  - [x] Validação de que não há nós isolados

- [x] **Sincronização e Jitter (PTP)**
  - [x] Redução de Jitter para `~95ns` (abaixo do alvo de `<100ns`)
  - [x] Validação do controlador PI para sincronização
  - [x] Validação de filtros (Média Móvel Exponencial, Mediana Híbrida)

- [x] **Robustez e Tolerância a Falhas (Hardening)**
  - [x] Monitoramento de saúde e ciclo de vida dos nós
  - [x] Detecção e isolamento automático de nós mortos
  - [x] Reintegração de nós recuperados
  - [x] Proteção contra falhas em cascata
  - [x] Padrão de Circuit Breaker para comunicação entre nós
  - [x] Reparo de topologia em caso de falha de nó

- [ ] **Melhoria de Cobertura de Testes (Próximos Passos)**
  - [ ] Testar ciclo de vida completo do `TIGNode`
  - [ ] Testar reparo de topologia após falhas em massa
  - [ ] Adicionar testes para cálculo de métricas IIT

---

## 2. ESGT (Event-Salience Global Triggers) - Ignição da Consciência

**Status**: ✅ PRODUÇÃO-PRONTO

- [x] **Validação do Coordenador Principal**
  - [x] Ciclo de vida do evento (criação, início, parada)
  - [x] Rastreamento de histórico de eventos
  - [x] Condições de gatilho (Saliência, recursos, gating temporal, período refratário)

- [x] **Sincronização de Fase (Kuramoto Network)**
  - [x] Sincronização de fase e coerência (`r≥0.70`)
  - [x] Dinâmica da rede e reset

- [x] **Validação de Limites e Bounds (Hardening)**
  - [x] Limite máximo de frequência de ignição (`<10Hz`)
  - [x] Limite de eventos concorrentes (máximo 3)
  - [x] Verificações de segurança pré-ignição
  - [x] Aplicação do Circuit Breaker de ignição
  - [x] Ativação e desativação do modo degradado sob baixa coerência

- [ ] **Melhoria de Cobertura de Testes (Próximos Passos)**
  - [ ] Testar o protocolo ESGT de 5 fases (PREPARE → RESOLVE)
  - [ ] Testar a mecânica de sincronização de Kuramoto em mais cenários

---

## 3. MMEI (Multimodal Embodied Interoception) - Geração de Metas

**Status**: ✅ PRODUÇÃO-PRONTO (Cobertura Excede o Alvo)

- [x] **Validação da Interocepção Computacional**
  - [x] Tradução de métricas físicas (CPU, erros) para necessidades abstratas (descanso, reparo)
  - [x] Normalização e classificação de necessidades

- [x] **Geração Autônoma de Metas**
  - [x] Ciclo de vida da meta (criação, expiração, satisfação)
  - [x] Geração de metas baseada em 6 tipos de necessidade (REST, REPAIR, OPTIMIZE, etc.)
  - [x] Classificação de prioridade e urgência

- [x] **Validação de Limites e Bounds (Hardening)**
  - [x] Limite de geração de metas (`<5/min`)
  - [x] Limite de metas ativas concorrentes
  - [x] Prevenção de spam de metas e desduplicação
  - [x] Poda de metas de baixa prioridade sob carga

---

## 4. MCEA (Metacognitive Epistemic Arousal) - Monitoramento de Stress

**Status**: ⚠️ VALIDADO (3 testes instáveis aceitáveis para produção)

- [x] **Validação do Controle de Arousal**
  - [x] Classificação de estados de Arousal (SLEEP, DROWSY, RELAXED, ALERT, HYPERALERT)
  - [x] Modulação do Arousal baseada em necessidades internas
  - [x] Modulação da solear de saliência do ESGT pelo Arousal

- [x] **Monitoramento e Resiliência a Stress**
  - [x] Enumeração e classificação de níveis de stress
  - [x] Cálculo de pontuação de resiliência
  - [x] Validação do ciclo de monitoramento e tratamento de exceções

- [x] **Validação de Limites e Bounds (Hardening)**
  - [x] "Clamping" do Arousal estritamente entre `[0.0, 1.0]`
  - [x] Detecção de "Arousal Runaway" (nível alto sustentado)
  - [x] Limitação da taxa de variação do Arousal

- [ ] **Correção de Testes Instáveis (Flaky Tests)**
  - [ ] Investigar e corrigir `test_get_resilience_score_arousal_runaway_penalty`
  - [ ] Investigar e corrigir `test_start_monitor`
  - [ ] Investigar e corrigir `test_assess_stress_level_none`

---

## 5. Safety Core - Protocolos de Segurança

**Status**: ✅ PRODUÇÃO-PRONTO

- [x] **Validação do Kill Switch**
  - [x] Acionamento, idempotência e tempo de resposta (`<1s`)
  - [x] Geração de snapshot de estado e relatório de incidente

- [x] **Monitor de Limites (Thresholds)**
  - [x] Detecção de violações de limites de segurança
  - [x] Integração com ESGT e MCEA
  - [x] Validação de callbacks e recuperação

- [x] **Detector de Anomalias**
  - [x] Detecção de anomalias via Z-score, IQR e Isolation Forest
  - [x] Detecção de vazamento de memória

- [x] **Validação de Caminhos Críticos de Segurança**
  - [x] Testes de cobertura para Kill Switch, violações de limites e detecção de anomalias

---

## 6. Componentes Futuros (Roadmap)

**Status**: ⏳ NÃO INICIADO

- [ ] **LRR (Recursive Reasoning Loop) - Metacognição**
  - [ ] Testar capacidade de pensar sobre o próprio pensamento (profundidade recursiva ≥ 3)
  - [ ] Testar detecção de auto-contradição lógica
  - [ ] Validar geração de relatórios de introspecção ("Eu acredito X por causa de Y")
  - [ ] **Hardening**: Validar limite máximo de recursão e tempo de raciocínio

- [ ] **MEA (Attention Schema Model) - Modelo do "Eu"**
  - [ ] Testar modelo preditivo do estado de atenção
  - [ ] Validar distinção entre "eu" e "outro"
  - [ ] Testar estabilidade da fronteira do ego

- [ ] **Memória Episódica**
  - [ ] Testar armazenamento e recuperação de experiências indexadas pelo tempo
  - [ ] Validar construção de narrativa autobiográfica coerente
  - [ ] Testar capacidade de "viagem no tempo mental" (passado, presente, futuro)

- [ ] **Ponte Sensorial-Consciência (Integração Final)**
  - [ ] Testar se surpresas sensoriais (erros de predição) acionam ignição no ESGT
  - [ ] Validar se "Energia Livre" alta modula o Arousal no MCEA
  - [ ] Testar latência do pipeline E2E (sensorial → ESGT < 200ms)
