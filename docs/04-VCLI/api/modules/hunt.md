
# 📄 `vertice/commands/hunt.py`

## 📋 Descrição

Este módulo agrupa os comandos da CLI focados em operações de *Threat Hunting* (Caça a Ameaças). Ele oferece ferramentas para buscar Indicadores de Comprometimento (IOCs), gerar timelines de incidentes e realizar análises de pivoteamento.

**IMPORTANTE:** No estado atual, este módulo é um **placeholder**. Quase todas as suas funcionalidades são simuladas e retornam dados hardcoded.

**Dependências Principais:**
- `typer`: Para a criação dos comandos da CLI.
- `output.py`: Para formatação da saída.
- `auth.py`: Para controle de acesso.

## 🏗️ Funções Públicas (Comandos da CLI)

### `search(query, json_output, verbose)`

Simula a busca por IOCs em fontes de inteligência com base em uma query.

**Parâmetros:**
- `query (str)`: A query de busca (ex: um domínio, IP, hash). (Obrigatório)
- `json_output (bool)`: Se `True`, exibe a saída em formato JSON. (Opcional)
- `verbose (bool)`: Se `True`, exibe logs de atividade. (Opcional)

**Lógica (Simulada):**
1.  Requer autenticação.
2.  Aguarda 2 segundos.
3.  Retorna uma lista hardcoded de IOCs relacionados à query.
4.  Exibe o resultado em uma tabela ou em JSON.

---

### `timeline(incident_id, last, json_output, verbose)`

Simula a geração de uma timeline de eventos para um determinado incidente.

**Parâmetros:**
- `incident_id (str)`: O ID do incidente a ser investigado. (Obrigatório)
- `last (str)`: O período de tempo a ser considerado (ex: "24h", "7d"). (Opcional, padrão: "24h")
- `json_output (bool)`: Se `True`, exibe a saída em formato JSON. (Opcional)
- `verbose (bool)`: Se `True`, exibe logs de atividade. (Opcional)

**Lógica (Simulada):**
1.  Requer autenticação.
2.  Aguarda 3 segundos.
3.  Retorna uma lista hardcoded de eventos de timeline.
4.  Exibe o resultado em uma tabela ou em JSON.

---

### `pivot(ioc, json_output, verbose)`

Simula uma análise de pivoteamento em um IOC para encontrar entidades relacionadas.

**Parâmetros:**
- `ioc (str)`: O IOC a ser usado como ponto de partida para a análise. (Obrigatório)
- `json_output (bool)`: Se `True`, exibe a saída em formato JSON. (Opcional)
- `verbose (bool)`: Se `True`, exibe logs de atividade. (Opcional)

**Lógica (Simulada):**
1.  Requer autenticação.
2.  Aguarda 2 segundos.
3.  Retorna uma lista hardcoded de entidades relacionadas.
4.  Exibe o resultado em uma tabela ou em JSON.

---

### `correlate(ioc1, ioc2, json_output)`

Placeholder para um futuro comando de correlação entre dois IOCs. Atualmente, apenas exibe uma mensagem "coming soon".

## 💡 Exemplos de Uso

**Buscar por um domínio malicioso:**
```bash
vcli hunt search "evil-domain.com"
```

**Gerar a timeline de um incidente das últimas 48 horas:**
```bash
vcli hunt timeline INC-12345 --last 48h
```

**Pivotar a partir de um endereço de IP:**
```bash
vcli hunt pivot 123.45.67.89
```

## 🧪 Guia de Testes

Como o módulo é um placeholder, os testes atuais se limitam a verificar a execução dos comandos e o retorno dos dados simulados.

**Para a implementação real, os testes deveriam incluir:**
1.  **Testes Unitários:**
    - Mockar os conectores de backend (ex: SIEM, Threat Intel Platform).
    - Verificar se a `query` do comando `search` é corretamente sanitizada e passada para o backend.
    - Testar a lógica de parsing dos diferentes tipos de IOCs.

2.  **Testes de Integração:**
    - Executar os comandos contra um ambiente de dados de teste.
    - Validar que a correlação e o pivoteamento encontram relações conhecidas nos dados de teste.
    - Testar o comando `timeline` com diferentes períodos de tempo.

## ❗ Pontos de Atenção e Melhoria

- **Funcionalidade Inexistente (Crítico):** Assim como o módulo `scan`, este módulo é quase inteiramente composto por débito técnico. As funcionalidades de *threat hunting*, que são o núcleo de uma ferramenta de cibersegurança, não estão implementadas.
- **Vulnerabilidade de Injeção (Potencial/Alta):** A implementação real do comando `search` deve tratar a `query` do usuário com extremo cuidado para evitar vulnerabilidades de injeção (SQLi, Command Injection, etc.), dependendo de como o backend realiza a busca.
- **Falta de Validação de Entrada:** As entradas (`query`, `incident_id`, `ioc`) não são validadas, o que pode levar a erros ou comportamento inesperado na implementação real.
