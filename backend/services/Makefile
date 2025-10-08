# adaptive_immunity_service autonomous_investigation_service ip_intelligence_service malware_analysis_service memory_consolidation_service narrative_analysis_service offensive_gateway predictive_threat_hunting_service reflex_triage_engine strategic_planning_service threat_intel_service chemical_sensing_service edge_agent_service ssl_monitor_service api_gateway
.PHONY: help install dev lint format fix clean update
help:
	@echo "Commands: install dev lint format fix clean update"
install:
	uv pip sync requirements.txt
dev:
	uv pip install -e ".[dev]"
lint:
	ruff check .
format:
	ruff format .
fix:
	ruff check . --fix && ruff format .
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
update:
	uv pip compile pyproject.toml -o requirements.txt
