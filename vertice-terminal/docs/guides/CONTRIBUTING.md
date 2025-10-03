
# 🤝 Guia de Contribuição para o Vértice CLI

Primeiramente, obrigado pelo seu interesse em contribuir para o Vértice CLI! Toda contribuição é bem-vinda, desde a correção de bugs e a melhoria da documentação até a proposição de novas funcionalidades.

## 🚀 Começando

### 1. Setup do Ambiente de Desenvolvimento

Para garantir um ambiente de desenvolvimento consistente, siga estes passos:

1.  **Fork & Clone:**
    - Faça um fork do repositório principal.
    - Clone o seu fork para a sua máquina local:
      ```bash
      git clone https://github.com/SEU_USUARIO/vertice-terminal.git
      cd vertice-terminal
      ```

2.  **Crie um Ambiente Virtual:**
    - É crucial usar um ambiente virtual para isolar as dependências do projeto.
      ```bash
      python3 -m venv venv
      source venv/bin/activate
      ```

3.  **Instale as Dependências:**
    - Instale as dependências de produção e de desenvolvimento.
      ```bash
      pip install -r requirements.txt
      # Se houver um requirements-dev.txt, instale-o também
      # pip install -r requirements-dev.txt
      ```

4.  **Instale o CLI em Modo Editável:**
    - Isso permite que as alterações que você faz no código sejam refletidas imediatamente ao executar o `vcli`.
      ```bash
      pip install -e .
      ```

5.  **Verifique a Instalação:**
    - Execute o comando de ajuda para garantir que tudo está funcionando.
      ```bash
      vcli --help
      ```

### 2. Padrões de Código

- **Formatação:** Usamos `black` para formatação de código e `isort` para ordenação de imports. Configure seu editor para usá-los ou execute-os manualmente antes de commitar.
- **Linting:** Usamos `flake8` ou `pylint` para checagem de estilo e erros. O código deve passar no linter sem erros.
- **Type Hints:** Todo novo código deve ter anotações de tipo completas. Usamos `mypy` para checagem estática de tipos.
- **Docstrings:** Funções e classes públicas devem ter docstrings no formato Google Style.

### 3. Git Workflow (Fluxo de Trabalho com Git)

1.  **Crie uma Branch:** Nunca trabalhe diretamente na `main`. Crie uma branch descritiva para a sua feature ou correção.
    ```bash
    # Para uma nova feature
    git checkout -b feature/nome-da-feature

    # Para uma correção de bug
    git checkout -b fix/descricao-do-bug
    ```

2.  **Faça Commits Atômicos:** Faça commits pequenos e focados. A mensagem do commit deve seguir o padrão [Conventional Commits](https://www.conventionalcommits.org/).
    - **Exemplo (feature):** `feat(scan): add support for IPv6 targets`
    - **Exemplo (fix):** `fix(auth): prevent crash when token file is corrupted`

3.  **Abra um Pull Request (PR):**
    - Faça o push da sua branch para o seu fork.
    - Abra um Pull Request para a branch `main` do repositório original.
    - No PR, descreva claramente o que foi feito e por quê. Se ele resolve uma Issue, mencione-a (ex: `Closes #123`).

### 4. Requisitos para Testes

- **Novas Funcionalidades:** Devem vir acompanhadas de testes unitários que cubram os cenários de sucesso, de falha e os casos de borda.
- **Correções de Bugs:** Devem incluir um teste que falhava antes da correção e que passa depois dela. Isso previne regressões.
- **Cobertura:** Buscamos manter a cobertura de testes (`test coverage`) acima de 80%.

## 📝 Checklist para Revisão de Código (Code Review)

Antes de aprovar um PR, os revisores verificarão:

- [ ] O código segue os padrões de estilo e formatação?
- [ ] O código está bem documentado (type hints, docstrings)?
- [ ] A mudança faz o que foi proposto?
- [ ] Existem testes para a nova funcionalidade ou correção?
- [ ] Os testes existentes continuam passando?
- [ ] A mudança introduz algum risco de segurança?
- [ ] A documentação do usuário (se aplicável) foi atualizada?

Obrigado por ajudar a tornar o Vértice CLI ainda melhor!
