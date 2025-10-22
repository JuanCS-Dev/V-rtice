
# 📄 `vertice/commands/scan.py`

## 📋 Descrição

Este módulo define os comandos da CLI para operações de scanning de rede. Ele inclui funcionalidades para escanear portas, executar o Nmap, procurar vulnerabilidades e descobrir redes.

**IMPORTANTE:** No estado atual, este módulo é um **placeholder**. Nenhuma funcionalidade de scanning real está implementada. Os comandos simulam uma execução com `asyncio.sleep` e retornam dados falsos e hardcoded.

**Dependências Principais:**
- `typer`: Para a criação dos comandos da CLI.
- `output.py`: Para formatação da saída.
- `auth.py`: Para controle de acesso.

## 🏗️ Funções Públicas (Comandos da CLI)

### `ports(target, json_output, verbose)`

Simula um scan de portas abertas em um alvo (IP ou hostname).

**Parâmetros:**
- `target (str)`: O alvo a ser escaneado. (Obrigatório)
- `json_output (bool)`: Se `True`, exibe a saída em formato JSON. (Opcional)
- `verbose (bool)`: Se `True`, exibe logs de atividade. (Opcional)

**Lógica (Simulada):**
1.  Requer autenticação.
2.  Aguarda 2 segundos para simular o scan.
3.  Retorna uma lista hardcoded de portas (22, 80, 443, 3389).
4.  Exibe o resultado em uma tabela ou em JSON.

---

### `nmap(target, json_output, verbose)`

Simula a execução de um scan com Nmap em um alvo.

**Parâmetros:**
- `target (str)`: O alvo para o scan Nmap. (Obrigatório)
- `json_output (bool)`: Se `True`, exibe a saída em formato JSON. (Opcional)
- `verbose (bool)`: Se `True`, exibe logs de atividade. (Opcional)

**Lógica (Simulada):**
1.  Requer autenticação.
2.  Aguarda 3 segundos.
3.  Retorna uma string de texto que se assemelha a um output do Nmap.
4.  Exibe o resultado como texto puro ou JSON.

---

### `vulns(target, json_output, verbose)`

Simula um scan de vulnerabilidades em um alvo.

**Parâmetros:**
- `target (str)`: O alvo a ser escaneado. (Obrigatório)
- `json_output (bool)`: Se `True`, exibe a saída em formato JSON. (Opcional)
- `verbose (bool)`: Se `True`, exibe logs de atividade. (Opcional)

**Lógica (Simulada):**
1.  Requer autenticação.
2.  Aguarda 4 segundos.
3.  Retorna uma lista hardcoded de vulnerabilidades (CVEs).
4.  Exibe o resultado em uma tabela ou em JSON.

---

### `network(json_output)`

Placeholder para um futuro comando de descoberta de rede. Atualmente, apenas exibe uma mensagem "coming soon".

## 💡 Exemplos de Uso

**Escanear portas de um host:**
```bash
vcli scan ports example.com
```

**Executar um scan Nmap e ver o resultado em JSON:**
```bash
vcli scan nmap scanme.nmap.org --json
```

**Procurar vulnerabilidades em um alvo:**
```bash
vcli scan vulns 192.168.1.1
```

## 🧪 Guia de Testes

Como o módulo é um placeholder, os testes atuais só podem verificar se os comandos executam sem erros e retornam os dados hardcoded esperados.

**Para a implementação real, os testes deveriam incluir:**
1.  **Testes Unitários:**
    - Mockar as chamadas a ferramentas externas (como o binário `nmap`).
    - Verificar se os argumentos do usuário são corretamente sanitizados e passados para os comandos subjacentes.
    - Testar a lógica de parsing do output das ferramentas de scan.

2.  **Testes de Integração:**
    - Executar scans contra um ambiente de teste controlado.
    - Validar se os resultados retornados correspondem ao estado real da rede de teste.
    - Testar o comportamento com alvos inválidos ou inacessíveis.

## ❗ Pontos de Atenção e Melhoria

- **Funcionalidade Inexistente (Crítico):** O débito técnico deste módulo é máximo. Nenhuma das funcionalidades principais está implementada. A prioridade número um é substituir a lógica simulada por integrações reais com ferramentas de scanning.
- **Vulnerabilidade de Injeção de Comando (Crítico):** A futura implementação do comando `nmap` apresenta um risco altíssimo de injeção de comando. O argumento `target` **NUNCA** deve ser passado diretamente para uma shell. É imperativo usar métodos de execução de sub-processo seguros que separem o comando de seus argumentos para prevenir que um input como `example.com; rm -rf /` seja executado.
- **Falta de Validação de Entrada:** Os alvos de scan não são validados. A implementação real deve validar se a entrada é um IP, um CIDR ou um hostname válido antes de iniciar o scan.
