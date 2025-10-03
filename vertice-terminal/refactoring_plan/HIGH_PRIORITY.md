
# ⏫ Plano de Refatoração: ALTA PRIORIDADE (Ações para a Próxima Semana)

Após a correção das vulnerabilidades críticas, esta fase foca em resolver os maiores débitos técnicos que afetam a funcionalidade, a manutenibilidade e a qualidade geral do código.

---

### 1. Implementar Funcionalidades de Placeholder

- **Descrição do Problema:** A maioria dos comandos da CLI (`scan`, `hunt`, `monitor`, `malware`, etc.) são apenas placeholders. Eles não possuem funcionalidade real, apenas simulam uma execução com `asyncio.sleep` e retornam dados falsos. A aplicação, em seu estado atual, é uma fachada.
- **Impacto Atual:** **MUITO ALTO.** A aplicação não entrega o valor que promete. A confiança do usuário é zero. O débito técnico é massivo.
- **Solução Proposta:**
    1.  Priorizar os comandos mais importantes (ex: `scan ports`, `hunt search`).
    2.  Para cada comando, implementar a lógica real:
        - **`scan`**: Integrar com ferramentas reais como `nmap-python` ou executar o binário `nmap` de forma segura.
        - **`hunt`**: Conectar a uma fonte de dados real (ex: um SIEM, um data lake, ou uma API de Threat Intelligence).
        - **`malware`**: Implementar o upload real do arquivo no `MalwareConnector` e a lógica de análise no backend.
    3.  Remover os dados hardcoded e os `asyncio.sleep`.
- **Esforço Estimado:** 20-30 horas (para as funcionalidades principais)
- **Risco da Correção:** Médio. A integração com sistemas externos pode ser complexa.

---

### 2. Abstrair Lógica de Comando Duplicada

- **Descrição do Problema:** A lógica de execução de comandos (criar conector, checar saúde, exibir spinner, chamar método, tratar erro, fechar conector) é repetida em quase todos os arquivos de `vertice/commands/`. Isso viola o princípio DRY e torna a manutenção um pesadelo.
- **Impacto Atual:** **ALTO.** Qualquer mudança no fluxo de execução de um comando (ex: adicionar logging) precisa ser feita em dezenas de lugares, o que é ineficiente e propenso a erros.
- **Solução Proposta:**
    1.  Criar um **decorator** (ex: `@with_connector(ConnectorClass)`) ou um **context manager** que encapsule todo esse fluxo repetitivo.
    2.  O decorator receberia a classe do conector como argumento, a instanciaria, faria o health check e a injetaria na função do comando.
    3.  O decorator também conteria o bloco `try...except...finally` para garantir o tratamento de erro padrão e o fechamento do conector.
    4.  Refatorar todos os comandos para usar este novo decorator, removendo 80% do código duplicado.
- **Esforço Estimado:** 4-6 horas
- **Risco da Correção:** Baixo. O benefício em manutenibilidade é imenso.

---

### 3. Implementar Validação de Entrada Robusta

- **Descrição do Problema:** A aplicação não valida a maioria das entradas do usuário (IPs, domínios, hashes, nomes de serviço) no lado do cliente. Isso pode levar a erros inesperados, comportamento incorreto e até vulnerabilidades de segurança se o backend não for robusto.
- **Impacto Atual:** **MÉDIO.** A CLI parece frágil e pode quebrar facilmente com entradas inválidas.
- **Solução Proposta:**
    1.  Usar as funções do `utils/validators.py` de forma consistente no início de cada comando para validar os argumentos antes de fazer qualquer chamada de API.
    2.  Para tipos de validação que não existem (ex: `service_name`), adicioná-los ao módulo de validadores.
    3.  Para os comandos que aceitam um `target`, implementar uma lógica que detecta o tipo de alvo (IP, domínio, etc.) e aplica a validação correta.
    4.  Retornar mensagens de erro claras para o usuário quando a validação falhar.
- **Esforço Estimado:** 3-5 horas
- **Risco da Correção:** Baixo.

---

### 4. Refatorar os "God Modules"

- **Descrição do Problema:** Os módulos `utils/auth.py` e `utils/output.py` acumulam responsabilidades demais, violando o Princípio da Responsabilidade Única.
- **Impacto Atual:** **MÉDIO.** Dificulta a navegação no código, os testes e a reutilização de componentes.
- **Solução Proposta:**
    1.  **Dividir `utils/output.py`:**
        - `ui/prompts.py`: Para as funções de input (`styled_input`, etc.).
        - `ui/formatters.py`: Para as funções de formatação de dados (`print_table`, `format_ip_analysis`).
        - `ui/messaging.py`: Para as mensagens de status (`print_success`, `print_error`).
    2.  **Dividir `utils/auth.py`:**
        - `auth/storage.py`: Para a lógica de salvar/carregar tokens e dados de usuário.
        - `auth/roles.py`: Para a definição e verificação de permissões (RBAC).
        - `auth/manager.py`: Para orquestrar o fluxo de autenticação.
- **Esforço Estimado:** 5-8 horas
- **Risco da Correção:** Médio. Exigirá a atualização de muitas declarações de `import` em toda a aplicação.
