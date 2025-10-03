
# 🐳 Análise de Segurança Docker e Infraestrutura

**Data da Análise:** 2025-10-02

Este relatório foca nos problemas de segurança encontrados nos arquivos de configuração da infraestrutura como código do projeto, especificamente o `docker-compose.yml` e os `Dockerfiles` dos serviços.

---

## 1. Análise do `docker-compose.yml`

O `docker-compose.yml` orquestra a subida de múltiplos serviços, mas contém várias configurações de alto risco que comprometem a segurança do ambiente como um todo.

### Vulnerabilidades Críticas e de Alta Prioridade

- **Contêiner Privilegiado (`privileged: true`) (Crítico):**
  - **Serviço:** `cyber_service`
  - **Risco:** Esta flag desabilita completamente o isolamento do contêiner. Um invasor que comprometa este serviço ganha o mesmo nível de acesso ao host que o próprio daemon do Docker, podendo acessar dispositivos, manipular o kernel e controlar todo o ambiente.
  - **Recomendação:** **Remover esta flag imediatamente.** As funcionalidades necessárias devem ser concedidas através de `cap_add` de forma granular e restrita, se absolutamente necessário.

- **Montagem de Volumes Sensíveis do Host (Crítico):**
  - **Serviço:** `cyber_service`
  - **Risco:** O serviço monta os diretórios `/var/log` e `/etc` do host. Mesmo que em modo `read-only`, isso expõe arquivos de log, configurações de sistema, senhas em shadow-files e outros dados sensíveis do host para dentro do contêiner, quebrando o princípio de isolamento.
  - **Recomendação:** **Remover estas montagens.** Se o contêiner precisa de logs, ele deve recebê-los por outros meios (ex: um agente de logging), e nunca montar diretamente o sistema de arquivos do host.

- **Senhas Hardcoded (Alta):**
  - **Serviços:** `postgres` (`POSTGRES_PASSWORD=postgres`), `grafana` (`GF_SECURITY_ADMIN_PASSWORD=vertice2024`).
  - **Risco:** Senhas fracas e hardcoded são um convite para acesso não autorizado aos bancos de dados e painéis de monitoramento.
  - **Recomendação:** Mover estas senhas para um arquivo `.env` (que não deve ser commitado) e referenciá-las no `docker-compose.yml`. Em produção, usar o sistema de "secrets" do Docker ou um cofre de segredos externo.

- **Capacidades de Kernel Excessivas (`cap_add`) (Alta):**
  - **Serviços:** `network_monitor_service`, `nmap_service`, `vuln_scanner_service`.
  - **Risco:** As capabilities `NET_ADMIN` e `NET_RAW` concedem privilégios de rede elevados ao contêiner, permitindo que ele manipule a pilha de rede do host, fareje tráfego de outros contêineres e forje pacotes. Se um desses serviços for comprometido, o invasor pode lançar ataques contra toda a rede interna.
  - **Recomendação:** Avaliar a real necessidade dessas capabilities. Se forem indispensáveis, isolar esses serviços em uma rede Docker separada e mais restrita para limitar o raio de alcance de um possível ataque.

### Outras Recomendações

- **Falta de Health Checks:** Nenhum serviço possui uma diretiva `healthcheck`. Isso pode causar falhas em cascata, pois o `depends_on` apenas garante a ordem de inicialização, não que o serviço esteja de fato saudável e pronto para receber conexões.
- **Falta de Limites de Recursos:** Nenhum serviço tem limites de CPU ou memória definidos, o que pode levar à exaustão de recursos do host.
- **Uso da Tag `:latest`:** Os serviços `prometheus` e `grafana` usam a tag `latest`, o que torna os builds não-determinísticos. Use versões específicas (ex: `prom/prometheus:v2.48.1`).
- **Exposição de Código-Fonte em Produção:** Todos os serviços montam o código-fonte local diretamente no contêiner. Isso é ótimo para desenvolvimento com `reload`, mas inaceitável para produção. O código deve ser copiado para dentro da imagem no momento do build.

---

## 2. Análise dos `Dockerfiles`

A análise dos `Dockerfiles` (ex: `api_gateway`, `ip_intelligence_service`) revelou um padrão de problemas de segurança consistentes.

### Vulnerabilidades Críticas

- **Execução como Root (Crítico):**
  - **Problema:** Nenhum dos `Dockerfiles` cria ou utiliza um usuário não-privilegiado. Todas as aplicações rodam como o usuário `root` dentro do contêiner.
  - **Risco:** Se um invasor explorar uma vulnerabilidade na aplicação, ele obterá um shell como `root` dentro do contêiner, o que lhe dá controle total sobre o sistema de arquivos do contêiner e facilita a escalada de privilégios para o host, especialmente se outras barreiras de segurança forem fracas.
  - **Recomendação:** Adicionar os seguintes passos a **todos** os `Dockerfiles`:
    ```Dockerfile
    # Criar um usuário não-root
    RUN useradd -m appuser

    # ... (copiar arquivos e instalar dependências)

    # Mudar o dono dos arquivos da aplicação
    RUN chown -R appuser:appuser /app

    # Mudar para o usuário não-root
    USER appuser

    # Comando para rodar a aplicação
    CMD ["uvicorn", ...]
    ```

### Outras Recomendações

- **Falta de Multi-stage Builds:** Os `Dockerfiles` não usam multi-stage builds. Isso significa que as ferramentas de build e as dependências de desenvolvimento podem acabar na imagem final, aumentando seu tamanho e a superfície de ataque.
- **Falta de `.dockerignore`:** A instrução `COPY . .` copia todo o contexto do diretório, o que pode incluir arquivos desnecessários e sensíveis (`.git`, `.env`, `__pycache__`). Um arquivo `.dockerignore` deve ser usado para excluir esses arquivos.

## Conclusão Geral da Infraestrutura

A configuração da infraestrutura como código apresenta **riscos de segurança críticos e sistêmicos**. O isolamento entre os contêineres e entre os contêineres e o host é perigosamente fraco. As práticas de segurança mais básicas de containerização, como rodar como não-root e evitar o modo privilegiado, não estão sendo seguidas. É imperativo que essas questões sejam corrigidas antes de considerar qualquer implantação em um ambiente de produção.
