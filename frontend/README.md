

# Package structure

This package lives in a monorepo, but is self-contained.
The following structure allows `import chakes.engine` from the backend.

```
chakes/
    backend/
    engine/
    frontend/
        ...
```

## Architecture

Vue 3 + TypeScript + Vite. State via Pinia, routing via vue-router.

```
src/
├── views/         # Route-level components. Own lifecycle (WS connect, store subscriptions).
├── stores/        # Pinia stores: session, catalog, lobby, game.
├── services/      # Transport only — no state.
│                  #   api.ts         REST wrappers
│                  #   gameSocket.ts  Typed WebSocket emitter
├── components/
│   ├── chakes/     # Presentational primitives (ChakesBoard, ChakesSquare, PieceSprite, PromotionBar).
│   │              # Take props, emit events. No store imports.
│   └── lobby/     # Feature-coupled (LobbyForm, GameSetup). May read stores.
├── composables/   # useBoardOrientation, useKeyboardShortcuts.
└── assets/        # SVGs + pieceImages.ts lookup.
```

Data flow: WS message → `gameSocket` emits typed event → `useGameStore` updates state → views/components react.

## Set up dev environment

Requires node 24. Install with e.g. `sudo snap install node --classic --channel 24` (ubuntu).
