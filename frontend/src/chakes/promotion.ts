// TODO: server should provide promotable pieces
/** Pieces a pawn may promote to, guessed from the game's piece names. */
export function promotablePieces(pieceNames: string[]): string[] {
  return pieceNames.filter((n) => !/pawn|king/i.test(n))
}
