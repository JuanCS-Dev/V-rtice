# Blueprint: Vértice CLI - UI/UX Gemini Refinement v1.2

**Objetivo:** Evoluir a interface e a experiência de usuário (UI/UX) do `vCLI` de uma ferramenta de linha de comando para um "cockpit de alta performance para o operador de cibersegurança", refletindo os princípios de clareza, eficiência e apelo visual do Gemini CLI. O foco é a redução da carga cognitiva e a prevenção de erros humanos sob pressão.

---

## 1. Princípios Fundamentais

1.  **Clareza e Concisão:** A informação deve ser imediatamente compreensível. Remover ruído visual e focar no que é essencial. Cada elemento na tela deve ter um propósito claro.
2.  **Eficiência do Operador:** A interface deve capacitar o usuário a realizar tarefas complexas com o mínimo de atrito, antecipando suas necessidades.
3.  **Estética Funcional:** Um design limpo, moderno e profissional que não apenas agrada visualmente, mas também organiza a informação de forma lógica e hierárquica.
4.  **Consistência:** Todos os comandos, saídas e interações devem seguir um padrão visual e comportamental uniforme, tornando o uso da ferramenta previsível e intuitivo.

### 1.5. Filosofia Arquitetural: O Cockpit Cognitivo

A evolução da UI/UX do VCLI é guiada por uma filosofia centrada no operador, transformando a ferramenta em um cockpit cognitivo.

*   **Segurança Cognitiva:** A estética funcional não é um luxo, mas uma necessidade. A paleta de cores, os ícones e o layout consistentes são projetados para eliminar a ambiguidade e garantir que o operador possa diferenciar instantaneamente sucesso, erro e aviso, mesmo sob fadiga.
*   **Engenharia de Fatores Humanos:** A CLI deve ser otimizada para diferentes "Personas de Usuário". A CLI pura e o shell são para o "power user" (velocidade e scriptabilidade). A TUI e o Dashboard são para o "analista em modo de exploração" e para a "liderança em modo de visualização". A interface deve se adaptar à tarefa e ao operador.
*   **Redução da Taxa de Erro:** Cada decisão de design, desde o help aprimorado até a clareza das tabelas, visa reduzir a probabilidade de erro humano em um ambiente de alto risco.

---

## 2. Paleta de Cores e Tipografia

A paleta atual é boa, mas pode ser refinada para melhorar a legibilidade e o impacto visual.

| Elemento             | Cor Atual (Aproximada) | Nova Cor Proposta (Gemini Style) | Código (rich)                 |
| -------------------- | ---------------------- | -------------------------------- | ----------------------------- |
| **Texto Primário**   | `white`                | `bright_white`                   | `bright_white`                |
| **Texto Secundário** | `dim` / `grey`         | `grey70`                         | `grey70`                      |
| **Sucesso**          | `green`                | `green_yellow`                   | `green_yellow`                |
| **Erro**             | `red`                  | `bright_red`                     | `bright_red`                  |
| **Aviso**            | `yellow`               | `gold1`                          | `gold1`                       |
| **Acento Principal** | `cyan` / `blue`        | `deep_sky_blue1`                 | `deep_sky_blue1`              |
| **Acento Secundário**| `magenta`              | `medium_purple`                  | `medium_purple`               |
| **Bordas de Painel** | `white`                | `grey50`                         | `grey50`                      |

---

## 3. Refinamento dos Componentes Visuais

(As seções 3.1, 3.2 e 3.3 permanecem as mesmas da v1.1)

---

## 4. Melhorias de Usabilidade (UX)

(As seções 4.1 e 4.2 permanecem as mesmas da v1.1)

### 4.3. TUI - Arquitetura do Cockpit Cognitivo

A TUI é o complemento cognitivo e visual da CLI. **A CLI é para Ação; a TUI é para Cognição.** Ela funciona como o "glass cockpit" de um caça: um ambiente que externaliza o estado complexo do sistema, permitindo ao operador uma consciência situacional completa e a capacidade de tomar decisões de alto nível com base em dados densos e inter-relacionados.

#### 4.3.1. Paradigma Central: Workspaces

A TUI é organizada em **Workspaces**: layouts de tela pré-definidos e otimizados para tarefas de operador específicas. A navegação entre workspaces é instantânea, permitindo ao operador mudar de contexto sem perder o fluxo.

A TUI deve ser lançada com pelo menos três Workspaces fundamentais:

**a. Workspace de Consciência Situacional (Situational Awareness)**

