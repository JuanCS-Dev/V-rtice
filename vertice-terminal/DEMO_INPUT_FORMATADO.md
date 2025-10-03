# 🎨 DEMONSTRAÇÃO: INPUT FORMATADO ESTILO GEMINI CLI

## ✅ IMPLEMENTADO COM SUCESSO!

### 📦 Funções Disponíveis em `vertice/utils/output.py`:

#### 1. **`styled_input(prompt, password=False, default="")`**
Input de texto com retângulo bonito

```python
from vertice.utils.output import styled_input

# Input normal
ip_address = styled_input("Enter IP address to analyze")

# Input com senha (oculto)
api_key = styled_input("Enter API key", password=True)

# Input com valor padrão
domain = styled_input("Enter domain", default="example.com")
```

**Visual:**
```
┌──────────────────────────────────┐
│ Enter IP address to analyze      │
└──────────────────────────────────┘

➤ 8.8.8.8
```

---

#### 2. **`styled_confirm(prompt, default=True)`**
Confirmação (Sim/Não) com retângulo bonito

```python
from vertice.utils.output import styled_confirm

# Confirmar ação
proceed = styled_confirm("Do you want to continue?")

if proceed:
    # Execute action
    pass
```

**Visual:**
```
┌────────────────────────────────┐
│ Do you want to continue?       │
└────────────────────────────────┘

➤ Yes
```

---

#### 3. **`styled_select(prompt, choices)`**
Seleção de opções com retângulo bonito

```python
from vertice.utils.output import styled_select

# Seleção de opções
scan_type = styled_select(
    "Select scan type",
    choices=["Quick Scan", "Full Scan", "Custom Scan"]
)
```

**Visual:**
```
┌──────────────────────┐
│ Select scan type     │
└──────────────────────┘

➤
  Quick Scan
❯ Full Scan
  Custom Scan
```

---

#### 4. **`spinner_task(message)`**
Spinner quadradinho durante tarefas

```python
from vertice.utils.output import spinner_task
import asyncio

async def analyze():
    with spinner_task("Analyzing IP address..."):
        await asyncio.sleep(2)  # Simula trabalho
        result = {"status": "complete"}

    return result
```

**Visual:**
```
■□□□ Analyzing IP address...
□■□□ Analyzing IP address...
□□■□ Analyzing IP address...
□□□■ Analyzing IP address...
```

---

#### 5. **`format_ip_analysis(data, console)`**
Formatter rico para análise de IP

```python
from vertice.utils.output import format_ip_analysis

data = {
    "ip": "8.8.8.8",
    "geolocation": {
        "country": "United States",
        "city": "Mountain View",
        "isp": "Google LLC",
        "asn": "AS15169"
    },
    "reputation": {
        "score": 5,
        "threat_level": "low",
        "description": "Trusted Infrastructure"
    },
    "network": {
        "open_ports": [53, 443],
        "ptr": "dns.google"
    }
}

format_ip_analysis(data)
```

**Visual:**
```
╭───────────────────────────────────────────────────╮
│        🔍 IP Analysis: 8.8.8.8                    │
│                                                   │
│  📍 Location                                      │
│    ├─ Country      United States                 │
│    ├─ City         Mountain View                 │
│    ├─ ISP          Google LLC                    │
│    └─ ASN          AS15169                       │
│                                                   │
│  🛡️  Threat Assessment                            │
│    ├─ Score        5/100 (LOW)                   │
│    ├─ Status       ✓ CLEAN                       │
│    └─ Reputation   Trusted Infrastructure        │
│                                                   │
│  🌐 Network                                       │
│    ├─ Open Ports   [53, 443]                     │
│    └─ PTR Record   dns.google                    │
╰───────────────────────────────────────────────────╯

⏱  Analysis completed
💾 Cached for 1 hour
```

---

## 🎯 EXEMPLO DE USO COMPLETO

```python
# vertice/commands/ip.py (exemplo atualizado)
import typer
import asyncio
from rich.console import Console
from typing_extensions import Annotated
from ..connectors.ip_intel import IPIntelConnector
from ..utils.output import (
    styled_input,
    styled_confirm,
    spinner_task,
    format_ip_analysis,
    print_json,
    print_error
)

console = Console()

app = typer.Typer(name="ip", help="🔍 IP Intelligence operations")

@app.command()
def analyze_interactive():
    """
    Interactive IP analysis with styled inputs.

    Example:
        vcli ip analyze-interactive
    """
    async def _analyze():
        # Input formatado estilo Gemini
        ip_address = styled_input("Enter IP address to analyze")

        if not ip_address:
            print_error("IP address is required")
            return

        # Confirmar antes de executar
        proceed = styled_confirm(f"Analyze {ip_address}?")

        if not proceed:
            console.print("[yellow]Analysis cancelled[/yellow]")
            return

        # Análise com spinner
        connector = IPIntelConnector()
        try:
            with spinner_task(f"Analyzing {ip_address}..."):
                result = await connector.analyze_ip(ip_address)

            # Formatar e exibir resultado
            format_ip_analysis(result)

        finally:
            await connector.close()

    asyncio.run(_analyze())
```

---

## 🔥 FEATURES IMPLEMENTADAS

✅ **Input com retângulo bonito** (estilo Gemini CLI)
✅ **Spinners quadradinhos modernos** (aesthetic)
✅ **Confirmações formatadas**
✅ **Seleções com menu bonito**
✅ **Formatters ricos para IP Analysis**
✅ **Cores e ícones consistentes**
✅ **Totalmente customizável**

---

## 💡 PRÓXIMOS PASSOS

1. Implementar formatters para:
   - `format_threat_intel()` - Threat intelligence
   - `format_adr_metrics()` - ADR metrics
   - `format_malware_report()` - Malware analysis

2. Adicionar validação inline nos inputs:
   ```python
   ip = styled_input("Enter IP", validator=validate_ip)
   ```

3. Criar progress bars para operações longas:
   ```python
   with styled_progress("Scanning 100 IPs...") as progress:
       # work
   ```

**IMPLEMENTAÇÃO COMPLETA E FUNCIONAL! 🚀**
