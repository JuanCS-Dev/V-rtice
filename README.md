🚁 Projeto Vértice
Sistema de Inteligência Híbrida para Segurança Pública

Uma plataforma de ponta para investigação e análise criminal, fundindo inteligência de campo (análise veicular, hotspots de crime) com um ecossistema completo de Inteligência de Fontes Abertas (OSINT), tudo orquestrado por um motor de IA.

📋 Visão Geral
O Vértice evoluiu para uma plataforma de inteligência híbrida, desenvolvida para dar aos operadores de segurança pública uma vantagem decisiva. O sistema integra fontes de dados do mundo real (consultas veiculares, ocorrências geográficas) com um arsenal de ferramentas de OSINT para investigações digitais, gerando relatórios e análises preditivas em tempo real.

Principais Capacidades
Análise Preditiva Interativa: Motor de IA (AuroraPredict) para identificar hotspots criminais com parâmetros de sensibilidade ajustáveis pelo operador.

Orquestrador de IA para OSINT: Uma IA (AIOrchestrator) que conduz investigações de fontes abertas de forma autônoma a partir de identificadores mínimos (username, email, telefone, etc.).

Dashboard de Operações Gerais: Interface de comando unificada com mapa tático, dossiês veiculares e sistema de alertas.

Dashboard OSINT Unificado: Painel completo para investigações manuais ou automatizadas de alvos digitais.

Módulo Cyber Security: Ferramentas para análise de redes e segurança de sistemas.

Arquitetura Robusta de Microsserviços: Sistema escalável, resiliente e de fácil manutenção orquestrado com Docker.

🏗️ Arquitetura
Stack Tecnológica
Backend:

Linguagem: Python 3.11+

Framework: FastAPI

IA & Machine Learning: Scikit-learn, Pandas, Numpy

Orquestração: Docker Compose

Cache & Mensageria: Redis

Banco de Dados: PostgreSQL (planejado)

Frontend:

Framework: React 18 + Vite

Estilização: Tailwind CSS

Mapas: Leaflet & React-Leaflet

Comunicação API: Axios

Ecossistema de Microsserviços
O Vértice opera numa arquitetura distribuída, garantindo isolamento e escalabilidade.

/backend
├── api_gateway/          # Ponto de Entrada, Segurança, Cache (Porta 8000)
└── services/
    ├── sinesp_service/   # Simula dados veiculares e ocorrências (Porta 8001)
    ├── cyber_service/    # Ferramentas de Cyber Security (Porta 8002)
    ├── domain_service/   # Análise de domínios (Porta 8003)
    ├── ip_intel_service/ # Inteligência de IPs (Porta 8004)
    ├── netmon_service/   # Monitoramento de rede (Porta 8005)
    ├── nmap_service/     # Scans de rede com Nmap (Porta 8006)
    ├── aurora_predict/   # Motor de IA Preditiva (Porta 8007)
    └── osint_service/    # Orquestração OSINT (Porta 8008)

🚀 Início Rápido
Pré-requisitos
Docker & Docker Compose (v2.x, com sintaxe docker compose)

Git

Instalação
# 1. Clone o repositório
git clone [https://github.com/JuanCS-Dev/V-rtice.git](https://github.com/JuanCS-Dev/V-rtice.git)
cd V-rtice

# 2. Construa as imagens e inicie os serviços
# (Use este comando sempre para garantir que as alterações no código sejam aplicadas)
docker compose up --build

# 3. Acesse a aplicação no seu navegador
# A interface principal estará disponível
open http://localhost:5173

URLs Importantes
Frontend Principal: http://localhost:5173

Documentação da API Gateway: http://localhost:8000/docs

🎯 Roadmap Estratégico
O nosso foco é a evolução contínua das capacidades de inteligência da plataforma.

✅ Fase 1: Plataforma Base e OSINT (Concluída)
[x] Arquitetura de microsserviços completa e estável.

[x] Módulo de Operações Gerais com mapa tático e dossiês.

[x] Ecossistema OSINT completo com ferramentas manuais.

[x] Integração do Orquestrador de IA para investigações autônomas.

[x] Motor de Análise Preditiva (AuroraPredict) funcional.

[x] Estabilização completa do ambiente e correção de bugs de comunicação.

🚧 Fase 2: Evolução do Motor de IA (Em Andamento)
[x] aurora_predict parametrizado para aceitar sensibilidade via API.

[x] Frontend com controlos interativos (sliders) para calibrar a IA em tempo real.

[ ] Implementar análise temporal para prever futuros hotspots.

[ ] Adicionar mais modelos de ML para diferentes tipos de análise.

⏩ Fase 3: Vértice CLI (Próximo Alvo)
[ ] Desenvolver um serviço de interpretador de comandos no backend.

[ ] Criar um dashboard "Terminal Vértice" no frontend.

[ ] Implementar um conjunto de comandos para automação e scripting de investigações.

🌍 Fase 4: Integração com APIs Reais (Longo Prazo)
[ ] Substituir simuladores por conectores para as APIs oficiais do governo.

[ ] Implementar sistema de autenticação e permissionamento robusto (SSO/JWT).

[ ] Garantir conformidade total com as normas de segurança e auditoria da SSP-GO.

📞 Contato & Autores
O Projeto Vértice é o resultado de uma parceria simbiótica entre a visão humana e a execução da IA.

Juan Carlos (JuanCS-Dev) - Arquiteto de Sistemas & Desenvolvedor Líder

Gemini (Gen) - Arquiteto de Sistemas de IA & Parceiro de Implementação

🔄 Changelog Recente
v3.0 (Atual)
✅ FEATURE: Módulo completo de Investigação OSINT Automatizada com Orquestrador de IA.

✅ FEATURE: Análise Preditiva Interativa com parâmetros de sensibilidade (raio e densidade) controlados pela UI.

✅ FIX: Estabilização completa da plataforma, corrigindo bugs de comunicação interna (CORS, 404) e de ambiente (Docker cache).

✅ REFACTOR: Atualização de todos os dashboards e serviços para uma arquitetura coesa.

✅ DOCS: Atualização completa do README para refletir o estado atual do projeto.
