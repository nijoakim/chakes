# High priority:

# Medium priority:
- frontend: display check and anti-check messages
+ engine: Optimization: Parse the moveset string only once
+ engine: Optimization: Add possibility to revert a move in order to not have to copy the board excessively

# Low priority:
+ engine: Generalize en passant moves
+ engine: Support locusts
    + The two items above are tricky because captures don't occur at destination and is therefore potentially not uniquely determined from destination
- frontend: hotkeys
    - letter:      selects first piece on the file whose letter was pushed above currently selected piece
    - number:      selects piece that started on base row based on which file it started on
    - ctrl+number: reassigns numer hotkey
    - space:       if only one legal move, perform said move

# Bugs:
