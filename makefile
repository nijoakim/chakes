SOURCE=$(wildcard */*.py)

.PHONY: all
all: run-game-engine

.PHONY: type-check
type-check:
	mypy $(SOURCE)

.PHONY: run-game-engine
run-game-engine: type-check
	python3 game_engine/game_engine.py
