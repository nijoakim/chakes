# High priority:
- Show text and freeze the game when winning.
- Show legal moves (light green)
- When creating a game, add the option to decide cooldowns (needs read pieces from engine and 1).
- När man skapar så bestämmer man cooldowns (reqires ability to read pieces from engine and present to client).

# Medium priority:
- New game (with new game ID) with the same player
- Move logs in engine that is exposed to client

# Low priority:
- Add the following to the UI
    - Right-click: Perform legal move
    - Left-click:
        - On illegal move: Select new piece
        - On legal move:   Move
    - Escape: Deselect

# Bugs:
- King can capture pieces even though will be attacked.
- King can castle condition applies to the wrong flank.
- Back-end should not return 500 for illegal move (4xx).