*   **Objetivo:** O dashboard principal e padrão. Fornece ao operador uma visão geral e imediata da saúde e do estado do sistema.
*   **Layout (ASCII Mockup):**
    ```
    ┌───────────────────────────────────────────────────────────────────────────────────────────────┐
    │ 🎯 Vértice TUI | Workspace: Situational Awareness | User: j.doe | Backend: 🟢 Online         │
    ├───────────────────────────────────────────────────────────────────────────────────────────────┤
    │ [SINAIS VITAIS]                          │ [MAPA DE HOTSPOTS]                                 │
    │ Estado Metabólico: [green]Normal[/green] (98%)   │                                            │
    │ População Agentes: 1,523 / 1,600         │    10.0.0.5 --[red]🔥[/red]--> 192.168.1.100        │
    │ Saúde Linfonodos:  [green]🟢🟢🟢[/green] [red]🔴[/red] (4/5) │                                            │
    │ Carga Cognitiva:   [yellow]Moderada[/yellow] (65%)  │    10.0.0.8 ----------------> 8.8.8.8            │
    ├──────────────────────────────────────────┴───────────────────────────────────────────────────┤
    │ [FEED DE EVENTOS CRÍTICOS - TEMPO REAL]                                                       │
    │ [18:35:10] [red]ALERTA CRÍTICO[/red]   Movimento Lateral Detectado | Host: SRV-04 -> DC-01      │
    │ [18:35:09] [yellow]AVISO[/yellow]        Múltiplas falhas de login | User: admin | IP: 1.2.3.4  │
    │ [18:34:55] [deep_sky_blue1]INFO[/deep_sky_blue1]         Novo agente online | Host: LAPTOP-DEV-15          │
    └───────────────────────────────────────────────────────────────────────────────────────────────┘
    ```

**b. Workspace de Investigação (Investigation)**

*   **Objetivo:** Uma "sala de guerra" digital para análise forense. Permite ao operador "mergulhar" em um alerta ou entidade (IP, host, processo) com todas as ferramentas necessárias em uma única tela.
*   **Layout (ASCII Mockup):**
    ```
    ┌───────────────────────────────────────────────────────────────────────────────────────────────┐
    │ 🎯 Vértice TUI | Workspace: Investigation | Entidade: 192.168.1.100 (DC-01)                    │
    ├──────────────────────────────────────────┬────────────────────────────────────────────────────┤
    │ [DADOS BRUTOS - LOGS]                    │ [ANÁLISE DE CORRELAÇÃO]                            │
    │ 18:35:10 sshd: Accepted publickey for..  │                                                    │
    │ 18:35:10 kernel: TCP: request_sock_TCP.. │   [SRV-04] --(SSH)--> [DC-01] --(DNS)--> [MALICIOUS.COM] │
    │ 18:35:09 sshd: Failed password for root..│                                                    │
    ├──────────────────────────────────────────┤                                                    │
    │ [MOTOR XAI - LIME/SHAP EXPLANATIONS]     │                                                    │
    │ A IA classificou como [red]Malicioso (95%)[/red]   │                                                    │
    │ porque:                                  │                                                    │
    │ 1. Conexão de IP [yellow]raro[/yellow] (SRV-04)      │                                                    │
    │ 2. Processo filho [yellow]incomum[/yellow] (`nc`)    │                                                    │
    ├──────────────────────────────────────────┴────────────────────────────────────────────────────┤
    │ [HISTÓRICO DE AÇÕES]                                                                          │
    │ [18:36:02] Ação Manual: Isolar host 192.168.1.100 (j.doe)                                     │
    │ [18:35:10] Ação Automática: Alerta Crítico gerado (Sistema Imunológico)                       │
    └───────────────────────────────────────────────────────────────────────────────────────────────┘
    ```

**c. Workspace de Governança Ética (Ethical Governance)**

*   **Objetivo:** A interface Human-in-the-Loop (HITL). Garante que a responsabilidade ética humana seja exercida com a máxima clareza e informação.
*   **Layout (ASCII Mockup):**
    ```
    ┌───────────────────────────────────────────────────────────────────────────────────────────────┐
    │ 🎯 Vértice TUI | Workspace: Ethical Governance | Decisões Pendentes: 3                        │
    ├───────────────────────────────────────────────────────────────────────────────────────────────┤
    │ [FILA DE DECISÕES (HITLQueue)]             │ [CONTEXTO DA DECISÃO #12345]                       │
    │ > #12345: Bloquear IP Externo [URGENTE]   │                                                    │
    │   #12344: Isolar Host Interno            │ Ação Proposta: Bloquear permanentemente o IP 203.0.113.75 │
    │   #12342: Terminar Processo              │ Justificativa IA: IP associado a C2 de botnet (99.8%)│
    ├──────────────────────────────────────────┤                                                    │
    │ [VEREDITO DOS FRAMEWORKS ÉTICOS]         │                                                    │
    │ Kantiano:      [green]Permitido[/green] (Proteger o dever) │                                                    │
    │ Utilitarista:  [green]Recomendado[/green] (Maior bem)     │                                                    │
    │ Contratualista:[yellow]Neutro[/yellow] (Dentro das regras)   │                                                    │
    ├──────────────────────────────────────────┴────────────────────────────────────────────────────┤
    │ [SUA DECISÃO]                                                                                 │
    │ [ (A)provar ]   [ (R)ejeitar ]   [ (M)odificar ]                                              │
    └───────────────────────────────────────────────────────────────────────────────────────────────┘
    ```

