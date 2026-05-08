# High priority:
- frontend/backend: adapt to changes in engine refactor (or tell Joakim to revert them)

# Medium priority:
- frontend: display check and anti-check messages

# Low priority:
+ engine: Generalize en passant moves
+ engine: Support locusts
    + The two items above are tricky because captures don't occur at destination and is therefore potentially not uniquely determined from destination
- frontend: Add possibility to play non-orthodoxly-sized boards (testable for knighted chess)
- frontend: hotkeys
    - letter:      selects first piece on the file whose letter was pushed above currently selected piece
    - number:      selects piece that started on base row based on which file it started on
    - ctrl+number: reassigns numer hotkey
    - space:       if only one legal move, perform said move

# Bugs:
