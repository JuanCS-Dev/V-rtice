# 🎯 PLANO DE REFATORAÇÃO COMPLETA - PARA GEMINI EXECUTAR

**Executor:** Gemini Pro / Flash
**Complexidade:** ALTA
**Tempo Estimado:** 8-12 horas
**Objetivo:** Corrigir TODOS os 35 issues do relatório de análise

---

## 📋 INSTRUÇÕES GERAIS PARA O GEMINI

1. **EXECUTE SEQUENCIALMENTE**: Uma task de cada vez, na ordem apresentada
2. **NÃO PULE ETAPAS**: Mesmo que pareça trivial
3. **VALIDE CADA PASSO**: Execute testes após cada mudança
4. **CRIE BACKUPS**: Antes de refatorações grandes
5. **DOCUMENTE**: Adicione comentários explicando mudanças complexas

**FORMATO DE RESPOSTA ESPERADO:**
```
✅ TASK X.Y COMPLETA
- Arquivo(s) modificado(s): [lista]
- Mudanças: [descrição breve]
- Testado: [sim/não]
- Issues corrigidos: [números]
```

---

# 🔥 FASE 1: VULNERABILIDADES CRÍTICAS (PRIORIDADE MÁXIMA)

## TASK 1.1: Criptografar Token Storage
**Arquivo:** `vertice/utils/auth.py`
**Linhas:** 118, 135
**Severidade:** CRITICAL

### O que fazer:
```python
# ANTES (linha 118 - INSEGURO):
with open(self.token_file, 'w') as f:
    json.dump(token_data, f, indent=2)

# DEPOIS (SEGURO):
from cryptography.fernet import Fernet
import base64
import os

class SecureStorage:
    def __init__(self):
        # Gera ou carrega chave de criptografia
        key_file = Path.home() / '.vertice' / '.key'
        if key_file.exists():
            with open(key_file, 'rb') as f:
                self.key = f.read()
        else:
            self.key = Fernet.generate_key()
            key_file.parent.mkdir(exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(self.key)
            # Protege a chave
            os.chmod(key_file, 0o600)
        self.cipher = Fernet(self.key)
    
    def encrypt_and_save(self, data: dict, filepath: Path):
        json_data = json.dumps(data)
        encrypted = self.cipher.encrypt(json_data.encode())
        with open(filepath, 'wb') as f:
            f.write(encrypted)
        os.chmod(filepath, 0o600)
    
    def load_and_decrypt(self, filepath: Path) -> dict:
        with open(filepath, 'rb') as f:
            encrypted = f.read()
        decrypted = self.cipher.decrypt(encrypted)
        return json.loads(decrypted.decode())
```

### Passos:
1. Adicione `cryptography` ao `requirements.txt`
2. Crie classe `SecureStorage` em `vertice/utils/secure_storage.py`
3. Modifique `AuthManager.save_auth_data()` para usar `SecureStorage`
4. Modifique `AuthManager.load_token_data()` para usar `SecureStorage`
5. Migre dados existentes (se houver) para formato criptografado
6. Teste: `vertice auth login` e `vertice auth whoami`

**Validação:**
```bash
# Token file deve estar criptografado
cat ~/.vertice/token.json  # Deve mostrar gibberish, não JSON
```

---

## TASK 1.2: Sanitizar Command Injection
**Arquivo:** `vertice/commands/adr.py`
**Linha:** 166
**Severidade:** CRITICAL

### O que fazer:
```python
# ANTES (linha 166 - PERIGOSO):
result = await connector._post("/api/adr/analyze/process", json={"command": cmd})

# DEPOIS (SEGURO):
from ..utils.file_validator import sanitize_command_arg

ALLOWED_COMMANDS = {
    'ps': ['ps', 'aux'],
    'netstat': ['netstat', '-an'],
    'top': ['top', '-b', '-n', '1'],
    'df': ['df', '-h'],
    'free': ['free', '-m']
}

def sanitize_process_command(cmd: str) -> list:
    """
    Converte comando string em lista segura.
    Apenas comandos whitelisted são permitidos.
    """
    cmd = cmd.strip()
    
    # Verifica se está na whitelist
    if cmd not in ALLOWED_COMMANDS:
        raise ValueError(f"Command not allowed: {cmd}")
    
    return ALLOWED_COMMANDS[cmd]

# No comando:
try:
    safe_cmd_list = sanitize_process_command(cmd)
    result = await connector._post("/api/adr/analyze/process", 
                                   json={"command": safe_cmd_list})
except ValueError as e:
    print_error(str(e))
    console.print("\n[yellow]Allowed commands:[/yellow]")
    for cmd_name in ALLOWED_COMMANDS:
        console.print(f"  - {cmd_name}")
    return
```

