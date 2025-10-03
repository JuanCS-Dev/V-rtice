# HCL Services - Makefile
# Comandos úteis para desenvolvimento

.PHONY: help up down build rebuild logs clean test health train

# Default target
.DEFAULT_GOAL := help

help: ## Mostra esta mensagem de ajuda
	@echo "HCL Services - Comandos disponíveis:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

up: ## Inicia todos os serviços
	docker-compose up -d
	@echo "✓ Serviços iniciados!"
	@echo "  - Knowledge Base: http://localhost:8000/health"
	@echo "  - Monitor: http://localhost:8001/health"
	@echo "  - Analyzer: http://localhost:8002/health"
	@echo "  - Planner: http://localhost:8003/health"
	@echo "  - Executor: http://localhost:8004/health"
	@echo "  - Grafana: http://localhost:3000 (admin/admin)"
	@echo "  - Prometheus: http://localhost:9090"

down: ## Para todos os serviços
	docker-compose down

build: ## Build de todas as imagens
	docker-compose build

rebuild: ## Rebuild e restart de todos os serviços
	docker-compose up -d --build

logs: ## Ver logs de todos os serviços
	docker-compose logs -f

logs-monitor: ## Ver logs do Monitor
	docker-compose logs -f hcl-monitor

logs-analyzer: ## Ver logs do Analyzer
	docker-compose logs -f hcl-analyzer

logs-planner: ## Ver logs do Planner
	docker-compose logs -f hcl-planner

logs-executor: ## Ver logs do Executor
	docker-compose logs -f hcl-executor

logs-kafka: ## Ver logs do Kafka
	docker-compose logs -f kafka

ps: ## Status dos serviços
	docker-compose ps

health: ## Verificar health de todos os serviços
	@echo "Verificando health dos serviços..."
	@echo ""
	@echo -n "Knowledge Base: "
	@curl -s http://localhost:8000/health | grep -q "healthy" && echo "✓ OK" || echo "✗ FAIL"
	@echo -n "Monitor: "
	@curl -s http://localhost:8001/health | grep -q "healthy" && echo "✓ OK" || echo "✗ FAIL"
	@echo -n "Analyzer: "
	@curl -s http://localhost:8002/health | grep -q "healthy" && echo "✓ OK" || echo "✗ FAIL"
	@echo -n "Planner: "
	@curl -s http://localhost:8003/health | grep -q "healthy" && echo "✓ OK" || echo "✗ FAIL"
	@echo -n "Executor: "
	@curl -s http://localhost:8004/health | grep -q "healthy" && echo "✓ OK" || echo "✗ FAIL"

train: ## Treinar todos os modelos ML
	@echo "Treinando modelos ML..."
	@echo ""
	@echo "1. SARIMA - CPU Forecasting (30 dias)"
	curl -X POST "http://localhost:8002/train/sarima/cpu_usage?days=30"
	@echo ""
	@echo "2. SARIMA - Memory Forecasting (30 dias)"
	curl -X POST "http://localhost:8002/train/sarima/memory_usage?days=30"
	@echo ""
	@echo "3. SARIMA - GPU Forecasting (30 dias)"
	curl -X POST "http://localhost:8002/train/sarima/gpu_usage?days=30"
	@echo ""
	@echo "4. Isolation Forest - Anomaly Detection (30 dias)"
	curl -X POST "http://localhost:8002/train/isolation_forest?days=30"
	@echo ""
	@echo "5. RL Agent - Resource Allocation (50k timesteps)"
	curl -X POST "http://localhost:8003/train/rl?timesteps=50000"
	@echo ""
	@echo "✓ Treinamento iniciado!"

test-fuzzy: ## Testar Fuzzy Logic Controller
	@echo "Testando Fuzzy Logic Controller..."
	@echo ""
	@echo "Cenário 1: Low usage (ENERGY_EFFICIENT)"
	curl -s "http://localhost:8003/fuzzy/test?cpu=20&memory=30&error_rate=5&latency=80" | jq
	@echo ""
	@echo "Cenário 2: High usage (HIGH_PERFORMANCE)"
	curl -s "http://localhost:8003/fuzzy/test?cpu=85&memory=78&error_rate=12&latency=450" | jq
	@echo ""
	@echo "Cenário 3: Medium usage (BALANCED)"
	curl -s "http://localhost:8003/fuzzy/test?cpu=50&memory=55&error_rate=15&latency=250" | jq

test-k8s: ## Testar operações Kubernetes (dry-run)
	@echo "Testando operações Kubernetes..."
	@echo ""
	@echo "1. Listar deployments"
	curl -s http://localhost:8004/deployments | jq
	@echo ""
	@echo "2. Testar scale (dry-run)"
	curl -s -X POST http://localhost:8004/scale \
		-H "Content-Type: application/json" \
		-d '{"service": "maximus_core", "target_replicas": 5}' | jq

kafka-topics: ## Listar Kafka topics
	docker exec -it hcl-kafka kafka-topics.sh \
		--bootstrap-server localhost:9092 --list

kafka-consume-metrics: ## Ver mensagens de métricas
	docker exec -it hcl-kafka kafka-console-consumer.sh \
		--bootstrap-server localhost:9092 \
		--topic system.telemetry.raw \
		--from-beginning

kafka-consume-predictions: ## Ver mensagens de predições
	docker exec -it hcl-kafka kafka-console-consumer.sh \
		--bootstrap-server localhost:9092 \
		--topic system.predictions \
		--from-beginning

kafka-consume-actions: ## Ver mensagens de ações
	docker exec -it hcl-kafka kafka-console-consumer.sh \
		--bootstrap-server localhost:9092 \
		--topic system.actions \
		--from-beginning

db-shell: ## Entrar no PostgreSQL
	docker exec -it hcl-postgres psql -U hcl_user -d hcl_knowledge

db-metrics: ## Ver últimas métricas no banco
	docker exec -it hcl-postgres psql -U hcl_user -d hcl_knowledge \
		-c "SELECT * FROM system_metrics ORDER BY timestamp DESC LIMIT 10;"

db-decisions: ## Ver últimas decisões no banco
	docker exec -it hcl-postgres psql -U hcl_user -d hcl_knowledge \
		-c "SELECT * FROM hcl_decisions ORDER BY timestamp DESC LIMIT 10;"

clean: ## Remove todos os containers e volumes (ATENÇÃO!)
	@echo "ATENÇÃO: Isso vai remover todos os dados!"
	@read -p "Confirma? (yes/no): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		docker-compose down -v --rmi all; \
		echo "✓ Limpeza completa realizada!"; \
	else \
		echo "✗ Operação cancelada"; \
	fi

restart-monitor: ## Restart apenas o Monitor
	docker-compose restart hcl-monitor

restart-analyzer: ## Restart apenas o Analyzer
	docker-compose restart hcl-analyzer

restart-planner: ## Restart apenas o Planner
	docker-compose restart hcl-planner

restart-executor: ## Restart apenas o Executor
	docker-compose restart hcl-executor

shell-monitor: ## Shell no container Monitor
	docker exec -it hcl-monitor bash

shell-analyzer: ## Shell no container Analyzer
	docker exec -it hcl-analyzer bash

shell-planner: ## Shell no container Planner
	docker exec -it hcl-planner bash

shell-executor: ## Shell no container Executor
	docker exec -it hcl-executor bash
