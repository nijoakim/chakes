include .env
export

.PHONY: all
all: run-engine

# === Lint ===

.PHONY: lint
lint: lint-engine lint-backend lint-frontend

.PHONY: lint-engine
lint-engine:
	uv run ruff check engine

.PHONY: lint-backend
lint-backend:
	uv run ruff check backend

.PHONY: lint-frontend
lint-frontend:
	cd frontend && npm run lint

# === Type check ===

.PHONY: typecheck
typecheck: typecheck-engine typecheck-backend typecheck-frontend

.PHONY: typecheck-engine
typecheck-engine:
	uv run ty check engine
	uv run --package engine mypy --config-file engine/pyproject.toml engine

.PHONY: typecheck-backend
typecheck-backend:
	uv run ty check backend
	cd backend && uv run --package backend mypy .

.PHONY: typecheck-frontend
typecheck-frontend:
	cd frontend && npm run type-check

# === Check (lint + typecheck) ===

.PHONY: check
check: lint typecheck

.PHONY: check-engine
check-engine: typecheck-engine

.PHONY: check-backend
check-backend: lint-backend typecheck-backend

.PHONY: check-frontend
check-frontend: lint-frontend typecheck-frontend

# === Format ===

.PHONY: format
format:
	uv run ruff format engine backend

.PHONY: format-check
format-check:
	uv run ruff format --check engine backend

.PHONY: fix
fix: format

# === Run ===

.PHONY: run-engine
run-engine: check-engine
	uv run python -m engine.chakes.engine.engine

.PHONY: run-backend
run-backend: check-engine check-backend
	uv run uvicorn chakes.backend.app:app --reload --port $(BACKEND_PORT)

.PHONY: run-frontend
run-frontend: check-frontend
	cd frontend && npm run dev

# === Test ===

.PHONY: test
test: test-engine test-backend

.PHONY: test-engine
test-engine: check-engine
	uv run --package engine python -m chakes.engine.unit_tests

.PHONY: test-backend
test-backend:
	uv run pytest backend/tests