### Passos:
1. Crie `ALLOWED_COMMANDS` dict no topo de `adr.py`
2. Crie função `sanitize_process_command()`
3. Modifique o comando `analyze process` para usar sanitização
4. Adicione mensagem de erro amigável com lista de comandos permitidos
5. Teste com comando válido: `vertice adr analyze process ps`
6. Teste com comando inválido: `vertice adr analyze process "rm -rf /"`

**Validação:**
```bash
# Deve funcionar
vertice adr analyze process ps

# Deve ser bloqueado
vertice adr analyze process "whoami && cat /etc/passwd"
```

---

## TASK 1.3: Validar Path Traversal em ADR
**Arquivo:** `vertice/commands/adr.py`
**Linha:** 106
**Severidade:** HIGH

### O que fazer:
```python
# ANTES (linha 106):
result = await connector._post("/api/adr/analyze/file", 
                               json={"file_path": path})

# DEPOIS:
from ..utils.file_validator import sanitize_file_path, ValidationError

try:
    # Valida path localmente antes de enviar
    safe_path = sanitize_file_path(path)
    
    # Envia apenas o nome do arquivo, não o path completo
    # (backend deve ter seu próprio diretório seguro)
    filename = safe_path.name
    
    result = await connector._post("/api/adr/analyze/file", 
                                   json={"filename": filename})
except ValidationError as e:
    print_error(f"Invalid file path: {e}")
    return
```

### Passos:
1. Import `sanitize_file_path` de `file_validator.py`
2. Adicione try/except em todos os lugares que aceitam file paths
3. Envie apenas nome do arquivo (não path completo) para backend
4. Teste com path normal: `vertice adr analyze file ./test.py`
5. Teste com path traversal: `vertice adr analyze file ../../../etc/passwd`

**Validação:**
```bash
# Deve funcionar
echo "test" > /tmp/test.txt
vertice adr analyze file /tmp/test.txt

# Deve ser bloqueado
vertice adr analyze file ../../../../etc/passwd
```

---

# 🔥 FASE 2: ELIMINAR DUPLICAÇÃO (DECORATOR PATTERN)

## TASK 2.1: Criar Decorator Base
**Arquivo NOVO:** `vertice/utils/decorators.py`
**Severidade:** HIGH (afeta manutenibilidade)

### O que fazer:
```python
"""
Command decorators for Vertice CLI.
Eliminates code duplication across all command modules.
"""
import asyncio
import functools
from typing import Type, Callable, Any
from rich.console import Console
from .output import spinner_task, print_error, print_json
from .auth import require_auth

console = Console()


def with_connector(connector_class: Type, require_authentication: bool = True):
    """
    Decorator que automatiza:
    - Autenticação
    - Criação de connector
    - Health check
    - Error handling
    - Cleanup (close)
    
    Uso:
        @with_connector(IPIntelConnector)
        async def analyze(target: str, json_output: bool = False, **kwargs):
            # connector está disponível como kwargs['connector']
            result = await kwargs['connector'].analyze_ip(target)
            return result
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Autenticação
            if require_authentication:
                require_auth()
            
            # Cria connector
            connector = connector_class()
            
            async def async_wrapper():
                try:
                    # Health check
                    with spinner_task(f"Connecting to {connector.service_name}..."):
                        if not await connector.health_check():
                            print_error(f"{connector.service_name} is not available")
                            return None
                    
                    # Injeta connector nos kwargs
                    kwargs['connector'] = connector
                    
                    # Executa função original
                    result = await func(*args, **kwargs)
                    
                    return result
                    
                except Exception as e:
                    print_error(f"Error: {str(e)}")
                    return None
                    
                finally:
                    # Cleanup
                    await connector.close()
            
            # Executa async
            return asyncio.run(async_wrapper())
        
        return wrapper
    return decorator
```

### Passos:
1. Crie arquivo `vertice/utils/decorators.py`
2. Implemente decorator `@with_connector`
3. Adicione docstrings completas
4. NÃO modifique comandos ainda (próxima task)

---

