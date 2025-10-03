
# 📄 `vertice/utils/output.py`

## 📋 Descrição

Este módulo é um utilitário central para toda a saída da CLI. Ele é um "God Module" que lida com uma vasta gama de responsabilidades de UI, incluindo:
- Impressão de mensagens padronizadas (sucesso, erro, aviso, info).
- Formatação de dados em JSON e Tabelas.
- Geração de spinners de progresso.
- Criação de prompts de entrada estilizados (texto, senha, confirmação, seleção).
- Formatação de saídas específicas de domínio (análise de IP, resposta da IA Maximus).

Ele se baseia fortemente nas bibliotecas `rich` e `questionary` para criar uma experiência de usuário visualmente atraente e interativa.

## 🌎 Variáveis Globais

- `console (Console)`: Uma instância global da classe `Console` da biblioteca `rich`, usada para toda a impressão no terminal.

## 🏗️ Funções Públicas

### Funções de Mensagens
- `print_success(message)`: Imprime uma mensagem de sucesso com um ícone ✅.
- `print_error(message, title)`: Imprime uma mensagem de erro dentro de um painel vermelho ✗.
- `print_warning(message, title)`: Imprime um aviso dentro de um painel amarelo ⚠.
- `print_info(message)`: Imprime uma mensagem informativa com um ícone ℹ️.

### Funções de Formatação de Dados
- `output_json(data)`: Imprime um dicionário ou lista como JSON formatado com syntax highlighting.
- `print_table(data, title)`: Renderiza um dicionário ou lista de dicionários como uma tabela `rich` estilizada.
- `print_maximus_response(data)`: Tenta de forma inteligente renderizar a resposta da IA, detectando se é JSON ou Markdown/texto.
- `format_ip_analysis(data)`: Uma função de formatação altamente especializada que cria uma tabela detalhada para os resultados da análise de IP.

### Funções de Interação com o Usuário
- `spinner_task(message)`: Um context manager que exibe um spinner enquanto uma tarefa está em execução.
- `styled_input(prompt, password, default)`: Exibe um prompt de entrada de texto estilizado.
- `styled_confirm(prompt, default)`: Exibe um prompt de confirmação (Sim/Não) estilizado.
- `styled_select(prompt, choices)`: Exibe um menu de seleção de múltipla escolha estilizado.

### Funções Auxiliares
- `create_panel(content, title, border_style)`: Cria um painel `rich` padronizado.
- `get_threat_color(level)`: Retorna uma string de cor com base em um nível de ameaça.

## 💡 Exemplo de Uso

```python
from .output import spinner_task, styled_input, print_success, print_error

name = styled_input("Qual é o seu nome?")

try:
    with spinner_task(f"Processando para {name}..."):
        # time.sleep(2)
        pass
    print_success(f"Processo para {name} concluído.")
except Exception as e:
    print_error(str(e))
```

## 🧪 Guia de Testes

- Testar cada função de `print_*` para garantir que ela renderiza sem erros.
- Testar `print_table` com listas vazias, dicionários e listas de dicionários.
- Testar `print_maximus_response` com payloads que contêm JSON válido, JSON inválido e texto puro.
- Mockar o `questionary` para testar as funções `styled_*` sem exigir interação manual, verificando se elas retornam os valores corretos.

## ❗ Pontos de Atenção e Melhoria

- **God Module (Crítico):** A principal fraqueza deste módulo é a violação massiva do Princípio da Responsabilidade Única. Ele faz de tudo um pouco relacionado à UI. Isso o torna um gargalo para o desenvolvimento, difícil de manter e de testar.
  - **Remediação:** Dividir o módulo em vários menores e mais focados: `ui/messaging.py` (para `print_success`, etc.), `ui/formatters.py` (para `print_table`, `format_ip_analysis`), e `ui/prompts.py` (para `styled_input`, etc.).
- **Duplicação de Código (Alta):** A lógica para criar os retângulos de prompt em `styled_input`, `styled_confirm` e `styled_select` é quase idêntica e deveria ser extraída para uma função auxiliar.
- **Estilos Hardcoded:** Todas as cores e estilos estão fixos no código, dificultando a criação de temas ou a alteração da aparência da CLI. Uma abordagem melhor seria carregar os estilos de um arquivo de configuração de tema.
- **Acoplamento de Domínio:** Funções como `format_ip_analysis` e `print_maximus_response` contêm lógica de formatação específica de um domínio. Elas estariam melhor localizadas nos seus respectivos módulos de comando (`ip.py`, `maximus.py`) ou em um submódulo de formatação específico, para que o `output.py` permaneça genérico.
