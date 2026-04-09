SOURCE=$(wildcard */*.py)

.PHONY: all
all: run-game-engine

.PHONY: run-server
run-server:
	uv run uvicorn chakes.server.app:app --reload

.PHONY: type-check
type-check:
	uv run ruff $(SOURCE)

.PHONY: run-engine
run-game-engine: type-check
	uv run python -m chakes.engine.game_engine