## TASK 2.2: Refatorar Comando IP com Decorator
**Arquivo:** `vertice/commands/ip.py`
**Severidade:** HIGH

### O que fazer:
```python
# ANTES (linhas 20-60 - MUITO CÓDIGO DUPLICADO):
@app.command()
def analyze(
    target: Annotated[str, typer.Argument(help="IP address to analyze")],
    json_output: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    require_auth()
    
    async def _analyze():
        connector = IPIntelConnector()
        try:
            with spinner_task("Connecting..."):
                if not await connector.health_check():
                    print_error("Service not available")
                    return
            
            with spinner_task(f"Analyzing {target}..."):
                result = await connector.analyze_ip(target)
            
            if json_output:
                print_json(result)
            else:
                # formatação...
        except Exception as e:
            print_error(str(e))
        finally:
            await connector.close()
    
    asyncio.run(_analyze())


# DEPOIS (LIMPO E SIMPLES):
from ..utils.decorators import with_connector
from ..connectors.ip_intel import IPIntelConnector

@app.command()
@with_connector(IPIntelConnector)
async def analyze(
    target: Annotated[str, typer.Argument(help="IP address to analyze")],
    json_output: Annotated[bool, typer.Option("--json", "-j")] = False,
    connector=None,  # Injetado pelo decorator
):
    """Analyze IP address."""
    with spinner_task(f"Analyzing {target}..."):
        result = await connector.analyze_ip(target)
    
    if json_output:
        print_json(result)
    else:
        # formatação (mantém igual)
        console.print(f"IP: {result.get('ip')}")
        # ...
```

### Passos:
1. Import `@with_connector` no topo do arquivo
2. Remova toda a lógica de setup/teardown
3. Adicione `connector=None` nos parâmetros
4. Mantenha APENAS a lógica de negócio
5. Teste: `vertice ip analyze 8.8.8.8`

**Validação:**
- Comando deve funcionar identicamente
- Código deve ter ~50% menos linhas
- Nenhum print() ou error handling manual

---

## TASK 2.3: Refatorar TODOS os Outros Comandos
**Arquivos:** `scan.py`, `hunt.py`, `monitor.py`, `adr.py`, `malware.py`, `threat.py`
**Severidade:** HIGH

### O que fazer:
Repita o padrão da TASK 2.2 para CADA comando em CADA arquivo.

### Checklist:
- [ ] `scan.py`: ports, nmap, vulns, network (4 comandos)
- [ ] `hunt.py`: search, timeline, pivot, correlate (4 comandos)
- [ ] `monitor.py`: start, stop, events, stats, alerts, block (6 comandos)
- [ ] `adr.py`: status, metrics, analyze (3 comandos)
- [ ] `malware.py`: analyze, scan, report (3 comandos)
- [ ] `threat.py`: lookup, search (2 comandos)

**Total:** 22 comandos a refatorar

### Template para cada comando:
```python
@with_connector(ConnectorClass)
async def command_name(
    arg: Annotated[str, typer.Argument(...)],
    json_output: bool = False,
    connector=None,  # ← IMPORTANTE
):
    # APENAS lógica de negócio aqui
    result = await connector.método(arg)
    
    if json_output:
        print_json(result)
    else:
        # formatação específica
```

---

# 🔥 FASE 3: REFATORAR GOD OBJECTS

## TASK 3.1: Dividir utils/output.py
**Arquivo:** `vertice/utils/output.py`
**Severidade:** HIGH (God Object com ~500 linhas)

### Estrutura nova:
```
vertice/utils/
├── output/
│   ├── __init__.py          # Exports tudo
│   ├── formatters.py        # print_json, format_table, format_ip_analysis
│   ├── ui_components.py     # spinners, prompts, confirmations
│   ├── console_utils.py     # print_error, print_success, print_info
│   └── styles.py            # Cores, temas, estilos
```

### Passos:
1. Crie pasta `vertice/utils/output/`
2. **formatters.py**:
```python
"""Data formatters for CLI output."""
import json
from rich.console import Console
from rich.table import Table
from typing import Any, Dict

console = Console()

def print_json(data: Any) -> None:
    """Print data as formatted JSON."""
    console.print_json(data=data)

def format_table(data: list, columns: list, title: str = None) -> Table:
    """Create formatted table from data."""
    table = Table(title=title, show_header=True)
    
    for col in columns:
        table.add_column(col['name'], style=col.get('style', 'white'))
    
    for row in data:
        table.add_row(*[str(row.get(col['key'], 'N/A')) for col in columns])
    
    return table

# Mova format_ip_analysis, format_threat_data, etc. aqui
```

