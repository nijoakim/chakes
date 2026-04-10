include .env
export

.PHONY: all
all: run-game-engine

.PHONY: lint
lint:
	uv run ruff check engine backend
	cd frontend && npm run lint

.PHONY: format
format:
	uv run ruff format engine backend

.PHONY: format-check
format-check:
	uv run ruff format --check engine backend

.PHONY: type-check
type-check:
	uv run ty check engine backend
	cd frontend && npm run type-check

.PHONY: check
check: lint format-check type-check

.PHONY: fix
fix: format

.PHONY: run-engine
run-engine: check
	uv run python -m chakes.engine.game_engine

.PHONY: run-backend
run-backend: check
	uv run uvicorn chakes.backend.app:app --reload --port $(BACKEND_PORT)

.PHONY: run-frontend
run-frontend: check
	cd frontend && npm run dev
