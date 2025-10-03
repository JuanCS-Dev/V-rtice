
# 🗳️ Backlog de Refatoração e Melhorias

Esta lista contém itens de baixa prioridade, sugestões de melhorias e ideias para o futuro. Eles não são urgentes, mas devem ser considerados para melhorar a qualidade de vida do desenvolvedor e adicionar polimento à aplicação a longo prazo.

---

### 1. Melhorar o Tratamento de Exceções

- **Descrição:** Atualmente, a maioria dos comandos usa um bloco `except Exception as e:` genérico. Isso pode mascarar bugs e não fornece feedback claro sobre o que deu errado (ex: foi um erro de rede, um erro 404 da API, ou um erro de lógica no cliente?).
- **Sugestão:**
    - Nos conectores, em vez de apenas imprimir o erro, levantar exceções customizadas (ex: `ServiceOfflineError`, `APINotFoundError`).
    - Nos comandos, capturar essas exceções específicas e fornecer mensagens de erro mais úteis para o usuário.

---

### 2. Melhorar o Design da API dos Conectores

- **Descrição:** Alguns conectores têm um design de API confuso. Por exemplo, o `ThreatIntelConnector` tem um método `lookup_threat` que é usado incorretamente pelo comando `threat scan` com um caminho de arquivo.
- **Sugestão:**
    - Revisar a API de cada conector para garantir que os nomes dos métodos sejam claros e que eles façam o que o nome diz.
    - Criar métodos distintos para ações distintas. Por exemplo, `ThreatIntelConnector` poderia ter `lookup_indicator()` e `scan_file()`, que chamariam endpoints diferentes no backend.

---

### 3. Adicionar Mais Recursos Avançados à CLI

- **Descrição:** A CLI atual é funcional (ou será, após a implementação dos placeholders), mas poderia ter recursos mais avançados para melhorar a usabilidade.
- **Sugestões:**
    - **Output em Diferentes Formatos:** Adicionar suporte para mais formatos de saída, como CSV, HTML, ou Markdown (`--output-format csv`).
    - **Pipelining:** Permitir que a saída de um comando seja usada como entrada para outro (ex: `vcli ip bulk ips.txt --quiet | vcli hunt search -`).
    - **Gerenciamento de Perfil:** Permitir que os usuários configurem e alternem entre diferentes perfis de autenticação e configuração (ex: `vcli config profile use work`).

---

### 4. Aumentar a Cobertura de Testes

- **Descrição:** A suíte de testes atual é um ponto de partida, mas não cobre todos os módulos, comandos e casos de borda. O objetivo de 80% de cobertura ainda não foi atingido.
- **Sugestão:**
    - Escrever testes unitários para todos os módulos de `commands` e `connectors` que ainda não foram cobertos.
    - Adicionar mais testes de integração para os fluxos de usuário mais críticos.
    - Focar em testar os casos de erro e de entrada inválida.

---

### 5. Melhorar a Documentação da API Gerada

- **Descrição:** A documentação gerada pelo `pydoc` é funcional, mas básica. Uma documentação mais rica e navegável melhoraria a experiência do desenvolvedor.
- **Sugestão:**
    - Migrar a geração de documentação de `pydoc` para `Sphinx`.
    - Usar extensões do Sphinx como `autodoc` (para gerar documentação a partir de docstrings) e `napoleon` (para suportar docstrings no estilo Google).
    - Criar um tema customizado para a documentação para alinhá-la com a identidade visual do Vértice.