3. **ui_components.py**:
```python
"""Interactive UI components."""
from rich.console import Console
from rich.prompt import Prompt, Confirm
from contextlib import contextmanager

console = Console()

def styled_input(prompt: str, default: str = None) -> str:
    """Get user input with styled prompt."""
    return Prompt.ask(f"[cyan]{prompt}[/cyan]", default=default)

def styled_confirm(question: str, default: bool = False) -> bool:
    """Get yes/no confirmation."""
    return Confirm.ask(f"[yellow]{question}[/yellow]", default=default)

@contextmanager
def spinner_task(message: str):
    """Context manager for spinner."""
    with console.status(f"[cyan]{message}[/cyan]", spinner="dots"):
        yield
```

4. **console_utils.py**:
```python
"""Console output utilities."""
from rich.console import Console

console = Console()

def print_error(message: str) -> None:
    """Print error message."""
    console.print(f"[bold red]✗ {message}[/bold red]")

def print_success(message: str) -> None:
    """Print success message."""
    console.print(f"[bold green]✓ {message}[/bold green]")

def print_info(message: str) -> None:
    """Print info message."""
    console.print(f"[cyan]ℹ {message}[/cyan]")
```

5. **__init__.py**:
```python
"""Output utilities for Vertice CLI."""
from .formatters import print_json, format_table
from .ui_components import styled_input, styled_confirm, spinner_task
from .console_utils import print_error, print_success, print_info

__all__ = [
    'print_json',
    'format_table',
    'styled_input',
    'styled_confirm',
    'spinner_task',
    'print_error',
    'print_success',
    'print_info',
]
```

6. Atualize imports em TODOS os comandos:
```python
# ANTES:
from ..utils.output import print_json, spinner_task

# DEPOIS (IGUAL - funciona por causa do __init__.py):
from ..utils.output import print_json, spinner_task
```

---

## TASK 3.2: Dividir utils/auth.py
**Arquivo:** `vertice/utils/auth.py`
**Severidade:** HIGH (God Object com ~400 linhas)

### Estrutura nova:
```
vertice/utils/auth/
├── __init__.py
├── token_storage.py      # TokenStorage class
├── user_manager.py       # UserManager class  
├── permission_manager.py # PermissionManager, RBAC
└── auth_ui.py           # display_welcome, etc.
```

### Passos:
1. **token_storage.py**:
```python
"""Secure token storage using system keyring."""
import keyring
from pathlib import Path
from typing import Optional
from .secure_storage import SecureStorage

class TokenStorage:
    """Manages secure storage of OAuth tokens."""
    
    def __init__(self):
        self.service_name = "vertice-cli"
        self.storage = SecureStorage()
        self.token_file = Path.home() / '.vertice' / 'token_meta.enc'
    
    def save_token(self, email: str, token: str, expires_in: int):
        """Save token securely."""
        # Token vai pro keyring
        keyring.set_password(self.service_name, email, token)
        
        # Metadata criptografado
        metadata = {
            'email': email,
            'expires_in': expires_in,
            'created_at': time.time()
        }
        self.storage.encrypt_and_save(metadata, self.token_file)
    
    def get_token(self, email: str) -> Optional[str]:
        """Retrieve token from keyring."""
        return keyring.get_password(self.service_name, email)
    
    def delete_token(self, email: str):
        """Delete token."""
        keyring.delete_password(self.service_name, email)
        if self.token_file.exists():
            self.token_file.unlink()
```

2. **user_manager.py**:
```python
"""User information management."""
from pathlib import Path
from typing import Optional, Dict
from .secure_storage import SecureStorage

class UserManager:
    """Manages user data storage."""
    
    def __init__(self):
        self.storage = SecureStorage()
        self.user_file = Path.home() / '.vertice' / 'user.enc'
    
    def save_user(self, user_info: Dict):
        """Save user info encrypted."""
        self.storage.encrypt_and_save(user_info, self.user_file)
    
    def get_user(self) -> Optional[Dict]:
        """Get user info."""
        if not self.user_file.exists():
            return None
        return self.storage.load_and_decrypt(self.user_file)
    
    def delete_user(self):
        """Delete user data."""
        if self.user_file.exists():
            self.user_file.unlink()
```

