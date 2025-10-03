
# 📈 Plano de Refatoração: MÉDIA PRIORIDADE (Ações para o Próximo Mês)

Estes itens de refatoração abordam a performance, a qualidade do código e a experiência do desenvolvedor. Embora não sejam tão urgentes quanto os itens críticos e de alta prioridade, resolvê-los tornará a aplicação mais rápida, robusta e agradável de se trabalhar.

---

### 1. Implementar o Sistema de Cache

- **Descrição do Problema:** O módulo `utils/cache.py` é um placeholder vazio. A aplicação não faz cache de nenhuma chamada de API, resultando em requisições repetidas para os mesmos recursos, o que aumenta a latência e a carga nos serviços de backend.
- **Impacto Atual:** **MÉDIO.** A performance da CLI é prejudicada, especialmente ao solicitar repetidamente informações sobre o mesmo indicador (ex: o mesmo IP).
- **Solução Proposta:**
    1.  A dependência `diskcache` já está no `requirements.txt`. Utilize-a.
    2.  Implementar os métodos `get`, `set` e `clear` na classe `Cache` em `utils/cache.py`, usando uma instância de `diskcache.Cache` para o armazenamento real.
    3.  Integrar o cache nos conectores ou na camada de comando. Por exemplo, antes de fazer uma chamada de API em `IPIntelConnector.analyze_ip`, verificar se o resultado para aquele IP já está no cache e não expirou.
    4.  Adicionar um comando `vcli cache clear` para permitir que os usuários limpem o cache manualmente.
- **Esforço Estimado:** 3-4 horas
- **Risco da Correção:** Baixo.

---

### 2. Otimizar Comandos de Ação em Massa (Bulk)

- **Descrição do Problema:** O comando `vcli ip bulk` processa os IPs de forma sequencial, em um loop `for`. Isso é extremamente ineficiente e não tira proveito da natureza assíncrona da aplicação.
- **Impacto Atual:** **BAIXO a ALTO (depende do uso).** Para listas pequenas, o impacto é baixo. Para listas com centenas ou milhares de IPs, o comando se torna inutilizável devido ao tempo de execução.
- **Solução Proposta:**
    1.  Refatorar a lógica do comando `bulk`.
    2.  Criar uma lista de todas as tarefas assíncronas a serem executadas (uma para cada chamada a `connector.analyze_ip`).
    3.  Usar `asyncio.gather(*tasks)` para executar todas as requisições em paralelo.
    4.  Processar os resultados após todas as tarefas terem sido concluídas.
- **Esforço Estimado:** 2-3 horas
- **Risco da Correção:** Baixo.

---

### 3. Abstrair Estilos da UI e Criar um Sistema de Temas

- **Descrição do Problema:** Todas as cores e estilos usados pela biblioteca `rich` estão hardcoded nos arquivos de comando e em `utils/output.py`. Isso torna difícil alterar a aparência da CLI ou criar temas (ex: um tema claro e um escuro).
- **Impacto Atual:** **BAIXO.** É um problema puramente estético e de manutenibilidade da UI.
- **Solução Proposta:**
    1.  Criar um dicionário de "tema" no arquivo de configuração `config.yaml`.
        ```yaml
        theme:
          primary_color: "bright_cyan"
          success_color: "green"
          error_color: "red"
          panel_border_style: "bright_cyan"
        ```
    2.  Refatorar o módulo `output.py` e outros componentes de UI para ler as cores e estilos deste dicionário de configuração em vez de usar strings hardcoded.
    3.  Isso permitiria que os usuários personalizassem a aparência da CLI simplesmente editando seu arquivo `config.yaml`.
- **Esforço Estimado:** 4-6 horas
- **Risco da Correção:** Baixo.

---

### 4. Refatorar para Injeção de Dependência

- **Descrição do Problema:** A aplicação depende de instâncias globais para `config` e `auth_manager`. Isso é um anti-pattern que torna o código mais difícil de testar e entender, pois as dependências não são explícitas.
- **Impacto Atual:** **BAIXO.** Afeta principalmente a qualidade do código e a experiência do desenvolvedor, não o usuário final diretamente.
- **Solução Proposta:**
    1.  Remover as instâncias globais.
    2.  Criar um "contexto" ou um "container de dependências" que é instanciado no ponto de entrada da aplicação (`cli.py`).
    3.  Passar este objeto de contexto para os comandos que precisam dele. O `typer` tem mecanismos para lidar com isso (ex: `ctx.obj`).
    4.  Os comandos então acessariam a configuração e o gerenciador de autenticação através do objeto de contexto, em vez de importá-los globalmente.
- **Esforço Estimado:** 5-7 horas
- **Risco da Correção:** Médio. Requer uma mudança estrutural na forma como as dependências são gerenciadas e passadas pela aplicação.
