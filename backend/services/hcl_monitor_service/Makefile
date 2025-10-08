# hcl_monitor_service
.PHONY: help install dev lint format fix clean update check
help:
	@echo "Commands: install dev lint format fix clean update check"
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
check:
	@echo "⚠️ No tests available - manual validation required"
	@python -m py_compile *.py 2>/dev/null || true
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage coverage.xml
update:
	uv pip compile pyproject.toml -o requirements.txt