3. **permission_manager.py**:
```python
"""Role-Based Access Control."""
import os
from typing import List, Dict

# Load from env
SUPER_ADMIN = os.getenv("SUPER_ADMIN_EMAIL")

ROLES = {
    "super_admin": {
        "permissions": ["*"],
        "level": 100
    },
    "admin": {
        "permissions": ["read", "write", "execute", "manage_users"],
        "level": 80
    },
    "analyst": {
        "permissions": ["read", "write", "execute"],
        "level": 50
    },
    "viewer": {
        "permissions": ["read"],
        "level": 10
    }
}

class PermissionManager:
    """Manages permissions and roles."""
    
    @staticmethod
    def get_user_role(email: str) -> str:
        """Determine user role based on email."""
        if email == SUPER_ADMIN:
            return "super_admin"
        # TODO: Load from database
        return "analyst"
    
    @staticmethod
    def has_permission(email: str, permission: str) -> bool:
        """Check if user has permission."""
        role = PermissionManager.get_user_role(email)
        perms = ROLES.get(role, {}).get('permissions', [])
        return '*' in perms or permission in perms
```

4. **auth_ui.py**:
```python
"""Authentication UI components."""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def display_welcome(user_info: dict, role: str):
    """Display welcome message after login."""
    # ... código de UI aqui
```

5. **__init__.py**:
```python
"""Authentication utilities."""
from .token_storage import TokenStorage
from .user_manager import UserManager
from .permission_manager import PermissionManager, ROLES, SUPER_ADMIN
from .auth_ui import display_welcome

class AuthManager:
    """Main authentication manager - facade pattern."""
    
    def __init__(self):
        self.tokens = TokenStorage()
        self.users = UserManager()
        self.permissions = PermissionManager()
    
    def save_auth_data(self, user_info, token, expires_in):
        email = user_info['email']
        self.tokens.save_token(email, token, expires_in)
        self.users.save_user(user_info)
    
    def is_authenticated(self) -> bool:
        user = self.users.get_user()
        if not user:
            return False
        token = self.tokens.get_token(user['email'])
        return token is not None
    
    def get_user_info(self):
        return self.users.get_user()
    
    def get_user_role(self):
        user = self.users.get_user()
        if not user:
            return None
        return self.permissions.get_user_role(user['email'])
    
    def logout(self):
        user = self.users.get_user()
        if user:
            self.tokens.delete_token(user['email'])
        self.users.delete_user()
    
    def display_welcome(self):
        user = self.users.get_user()
        role = self.get_user_role()
        display_welcome(user, role)

# Global instance
auth_manager = AuthManager()

def require_auth():
    """Decorator/function to require authentication."""
    if not auth_manager.is_authenticated():
        console.print("[red]Not authenticated. Run: vertice auth login[/red]")
        raise typer.Exit(1)

__all__ = ['auth_manager', 'require_auth', 'ROLES', 'SUPER_ADMIN']
```

---

# 🔥 FASE 4: CONFIGURAÇÃO E MAGIC NUMBERS

## TASK 4.1: Centralizar Portas em Config
**Arquivos NOVOS:** `.env.example`, `vertice/config/services.yaml`
**Severidade:** MEDIUM

### O que fazer:

1. **Crie `.env.example`**:
```bash
# Backend Services URLs
NMAP_SERVICE_URL=http://localhost:8010
VULN_SCANNER_SERVICE_URL=http://localhost:8015
NETWORK_MONITOR_SERVICE_URL=http://localhost:8009
THREAT_INTEL_SERVICE_URL=http://localhost:8013
IP_INTEL_SERVICE_URL=http://localhost:8004
MALWARE_SERVICE_URL=http://localhost:8017
ADR_CORE_SERVICE_URL=http://localhost:8011

# Google OAuth2
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8080

# Admin
SUPER_ADMIN_EMAIL=admin@example.com
```

2. **Modifique cada Connector**:
```python
# ANTES:
class NmapConnector(BaseConnector):
    def __init__(self, base_url: str = "http://localhost:8010"):
        super().__init__(base_url)

# DEPOIS:
import os

class NmapConnector(BaseConnector):
    def __init__(self, base_url: str = None):
        if base_url is None:
            base_url = os.getenv("NMAP_SERVICE_URL", "http://localhost:8010")
        super().__init__(base_url)
```

