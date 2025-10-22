
# 📄 `vertice/commands/auth.py`

## 📋 Descrição

Este módulo fornece os comandos da CLI para gerenciar a autenticação e o status do usuário. Ele lida com o login (simulado), logout e a verificação do usuário atualmente autenticado.

**IMPORTANTE:** A funcionalidade de login neste módulo é um **placeholder completamente inseguro**. Ele não realiza uma autenticação real, permitindo que qualquer pessoa se passe por qualquer usuário.

**Dependências Principais:**
- `typer`: Para a criação dos comandos da CLI.
- `auth_manager`: A instância do gerenciador de autenticação de `utils/auth.py`.
- `output.py`: Para a criação de prompts de entrada estilizados.

## 🏗️ Funções Públicas (Comandos da CLI)

### `login(email)`

Simula um fluxo de autenticação com Google OAuth2. **NÃO É SEGURO.**

**Parâmetros:**
- `email (str)`: O e-mail a ser usado para a autenticação simulada. Se não for fornecido, será solicitado ao usuário. (Opcional)

**Lógica (Simulada):**
1.  Solicita o e-mail do usuário se não for fornecido.
2.  Pede confirmação ao usuário.
3.  Gera dados de usuário e um token de acesso **falsos** com base no e-mail fornecido.
4.  Chama `auth_manager.save_auth_data` para salvar os dados falsos, efetivamente "autenticando" o usuário sem qualquer verificação.

---

### `logout()`

Realiza o logout do usuário, removendo os dados de autenticação armazenados.

**Lógica:**
1.  Verifica se o usuário está logado.
2.  Pede confirmação para o logout.
3.  Chama `auth_manager.logout()` para limpar os tokens e os arquivos de usuário.

---

### `whoami()`

Exibe informações detalhadas sobre o usuário atualmente autenticado, incluindo e-mail, nome, role e permissões.

**Lógica:**
1.  Verifica se o usuário está autenticado.
2.  Obtém os dados do usuário e do seu role através do `auth_manager`.
3.  Formata e exibe as informações em uma tabela rica.

---

### `status()`

Fornece uma verificação rápida do status de autenticação.

**Lógica:**
1.  Verifica se o usuário está autenticado.
2.  Exibe uma mensagem simples indicando o status de login e o e-mail/role do usuário, se aplicável.

## 💡 Exemplos de Uso

**Realizar um login (simulado) como super admin:**
```bash
vcli auth login --email juan.brainfarma@gmail.com
```

**Verificar quem está logado:**
```bash
vcli auth whoami
```

**Fazer logout:**
```bash
vcli auth logout
```

## 🧪 Guia de Testes

**Para a implementação atual (simulada):**
- Testar se `vcli auth login --email test@example.com` cria os arquivos de token e usuário.
- Testar se `vcli auth whoami` exibe as informações corretas após o login simulado.
- Testar se `vcli auth logout` remove os arquivos de autenticação.

**Para uma implementação real e segura:**
- Os testes se tornariam muito mais complexos, envolvendo o mock do fluxo OAuth2 completo.
- Seria necessário mockar um servidor HTTP local para receber o callback do OAuth2.
- Validar a troca do `authorization_code` por um `access_token`.
- Testar a proteção contra CSRF (Cross-Site Request Forgery) validando o parâmetro `state`.

## ❗ Pontos de Atenção e Melhoria

- **Vulnerabilidade de Autenticação Falsa (Crítica):** A maior prioridade é substituir o fluxo de login simulado por uma implementação real e segura do Google OAuth2. O estado atual permite que qualquer pessoa assuma a identidade de qualquer usuário, incluindo o super administrador, comprometendo toda a segurança da aplicação.
- **Débito Técnico:** Todo o módulo de login é um débito técnico. A funcionalidade principal de segurança da aplicação não existe.
- **UX do Login:** O fluxo de login simulado ainda pede confirmação manual. Um fluxo OAuth2 real seria mais fluido, abrindo o navegador e lidando com o redirecionamento automaticamente.
