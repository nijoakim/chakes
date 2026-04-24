# High priority:
- Show text and freeze the game when winning.
- Show legal moves (light green)
- When creating a game, add the option to decide cooldowns (needs read pieces from engine and present to client).

# Medium priority:
- New game (with new game ID) with the same player
- Refractor game engine to have a position object instead of relying on tuples and string conversions

# Low priority:
- Add the following to the UI
    - Right-click: Perform legal move
    - Left-click:
        - On illegal move: Select new piece
        - On legal move:   Move
    - Escape: Deselect
- When creating a game, add the option to select game type (Orthodox, Chess 960, Anti Chess, and more)
- When creating a game, add the checkbox to play upside-down chess


# Bugs:
- Back-end should not return 500 for illegal move (4xx).