3. Faça isso para TODOS os conectores:
- [ ] NmapConnector
- [ ] VulnScannerConnector  
- [ ] NetworkMonitorConnector
- [ ] ThreatIntelConnector
- [ ] IPIntelConnector
- [ ] MalwareConnector
- [ ] ADRCoreConnector

---

# 🔥 FASE 5: TYPE HINTS E QUALIDADE

## TASK 5.1: Adicionar Type Hints Completos
**Arquivos:** TODOS os .py
**Severidade:** MEDIUM

### Template:
```python
# ANTES:
def analyze_ip(ip):
    result = self.client.get(f"/analyze/{ip}")
    return result.json()

# DEPOIS:
from typing import Dict, Any

def analyze_ip(self, ip: str) -> Dict[str, Any]:
    """
    Analyze IP address.
    
    Args:
        ip: IP address to analyze
        
    Returns:
        Dictionary with analysis results
        
    Raises:
        ValueError: If IP is invalid
        httpx.HTTPError: If request fails
    """
    result = self.client.get(f"/analyze/{ip}")
    return result.json()
```

### Prioridade:
1. Conectores (base.py e todos os filhos)
2. Utils (auth/, output/)
3. Comandos (commands/)

---

# 🔥 FASE 6: TESTES UNITÁRIOS

## TASK 6.1: Setup Pytest
**Arquivos NOVOS:** `tests/`, `pytest.ini`, `conftest.py`

```bash
mkdir -p tests/{unit,integration}
```

### pytest.ini:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --cov=vertice
    --cov-report=html
    --cov-report=term
```

### conftest.py:
```python
"""Pytest configuration and fixtures."""
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.fixture
def mock_connector():
    """Mock connector for testing."""
    connector = Mock()
    connector.health_check = AsyncMock(return_value=True)
    connector.close = AsyncMock()
    return connector

@pytest.fixture
def sample_ip_result():
    """Sample IP analysis result."""
    return {
        "ip": "8.8.8.8",
        "status": "success",
        "reputation": "clean",
        "location": "US"
    }
```

---

## TASK 6.2: Criar Testes para Conectores
**Arquivo:** `tests/unit/test_connectors.py`

```python
"""Tests for connector classes."""
import pytest
from unittest.mock import AsyncMock, patch
from vertice.connectors.ip_intel import IPIntelConnector

class TestIPIntelConnector:
    @pytest.mark.asyncio
    async def test_health_check_success(self):
        connector = IPIntelConnector()
        
        with patch.object(connector, '_get') as mock_get:
            mock_get.return_value = {"status": "operational"}
            
            result = await connector.health_check()
            
            assert result is True
            mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_ip_success(self, sample_ip_result):
        connector = IPIntelConnector()
        
        with patch.object(connector, '_post') as mock_post:
            mock_post.return_value = sample_ip_result
            
            result = await connector.analyze_ip("8.8.8.8")
            
            assert result["ip"] == "8.8.8.8"
            assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_analyze_invalid_ip_raises_error(self):
        connector = IPIntelConnector()
        
        with pytest.raises(ValueError):
            await connector.analyze_ip("invalid_ip")
```

**Target:** 80%+ coverage

---

# 📊 VALIDAÇÃO FINAL

Após TODAS as tasks, execute:

```bash
# 1. Linting
black vertice/ --check
flake8 vertice/
mypy vertice/

# 2. Security
bandit -r vertice/ -ll

# 3. Tests
pytest tests/ --cov=vertice --cov-report=term

# 4. Funcional
vertice auth login
vertice scan ports scanme.nmap.org
vertice hunt search malicious.com
vertice monitor stats
```

---

# ✅ CHECKLIST FINAL

- [ ] Vulnerabilidades CRITICAL: 0/4 (todas corrigidas)
- [ ] Vulnerabilidades HIGH: 0/15 (todas corrigidas)
- [ ] Duplicação de código: <10% (era 80%)
- [ ] God Objects: 0 (eram 2)
- [ ] Magic numbers: 0 (eram 7 ports hardcoded)
- [ ] Type hints: 100% (era 20%)
- [ ] Test coverage: 80%+ (era 0%)
- [ ] Security score: 9.5/10 (era 6.5/10)
- [ ] Maintainability: 9/10 (era 4/10)

**Status Esperado:** PRODUCTION READY 95%+

---

**GERADO POR:** Claude Sonnet 4.5
**PARA:** Gemini Pro/Flash
**DATA:** 2025-10-02
