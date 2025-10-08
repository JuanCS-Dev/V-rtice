# immunis_cytotoxic_t_service - Makefile
.PHONY: help install dev lint format fix clean update

help:
	@echo "immunis_cytotoxic_t_service - Commands: install dev lint format fix clean update"

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
