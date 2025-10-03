---
Documento de Visão e Roadmap Técnico – Projeto C.S. do Cerrado
Versão: 1.0
Data: 14 de setembro de 2025
Autor: Equipe de Arquitetura de Sistemas

Resumo Executivo
O Projeto C.S. do Cerrado visa desenvolver uma Plataforma Unificada de Inteligência Policial para o Estado de Goiás, inspirada na eficiência de sistemas de fusão de dados em tempo real. O objetivo é transformar dados brutos de múltiplas fontes (Boletins de Ocorrência, registros veiculares, vigilância, etc.) em inteligência acionável para otimizar investigações, prever atividades criminosas e aumentar a segurança pública, operando sempre dentro dos estritos limites legais e éticos.

1. Princípios de Arquitetura
A construção do sistema será guiada pelos seguintes princípios fundamentais:

Arquitetura de Microsserviços: O sistema será composto por serviços pequenos, independentes e focados em uma única responsabilidade de negócio (ingestão de dados, análise de vínculos, etc.). Isso promove escalabilidade, resiliência e manutenibilidade.

Design API-Centric: Todos os serviços se comunicarão através de APIs bem definidas e documentadas. O frontend será um consumidor dessas APIs, garantindo uma separação clara entre a lógica de negócio e a apresentação.

Segurança por Design (Security by Design): Mecanismos de autenticação, autorização, auditoria e conformidade com a LGPD serão integrados desde o início do projeto, não como uma camada posterior.

Containerização Total: Todos os serviços e dependências serão executados em contêineres Docker, garantindo paridade entre os ambientes de desenvolvimento, teste e produção.

Documentação como Código: A documentação da API será gerada automaticamente a partir do próprio código, garantindo que ela nunca fique desatualizada.

2. Stack Tecnológica (A Caixa de Ferramentas)
Componente	Tecnologia Escolhida	Justificativa
Backend (Microsserviços)	Python 3.11+ com FastAPI	Performance excepcional, sintaxe moderna, ecossistema robusto para IA/ML (Módulo Aurora), e geração automática de documentação OpenAPI, que é crucial para a integração com o frontend e outros sistemas.
Frontend (Console Web)	React com TypeScript	Componentização robusta, vasto ecossistema de bibliotecas (mapas, gráficos) e a segurança de tipos do TypeScript para construir uma UI complexa e de grande escala com menos bugs.
Banco de Dados Relacional	PostgreSQL 16+ com a extensão PostGIS	Padrão ouro para bancos de dados open-source. A extensão PostGIS oferece funcionalidades geoespaciais avançadas, essenciais para a plotagem de mapas, geofencing e análise de "mancha criminal".
Banco de Dados de Grafos	Neo4j	Especializado em armazenar e consultar dados de relacionamento complexos. Será o coração do Módulo Seriema para a análise de vínculos entre pessoas, veículos, locais e crimes de forma ultra-rápida.
Orquestração de Contêineres	Docker Compose (Dev) / Kubernetes (Prod)	Docker Compose para simplicidade no ambiente de desenvolvimento. Kubernetes para orquestração, escalabilidade e resiliência em um ambiente de produção crítico.
Mensageria / Event Stream	RabbitMQ ou Apache Kafka	Para a comunicação assíncrona entre os microsserviços. Essencial para desacoplar os serviços e garantir que o sistema continue funcionando mesmo que um componente falhe temporariamente.
CI/CD (Automação)	GitHub Actions	Integração nativa com o repositório de código, permitindo a automação de testes, builds de contêineres e deployments, garantindo um processo de entrega de software rápido e confiável.

Exportar para as Planilhas
3. Roadmap de Desenvolvimento
Fase 0: Alinhamento e Arquitetura (Concluída)
Objetivo: Definir a fundação do projeto, a stack tecnológica e a estrutura inicial.

Entregas Chave: Documento de visão, criação da estrutura de diretórios, inicialização do repositório Git, setup do primeiro serviço (api_gateway) com Docker.

Fase 1: MVP – O "Big Board" Digital (Prazo: 6 Meses)
Objetivo: Entregar a primeira versão funcional da plataforma, focada na visualização de dados de ocorrências e veículos.

Entregas Chave:

Módulo TÁTACA v1.0: Serviço de ingestão para Boletins de Ocorrência e dados do Detran.

Módulo CERRADO v1.0: Interface de mapa interativo que plota as ocorrências, com filtros básicos (data, tipo de crime).

Busca unificada por placa de veículo.

Detalhes Técnicos:

Desenvolvimento dos serviços tataca_ingestion e api_gateway.

Criação do schema inicial no PostgreSQL (tabelas ocorrencias, veiculos, pessoas).

Definição dos endpoints da API: GET /ocorrencias, GET /ocorrencias/{id}, GET /veiculos/{placa}.

Desenvolvimento do frontend em React com a biblioteca Leaflet ou Mapbox para o mapa.

Fase 2: Inteligência Conectada (Prazo: 6 Meses)
Objetivo: Introduzir a capacidade de análise de vínculos e enriquecer a base de dados.

Entregas Chave:

Módulo SERIEMA v1.0: Lançamento da visualização de gráfico de vínculos.

TÁTACA v2.0: Ingestão de novas fontes (ex: antecedentes criminais, sistema prisional).

Detalhes Técnicos:

Desenvolvimento do serviço seriema_graph com API para consultar o Neo4j.

Integração do tataca_ingestion para popular o Neo4j com nós (Pessoa, Veículo, Endereço) e arestas (Possui, EnvolvidoEm, ResideEm).

Endpoint GET /vinculos/{entidade_id} na API.

Desenvolvimento de um componente de visualização de grafos no frontend (ex: com D3.js ou vis.js).

Fase 3: Operações em Tempo Quase-Real (Prazo: 8 Meses)
Objetivo: Transformar a plataforma de uma ferramenta de análise para uma ferramenta de consciência situacional ao vivo.

Entregas Chave:

Integração com feeds de câmeras de segurança com leitores de placa (ANPR).

Sistema de alertas em tempo real (ex: "Veículo roubado detectado").

App móvel/tablet para viaturas (versão simplificada).

Detalhes Técnicos:

Uso de RabbitMQ/Kafka para processar o fluxo de eventos das câmeras.

Desenvolvimento de um serviço de "alerta" que consome esses eventos e dispara notificações (via WebSockets para o frontend).

Endpoint GET /alertas e uma conexão WebSocket para o console CERRADO.

Fase 4: Análise Preditiva e IA (Contínuo)
Objetivo: Utilizar a inteligência artificial para prever tendências e otimizar o policiamento.

Entregas Chave:

Módulo AURORA v1.0: Implementação de modelos de ML para prever "hotspots" de criminalidade.

Dashboards estratégicos para o comando.

Detalhes Técnicos:

Desenvolvimento do serviço aurora_predict, utilizando bibliotecas como Scikit-learn, Pandas e TensorFlow/PyTorch.

Criação de pipelines de treinamento de modelos (MLOps) utilizando os dados históricos do PostgreSQL.

Endpoint GET /predicao/hotspots?data={data}&regiao={regiao}.
