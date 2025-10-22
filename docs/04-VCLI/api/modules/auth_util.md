
# 📄 `vertice/utils/auth.py`

## 📋 Descrição

Este módulo é o pilar (ainda que frágil) do sistema de autenticação e autorização da CLI. Ele define a classe `AuthManager`, que gerencia o estado de login, os dados do usuário, os papéis (roles) e as permissões. Ele também expõe funções de alto nível para serem usadas como "guards" nos comandos da CLI.

**IMPORTANTE:** A arquitetura deste módulo mistura múltiplas responsabilidades e contém vulnerabilidades de segurança críticas, como configurações e papéis hardcoded.

## 🏗️ Classes

### `AuthManager`

Classe central que lida com todo o ciclo de vida da autenticação.

**Atributos:**
- `auth_dir (Path)`: O diretório `~/.vertice/auth` onde os arquivos de autenticação são armazenados.
- `token_file (Path)`: O caminho para `token.json`, que armazena metadados do token (como a data de expiração).
- `user_file (Path)`: O caminho para `user.json`, que armazena informações do usuário logado.

**Métodos Principais:**

- `is_authenticated() -> bool`: Verifica se um `token.json` válido e não expirado existe.
- `get_current_user() -> Optional[Dict]`: Lê e retorna os dados do `user.json`.
- `get_user_role() -> str`: Determina o papel (role) do usuário atual, com uma regra especial para o `SUPER_ADMIN`.
- `has_permission(permission: str) -> bool`: Verifica se o role do usuário atual tem a permissão especificada, com base no dicionário `ROLES`.
- `save_auth_data(...)`: Salva os dados de autenticação. Tenta salvar o `access_token` no `keyring` do sistema e os metadados/dados do usuário nos arquivos JSON.
- `logout()`: Remove o token do `keyring` e apaga os arquivos `token.json` e `user.json`.
- `get_access_token() -> Optional[str]`: Recupera o `access_token` do `keyring`.
- `require_auth()`: Função de guarda que encerra a execução da CLI se o usuário não estiver autenticado.
- `require_permission(permission: str)`: Função de guarda que encerra a execução se o usuário não tiver a permissão necessária.

## 🌎 Variáveis Globais

- `AUTH_CONFIG (dict)`: Dicionário com placeholders para as credenciais do Google OAuth2. **(Vulnerabilidade Crítica)**
- `SUPER_ADMIN (str)`: E-mail do super administrador hardcoded. **(Vulnerabilidade Alta)**
- `ROLES (dict)`: Dicionário que define os papéis e suas permissões de forma estática. **(Débito Técnico Grave)**
- `auth_manager (AuthManager)`: Instância global da classe `AuthManager`, usada em toda a aplicação.

## 💡 Exemplo de Uso (em um comando)

```python
from ..utils.auth import require_auth, require_permission

@app.command()
def my_secure_command():
    # Garante que o usuário está logado
    require_auth()

    # Garante que o usuário tem a permissão 'execute'
    require_permission('execute')

    print("Acesso concedido!")
```

## 🧪 Guia de Testes

- Testar a lógica de `is_authenticated` com arquivos de token ausentes, presentes, expirados e válidos.
- Testar a lógica de `get_user_role` para um usuário normal e para o `SUPER_ADMIN`.
- Testar `has_permission` para diferentes papéis e permissões, incluindo o wildcard `*`.
- Mockar o `keyring` para testar o armazenamento e a recuperação do token.
- Testar os guards `require_auth` e `require_permission` para garantir que eles levantam `typer.Exit` quando as condições não são satisfeitas.

## ❗ Pontos de Atenção e Melhoria

- **Credenciais Hardcoded (Crítico):** `CLIENT_ID` e `CLIENT_SECRET` nunca devem estar no código-fonte. Devem ser carregados de um ambiente seguro.
- **Super Admin Hardcoded (Crítico):** O conceito de um super admin atrelado a um e-mail específico é extremamente perigoso e inflexível. O sistema de papéis precisa ser dinâmico e gerenciado externamente.
- **God Object (Grave):** A classe `AuthManager` viola o Princípio da Responsabilidade Única, misturando gerenciamento de estado, I/O de arquivos, lógica de permissões e até formatação de UI (`display_welcome`). Ela deveria ser dividida em classes menores e mais focadas.
- **Armazenamento Inseguro (Médio):** Os arquivos `token.json` e `user.json` são armazenados em texto plano, expondo metadados da sessão e PII do usuário. Esses arquivos deveriam ser criptografados.
- **Estado Global:** A instância `auth_manager` global dificulta os testes e o raciocínio sobre o código. A injeção de dependência seria uma abordagem muito superior.
