
# 🕵️ Caso de Uso: Análise de Inteligência de IP

Este documento descreve o fluxo de usuário para os comandos relacionados à análise de IP.

## 1. Análise de IP Único (`vcli ip analyze`)

**Jornada do Usuário:**
Um analista de segurança precisa investigar um endereço de IP suspeito que encontrou em um log.

- **Comando:** `vcli ip analyze <IP_ADDRESS>`
- **Exemplo:** `vcli ip analyze 8.8.8.8`

### Fluxo de Execução

1.  **Entrada:** O usuário fornece um endereço de IP como argumento na linha de comando.
2.  **Validação (Cliente):**
    - O `typer` parseia o argumento.
    - **(Falha Atual):** Nenhuma validação de formato de IP é feita no cliente.
3.  **Autenticação:**
    - A função `require_auth()` é chamada.
    - O `AuthManager` verifica se um token válido e não expirado existe em `~/.vertice/auth/token.json`.
    - Se não autenticado, a aplicação encerra com uma mensagem de erro.
4.  **Processamento Interno:**
    - Uma instância do `IPIntelConnector` é criada.
    - Uma verificação de saúde (`health_check`) é feita contra o serviço de IP Intelligence para garantir que ele está online.
    - O método `analyze_ip(ip_address)` do conector é chamado. Isso envia uma requisição POST para o endpoint `/api/ip/analyze` do serviço de backend.
5.  **Dependências Externas:**
    - **Serviço de Autenticação:** (Atualmente simulado) Necessário para validar o acesso.
    - **Serviço de IP Intelligence:** O microserviço real que executa a análise.
6.  **Saída:**
    - **Padrão:** Uma tabela rica (`rich.Table`) é exibida no console com informações de geolocalização, reputação e rede.
    - **Com `--json`:** A resposta JSON bruta da API é impressa no console com syntax highlighting.
    - **Com `--quiet`:** Apenas o nível de ameaça (ex: `CLEAN`, `MALICIOUS`) é impresso como texto puro.
7.  **Efeitos Colaterais:**
    - O resultado da API pode ser armazenado em cache (funcionalidade atualmente não implementada).

### Edge Cases e Tratamento de Erros

- **Entrada Inválida:**
  - **IP Malformado:** Se o usuário fornecer uma string que não é um IP (ex: `vcli ip analyze not-an-ip`), a aplicação atualmente envia a string para o backend. O backend provavelmente retornará um erro. A CLI deveria validar o formato do IP antes de enviar.
- **Timeouts:**
  - O `httpx.AsyncClient` na `BaseConnector` tem um timeout padrão (10s). Se a API não responder a tempo, uma `httpx.TimeoutException` será levantada e capturada pelo `except Exception`, resultando em uma mensagem de erro genérica.
- **Falhas de Rede:**
  - Se o serviço estiver inacessível, o `health_check` falhará e uma mensagem de erro clara ("IP Intelligence service is offline") será exibida.
- **Serviço Offline:**
  - Tratado pelo `health_check` no início da execução do comando.
- **Token Expirado/Inválido:**
  - O `require_auth()` falhará e instruirá o usuário a fazer login novamente.

---

## 2. Análise de IP em Massa (`vcli ip bulk`)

**Jornada do Usuário:**
Um analista precisa verificar a reputação de uma longa lista de endereços de IP exportada de um firewall.

- **Comando:** `vcli ip bulk <FILE_PATH>`
- **Exemplo:** `vcli ip bulk ./lista_de_ips.txt`

### Fluxo de Execução

1.  **Entrada:** O usuário fornece o caminho para um arquivo de texto. O arquivo deve conter um IP por linha.
2.  **Validação (Cliente):**
    - **(Falha de Segurança):** O caminho do arquivo não é sanitizado, levando a uma vulnerabilidade de **Path Traversal**.
3.  **Autenticação:** Idêntico ao `ip analyze`.
4.  **Processamento Interno:**
    - O arquivo é aberto e lido linha por linha.
    - O comando itera sobre a lista de IPs e, para **cada IP**, executa a mesma lógica do `ip analyze` de forma **sequencial**.
    - **(Falha de Performance):** A execução sequencial torna este comando extremamente lento para arquivos grandes.
5.  **Saída:**
    - **Padrão:** Uma série de tabelas ricas, uma para cada IP, separadas por uma linha.
    - **Com `--json`:** Um grande array JSON contendo os resultados de todas as análises.

### Edge Cases e Tratamento de Erros

- **Arquivo Inexistente:** O `open(file, 'r')` levantará uma `FileNotFoundError`, que será capturada pelo `except Exception` e exibida como uma mensagem de erro genérica.
- **Arquivo Vazio:** O código verifica se a lista de IPs está vazia e exibe uma mensagem de aviso.
- **Linhas Malformadas:** Linhas vazias são ignoradas. Linhas com texto que não é um IP serão enviadas para a API, resultando em erros individuais para essas linhas.
