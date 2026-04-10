SOURCE=$(wildcard */*.py)

.PHONY: all
all: run-game-engine

.PHONY: run-backend
run-server:
	uv run uvicorn chakes.backend.app:app --reload

.PHONY: type-check
type-check:
	uv run ty .

.PHONY: run-engine
run-game-engine: type-check
	uv run python -m chakes.engine.game_engine
