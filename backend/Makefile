.PHONY: install migrate run test lint fmt

install:
	uv sync

migrate:
	uv run alembic upgrade head

run:
	uv run uvicorn midinecromancer.main:app --reload --port 8000

test:
	uv run pytest

lint:
	uv run ruff check src/ tests/

fmt:
	uv run ruff format src/ tests/

lint-fix:
	uv run ruff check --fix src/ tests/
	uv run ruff format src/ tests/

