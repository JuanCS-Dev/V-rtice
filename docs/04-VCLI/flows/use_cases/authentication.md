
# 🕵️ Caso de Uso: Autenticação de Usuário

Este documento descreve o fluxo de usuário para os comandos de autenticação (`login`, `logout`, `whoami`).

**ALERTA DE SEGURANÇA:** O fluxo de `login` descrito abaixo é o fluxo **simulado e inseguro** atualmente implementado no código. Ele **não** representa um fluxo OAuth2 seguro.

## 1. Login de Usuário (`vcli auth login`)

**Jornada do Usuário:**
Um novo usuário precisa se autenticar na CLI para ter acesso aos comandos protegidos.

- **Comando:** `vcli auth login`
- **Exemplo:** `vcli auth login --email juan.brainfarma@gmail.com`

### Fluxo de Execução (Simulado)

1.  **Entrada:** O usuário pode opcionalmente fornecer um e-mail via flag `--email`.
2.  **Validação (Cliente):**
    - Se o e-mail não for fornecido, um prompt estilizado (`styled_input`) solicita o e-mail.
    - Se o e-mail continuar vazio, a aplicação encerra.
3.  **Autenticação (Simulada):**
    - O sistema **não** abre um navegador nem inicia um fluxo OAuth2 real.
    - Ele pede uma confirmação manual ao usuário: `Authenticate as <email>?`.
    - Se o usuário confirmar, o sistema **falsifica** os dados de autenticação:
        - `user_info` é criado com base no e-mail fornecido.
        - Um `access_token` falso é gerado (ex: `ya29.mock_token_for_...`).
4.  **Armazenamento de Credenciais:**
    - A função `auth_manager.save_auth_data` é chamada com os dados falsos.
    - O `AuthManager` tenta salvar o token falso no `keyring` do sistema.
    - Ele salva os metadados do token (datas) em `~/.vertice/auth/token.json`.
    - Ele salva os dados do usuário em `~/.vertice/auth/user.json`.
5.  **Dependências Externas:** Nenhuma (pois o fluxo é 100% local e simulado).
6.  **Saída:** Uma mensagem de boas-vindas é exibida, confirmando o "sucesso" da autenticação e mostrando o `role` do usuário.
7.  **Efeitos Colaterais:** Cria/sobrescreve os arquivos `token.json` e `user.json` no diretório `~/.vertice/auth`.

### Edge Cases e Tratamento de Erros

- **E-mail não fornecido:** O sistema solicita interativamente.
- **Autenticação cancelada:** Se o usuário não confirmar no prompt, a aplicação encerra com uma mensagem de "Authentication cancelled".
- **Falha no Keyring:** Se o `keyring` não estiver acessível, um aviso é exibido, mas a autenticação (simulada) prossegue, armazenando os dados apenas nos arquivos JSON.

---

## 2. Logout de Usuário (`vcli auth logout`)

**Jornada do Usuário:**
Um usuário deseja encerrar sua sessão na CLI de forma segura.

- **Comando:** `vcli auth logout`

### Fluxo de Execução

1.  **Entrada:** Nenhum argumento é necessário.
2.  **Validação:** O sistema verifica se o usuário está atualmente logado. Se não, exibe uma mensagem e encerra.
3.  **Confirmação:** Pede ao usuário para confirmar a ação de logout.
4.  **Processamento Interno:**
    - A função `auth_manager.logout()` é chamada.
    - O `AuthManager` tenta apagar a senha `vertice-cli` do `keyring`.
    - Os arquivos `~/.vertice/auth/token.json` e `~/.vertice/auth/user.json` são removidos do sistema de arquivos.
5.  **Saída:** Uma mensagem de "Logout successful!" é exibida.

### Edge Cases e Tratamento de Erros

- **Usuário não logado:** O comando informa que o usuário não está logado e sai.
- **Logout cancelado:** Se o usuário não confirmar, a operação é abortada.
- **Erro na remoção de arquivos:** Uma exceção genérica será capturada e uma mensagem de erro será exibida.
