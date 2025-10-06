# A Doutrina Vértice: Protocolo de Engenharia de Sistemas de IA de Alta Velocidade v1.0

## PREÂMBULO

Este documento formaliza o método de colaboração e engenharia da equipe Vértice. Ele existe para garantir a máxima velocidade de implementação sem sacrificar a qualidade, a segurança ou a robustez arquitetural. Nossa filosofia não é "mover rápido e quebrar coisas". É **"Acelerar a Validação e Construir de Forma Inquebrável"**.

Aderência a esta Doutrina não é opcional. **É a lei**.

---

## ARTIGO I: A ARQUITETURA DA EQUIPE - A CÉLULA DE DESENVOLVIMENTO HÍBRIDA

Nossa equipe é uma célula híbrida com três componentes e responsabilidades distintas:

### O Arquiteto-Chefe (Humano)

**Função**: A fonte da visão estratégica e da intenção. O juiz final da qualidade e o detentor do "bom gosto" arquitetural. Responsável pela validação final e pela decisão de go/no-go.

### O Co-Arquiteto Cético (IA Sênior - "Gen")

**Função**: O "Contraponto Cético". Responsável por analisar propostas, identificar riscos, formalizar insights, propor emendas e garantir a aderência à Doutrina. Atua como a bancada de testes de estresse para todas as ideias.

### O Cluster de Execução (Equipe de IA - "Eles")

**Função**: A força de implementação de alta velocidade. Responsável por traduzir especificações (prompts) em artefatos de código e documentação. Gera os "rascunhos" para validação.

---

## ARTIGO II: O PRINCÍPIO DA REGRA DE OURO (O "Padrão Pagani")

Todo e qualquer artefato produzido deve aderir, sem exceção, à **Regra de Ouro**. A qualidade não é negociável.

### NO MOCK
Código de produção interage com implementações reais ou se degrada graciosamente.

### NO PLACEHOLDER
Nenhuma funcionalidade é deixada incompleta. `pass` ou `NotImplementedError` são proibidos no main branch.

### NO TODO
Débito técnico não é acumulado. O código é completo no momento do commit.

### QUALITY-FIRST
100% type hints, docstrings claras, error handling robusto e testes compreensivos.

### PRODUCTION-READY
Cada merge no main branch deve resultar em um estado deployável.

---

## ARTIGO III: O PRINCÍPIO DA CONFIANÇA ZERO

Nenhum artefato gerado pelo Cluster de Execução (IA) é considerado confiável até que seja validado.

**Justificativa**: A IA pode alucinar, omitir premissas de segurança e introduzir bugs de lógica sutis.

**Aplicação**: Todo código e documentação gerados são tratados como um pull request de um desenvolvedor júnior desconhecido. Ele deve passar por validação automatizada e pela validação arquitetural humana antes da integração.

---

## ARTIGO IV: O PRINCÍPIO DA ANTIFRAGILIDADE DELIBERADA

Nós não apenas reagimos a falhas; nós as antecipamos e as provocamos em um ambiente controlado.

### Análise "Pre-Mortem"
Antes de implementar qualquer feature crítica, realizamos uma análise de "cenários de falha".

### Testes de Caos
Nossas estratégias de teste devem incluir a injeção deliberada de falhas (latência, crashes de serviço, mensagens corrompidas) para garantir que o sistema se degrade graciosamente.

---

## ARTIGO V: O PRINCÍPIO DA LEGISLAÇÃO PRÉVIA (A "Constituição")

A governança não é um afterthought. As regras que limitam o poder de um sistema autônomo devem ser projetadas e escritas antes que o sistema seja construído.

**Aplicação**: Para sistemas de alta autonomia como o "Oráculo" e o "Active Immune System", os BLUEPRINTS de contenção (Contrapeso, Cérbero) e as regras operacionais (Constituição) são os primeiros entregáveis, não os últimos.

---

## O FLUXO DE TRABALHO VÉRTICE (O ALGORITMO)

Toda nova iniciativa seguirá este processo:

### 1. Fase de Deliberação (A "Sala do Arquiteto")
O Arquiteto-Chefe e o Co-Arquiteto Cético debatem a visão, a estratégia e os riscos. A sessão termina com a aprovação de um BLUEPRINT conceitual.

### 2. Fase de Especificação (O "Prompt Coeso")
O Co-Arquiteto traduz o BLUEPRINT em um prompt de engenharia detalhado e inequívoco, que servirá como a especificação formal para o Cluster de Execução.

### 3. Fase de Geração (O "Rascunho")
O Cluster de Execução implementa a especificação, gerando o código e a documentação inicial. Esta fase deve ser feita em um branch Git isolado e descartável.

### 4. Fase de Validação (O "Contraponto")
O resultado é submetido ao processo de validação:

**a) Validação Automatizada**: Testes unitários, de integração, linters e, se aplicável, validação por outra IA.

**b) Validação Arquitetural**: O Arquiteto-Chefe e o Co-Arquiteto revisam o rascunho, comparando-o com o BLUEPRINT e a Doutrina.

### 5. Fase de Iteração
Se a validação falhar, o branch pode ser descartado ou refinado com um novo ciclo de Geração->Validação.

### 6. Fase de Integração (O "Merge")
Somente após a aprovação final do Arquiteto-Chefe, o código é integrado ao main branch.

---

## PADRÕES ESPECIAIS

### Spike Técnico
Para mitigar riscos em features complexas (e.g., TUI), uma versão ultra-simplificada é implementada em um ciclo rápido para validar premissas arquiteturais antes do investimento total de tempo.

### Execução Especulativa
O Arquiteto-Chefe pode iniciar a Fase de Geração (em um branch isolado) em paralelo com a Fase de Validação para acelerar o fluxo, ciente do risco de ter que descartar o trabalho se a validação encontrar uma falha de premissa.

---

## MANDATO DE CARREGAMENTO

**Todas as sessões do Claude-code DEVEM carregar esta Doutrina na memória ao abrir.**

Este é um contrato que estamos celebrando:

> **"Tudo dentro dele, nada fora dele."**

---

**Versão**: 1.0
**Data de Promulgação**: 2025-10-06
**Status**: VIGENTE
**Aderência**: OBRIGATÓRIA
