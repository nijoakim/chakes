import type { PieceInstance } from '@/services/types'
import type { Square } from './square'

// The server pushes whole boards and never says which move happened, so moves
// are recovered by diffing two consecutive boards. Between two pushes several
// moves may have happened (both sides move at once, castling moves two
// pieces), so the diff is a matching problem: every square whose occupant
// changed contributes a "vacated" piece (what was there) and/or an "arrived"
// piece (what is there now). Arrivals are matched to vacated pieces of the same
// owner — first the same piece type (ordinary moves, castling), then any type
// (promotion) — nearest first. Vacated pieces left unmatched were captured
// (normally on the square a piece arrived on; en passant elsewhere).

type Cell = PieceInstance | null | undefined
type Grid = readonly (readonly Cell[])[]

export interface BoardMove {
  from: Square
  to: Square
  /** The piece as it stands on `to` (the promoted piece after a promotion). */
  piece: PieceInstance
}

export interface BoardRemoval {
  square: Square
  piece: PieceInstance
}

export interface BoardDiff {
  moves: BoardMove[]
  removed: BoardRemoval[]
}

/**
 * More matched moves than this between two pushes is not play but a reset
 * (a new game on the same board, a reconnect): diffBoards reports it as null.
 */
const MAX_MOVES_PER_DIFF = 6

/** Same piece type and owner; ignores display-only flags such as `pending`. */
export function samePiece(a: Cell, b: Cell): boolean {
  if (!a || !b) return !a && !b
  return a.name === b.name && a.owner === b.owner
}

interface Change {
  square: Square
  piece: PieceInstance
  used: boolean
}

function distance([ar, ac]: Square, [br, bc]: Square): number {
  return Math.hypot(ar - br, ac - bc)
}

/**
 * Moves and captures that turn `prev` into `next`, or null when the boards are
 * not consecutive positions of one game (empty / differently sized `prev`, or
 * implausibly many changes).
 */
export function diffBoards(prev: Grid, next: Grid): BoardDiff | null {
  const rows = prev.length
  const cols = prev[0]?.length ?? 0
  if (rows === 0 || cols === 0 || next.length !== rows || (next[0]?.length ?? 0) !== cols) return null

  const vacated: Change[] = []
  const arrived: Change[] = []
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const a = prev[r]?.[c]
      const b = next[r]?.[c]
      if (samePiece(a, b)) continue
      if (a) vacated.push({ square: [r, c], piece: a, used: false })
      if (b) arrived.push({ square: [r, c], piece: b, used: false })
    }
  }

  const moves: BoardMove[] = []
  for (const sameType of [true, false]) {
    for (const arr of arrived) {
      if (arr.used) continue
      let best: Change | null = null
      let bestDist = Infinity
      for (const v of vacated) {
        if (v.used || v.piece.owner !== arr.piece.owner) continue
        if (sameType && v.piece.name !== arr.piece.name) continue
        const d = distance(v.square, arr.square)
        if (d < bestDist) {
          best = v
          bestDist = d
        }
      }
      if (!best) continue
      best.used = true
      arr.used = true
      moves.push({ from: best.square, to: arr.square, piece: arr.piece })
    }
  }

  if (moves.length > MAX_MOVES_PER_DIFF) return null
  // Pieces appearing from nowhere (beyond a stray one) also mean a reset.
  if (arrived.filter((a) => !a.used).length > 2) return null

  const removed = vacated.filter((v) => !v.used).map(({ square, piece }) => ({ square, piece }))
  return { moves, removed }
}