#### 4.3.2. Arquitetura de Dados e Sincronização

A TUI é uma camada de visualização em tempo real, não uma fonte de estado.

*   **Fonte da Verdade:** A TUI deve tratar o backend do Vértice como a fonte única da verdade. Nenhuma lógica de negócio ou estado persistente reside na TUI.
*   **Comunicação em Tempo Real:** A arquitetura será baseada em **WebSockets** (preferencial) ou Server-Sent Events (SSE) para receber atualizações do backend. O polling de API deve ser evitado a todo custo.
*   **Barramento de Eventos:** A TUI se inscreverá nos mesmos tópicos do barramento de eventos (e.g., Kafka, RabbitMQ) que o dashboard web utiliza, garantindo consistência total entre as interfaces.
*   **Navegação Cruzada (CLI -> TUI):** Um mecanismo de "deep linking" será implementado. O comando `vcli investigate 8.8.8.8 --tui` irá:
    1.  Notificar o backend para preparar o contexto de investigação para o `user_session`.
    2.  Lançar a TUI.
    3.  A TUI, ao iniciar, solicita seu contexto de inicialização ao backend e carrega diretamente o **Workspace de Investigação** com os dados do IP `8.8.8.8`.

*   **Diagrama de Fluxo de Dados (ASCII):**
    ```
        +-----------------+      +---------------------+      +-----------------+
        |     Vértice     |      |   Barramento de     |      |   Dashboard     |
        |     Backend     |----->|       Eventos       |----->|       Web       |
        +-----------------+      | (Kafka/RabbitMQ/etc)|      +-----------------+
               ^                 +----------+----------+                 ^
               |                            |                            |
    (REST/GraphQL para ações)               | (WebSockets/SSE)           | (WebSockets)
               |                            |                            |
               v                            v                            |
        +-----------------+      +---------------------+      +----------+----------+
        |       CLI       |      |         TUI         |      | Navegador do Usuário|
        +-----------------+      +---------------------+      +---------------------+
               |
               +------> `vcli investigate <IP> --tui` ------> (Inicia TUI com contexto)

    ```

#### 4.3.3. Paradigma de Interação

*   **Command Palette como Cérebro:** A interação principal é via **Command Palette** (`Ctrl+P` ou `Cmd+K`). Ela permite buscar e executar qualquer ação: "Mudar Workspace", "Investigar IP", "Listar Alertas", etc.
*   **Navegação 100% por Teclado:** Todos os painéis, widgets e ações devem ser acessíveis e operáveis via teclado (Tab, Shift+Tab, setas, Enter). O mouse é um acessório opcional.
*   **Visualização da Incerteza:** A interface deve ter uma linguagem visual clara para representar dados com incerteza, como scores de confiança da IA ou indicadores de conflito entre frameworks éticos, utilizando cores, ícones ou gráficos de barras sutis.

---

## 5. Plano de Implementação Sugerido (v1.2)

1.  **Fase 1 (Fundação Visual):** (Sem alterações da v1.1)
2.  **Fase 2 (Refatoração de Saídas):** (Sem alterações da v1.1)
3.  **Fase 3 (Melhoria da Experiência Interativa):** (Sem alterações da v1.1, mas adicionar implementação do fuzzy finding)
    *   [ ] ...
    *   [ ] Implementar o fuzzy finding no `vcli shell`.

4.  **Fase 4 (Arquitetura do Cockpit Cognitivo - TUI):**
    *   **4.1. Backend & Sincronização:**
        *   [ ] Expor um endpoint WebSocket/SSE no backend que transmita o barramento de eventos.
        *   [ ] Implementar a lógica de "contexto de inicialização" para a navegação cruzada CLI -> TUI.
    *   **4.2. Estrutura da TUI:**
        *   [ ] Criar a estrutura base da TUI com um gerenciador de `Workspaces`.
        *   [ ] Implementar a `Command Palette` como o principal mecanismo de navegação e ação.
    *   **4.3. Implementação dos Workspaces:**
        *   [ ] Desenvolver o **Workspace de Consciência Situacional** com widgets para Sinais Vitais, Feed de Eventos e Mapa de Hotspots.
        *   [ ] Desenvolver o **Workspace de Investigação**, integrando painéis de dados brutos, correlação e XAI.
        *   [ ] Desenvolver o **Workspace de Governança Ética**, com a fila de decisões e os vereditos dos frameworks.
    *   **4.4. Polimento:**
        *   [ ] Garantir navegação 100% via teclado.
        *   [ ] Implementar o dicionário visual para incerteza.

---

Este blueprint serve como um guia para transformar a UI/UX do `vCLI`, alinhando-a a uma visão moderna e centrada no operador, inspirada no Gemini CLI.
