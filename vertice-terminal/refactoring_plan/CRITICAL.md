
# 🚨 Plano de Refatoração: CRÍTICO (Ações para as Próximas 24 Horas)

Esta lista contém as vulnerabilidades e débitos técnicos mais graves que comprometem fundamentalmente a segurança e a funcionalidade do Vértice CLI. A correção destes itens é de **prioridade máxima**.

---

### 1. Remover a Autenticação Simulada (Mocked Authentication)

- **Descrição do Problema:** O comando `vcli auth login` não realiza uma autenticação real. Ele permite que qualquer pessoa se "autentique" com qualquer e-mail, incluindo o do super administrador, simplesmente fornecendo-o como argumento. Isso anula completamente a segurança da aplicação.
- **Impacto Atual:** **COMPROMETIMENTO TOTAL.** Qualquer pessoa pode ganhar acesso de super administrador.
- **Solução Proposta:**
    1.  Remover completamente o código do fluxo de login simulado em `vertice/commands/auth.py`.
    2.  Implementar um fluxo OAuth2 real e funcional. Isso envolve:
        - Abrir o navegador para a página de consentimento do Google.
        - Iniciar um servidor web local temporário para receber o callback com o `authorization_code`.
        - Trocar o `authorization_code` por um `access_token` real fazendo uma requisição segura ao Google.
        - Implementar proteção contra CSRF usando o parâmetro `state`.
    3.  Até que o fluxo real seja implementado, o comando `login` deve ser desativado ou exibir uma mensagem clara de que é inseguro e não funcional.
- **Esforço Estimado:** 4-6 horas
- **Risco da Correção:** Baixo. O risco de *não* corrigir é catastrófico.

---

### 2. Remover Credenciais e Papéis Hardcoded

- **Descrição do Problema:** Segredos (`CLIENT_ID`, `CLIENT_SECRET`) estão como placeholders no código-fonte (`utils/auth.py`). Pior, o e-mail do `SUPER_ADMIN` e a estrutura de `ROLES` estão hardcoded, criando um ponto único de falha e uma grave vulnerabilidade de segurança.
- **Impacto Atual:** **CRÍTICO.** Se o e-mail do super admin for comprometido, a aplicação inteira é comprometida. A gestão de papéis é impossível sem alterar o código.
- **Solução Proposta:**
    1.  Mover `CLIENT_ID` e `CLIENT_SECRET` para o arquivo de configuração (`config.yaml`), que por sua vez deve ser carregado de um local seguro e nunca commitado no repositório.
    2.  Remover a variável `SUPER_ADMIN` do código. O papel de super admin deve ser atribuído dinamicamente (ex: através de uma lista de e-mails na configuração ou em um banco de dados).
    3.  Externalizar a definição de `ROLES` para o arquivo de configuração, permitindo que eles sejam gerenciados sem modificar o código.
- **Esforço Estimado:** 2 horas
- **Risco da Correção:** Baixo.

---

### 3. Corrigir Vulnerabilidades de Path Traversal

- **Descrição do Problema:** Comandos como `vcli ip bulk` e `vcli adr analyze file` aceitam um caminho de arquivo do usuário e o usam diretamente (`open()`) ou o enviam para o backend. Isso permite que um usuário mal-intencionado leia arquivos arbitrários no sistema.
- **Impacto Atual:** **ALTO.** Exposição de arquivos sensíveis no sistema que executa a CLI ou no servidor de backend.
- **Solução Proposta:**
    1.  **Sanitização de Entrada:** Implementar uma função de utilitário que valide e sanitize todos os inputs de caminho de arquivo.
    2.  A função deve resolver o caminho absoluto e verificar se ele está dentro de um diretório base permitido e seguro.
    3.  Proibir o uso de `..` nos caminhos.
    4.  Aplicar esta função de sanitização imediatamente em todos os comandos que aceitam caminhos de arquivo como argumento.
- **Esforço Estimado:** 2-3 horas
- **Risco da Correção:** Baixo.

---

### 4. Implementar Comunicação Segura (HTTPS)

- **Descrição do Problema:** Toda a comunicação entre a CLI e os serviços de backend é feita via `http`, sem criptografia. Isso expõe todos os dados, incluindo tokens de autenticação, a ataques de Man-in-the-Middle.
- **Impacto Atual:** **CRÍTICO.** Qualquer pessoa na mesma rede pode interceptar e ler o tráfego, roubando tokens e dados sensíveis.
- **Solução Proposta:**
    1.  Atualizar as URLs base em todos os conectores e configurações para usar `https://`.
    2.  Garantir que os serviços de backend estejam configurados com certificados TLS/SSL válidos (mesmo que autoassinados para desenvolvimento local).
    3.  Configurar o `httpx.AsyncClient` na `BaseConnector` para verificar os certificados SSL por padrão.
- **Esforço Estimado:** 3-4 horas (depende da configuração do backend)
- **Risco da Correção:** Médio. Pode introduzir problemas de verificação de certificado se o ambiente não estiver configurado corretamente.
