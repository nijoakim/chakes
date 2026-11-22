/** Conventional promotion order; any other promotable piece follows alphabetically. */
const CONVENTIONAL_ORDER = ['Queen', 'Rook', 'Bishop', 'Knight']

function rank(name: string): number {
  const i = CONVENTIONAL_ORDER.indexOf(name)
  return i === -1 ? CONVENTIONAL_ORDER.length : i
}

// TODO: server should provide promotable pieces
/**
 * Pieces a pawn may promote to, guessed from the game's piece names, in a
 * deterministic order (independent of the order the server sends them in, so
 * both players see the same list).
 */
export function promotablePieces(pieceNames: string[]): string[] {
  return [...new Set(pieceNames.filter((n) => !/pawn|king/i.test(n)))]
    .sort((a, b) => rank(a) - rank(b) || a.localeCompare(b))
}
