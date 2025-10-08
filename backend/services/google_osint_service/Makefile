# google_osint_service
.PHONY: help install dev test lint format fix clean update
help:
	@echo "Commands: install dev test lint format fix clean update"
install:
	uv pip sync requirements.txt
dev:
	uv pip install -e ".[dev]"
test:
	PYTHONPATH=. python -m pytest -v --tb=short
lint:
	ruff check .
format:
	ruff format .
fix:
	ruff check . --fix && ruff format .
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage coverage.xml
update:
	uv pip compile pyproject.toml -o requirements.txt
