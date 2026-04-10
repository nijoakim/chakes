SOURCE=$(wildcard */*.py)

include .env
export

.PHONY: all
all: run-game-engine

.PHONY: run-backend
run-backend:
	uv run uvicorn chakes.backend.app:app --reload --port $(BACKEND_PORT)

.PHONY: run-frontend
run-frontend:
	cd frontend && npm run dev

.PHONY: type-check
type-check:
	uv run ty .

.PHONY: run-engine
run-game-engine: type-check
	uv run python -m chakes.engine.game_engine
