import type { Color } from '@/services/types'
import type { DisplayPiece } from './types'
import { sameSquare, squareKey, type Square } from './square'

export interface ClickState {
  /** False when there is no running game (no game id, or a winner is decided). */
  active: boolean
  square: Square
  /** Piece on the clicked square, as displayed (including optimistic moves). */
  piece: DisplayPiece | null
  selected: Square | null
  /** Destination keys (see squareKey) legal for the current selection. */
  legalTargets: ReadonlySet<string>
  /** Null for spectators, who own no pieces and so can never select. */
  playerColor: Color | null
  /** Clicked square is neither on cooldown nor an unconfirmed optimistic piece. */
  selectable: boolean
}

export type ClickAction =
  | { kind: 'none' }
  | { kind: 'select'; square: Square }
  | { kind: 'deselect' }
  | { kind: 'move'; from: Square; to: Square }

const NONE: ClickAction = { kind: 'none' }

/**
 * Left-click priority: execute the move if the square is a legal target,
 * otherwise select the own piece on it. Clicking the selected piece deselects.
 * (Moving also deselects; the caller does that when applying the move.)
 */
export function decideLeftClick(s: ClickState): ClickAction {
  if (!s.active) return NONE
  const own = s.playerColor !== null && s.piece !== null && s.piece.owner === s.playerColor
  const select: ClickAction = s.selectable ? { kind: 'select', square: s.square } : NONE

  if (s.selected === null) return own ? select : NONE

  const isTarget = s.legalTargets.has(squareKey(s.square))
  if (own) {
    if (sameSquare(s.selected, s.square)) return { kind: 'deselect' }
    if (isTarget) return { kind: 'move', from: s.selected, to: s.square }
    return select
  }
  return isTarget ? { kind: 'move', from: s.selected, to: s.square } : NONE
}

/**
 * Right-click: with a selection, send a move to any other square without
 * checking the cached legal moves (the server is the judge; a rejection
 * flashes). Always deselects: sending a move deselects (the caller does that
 * when applying it), and right-clicking the selected square just deselects.
 */
export function decideRightClick(s: ClickState): ClickAction {
  if (!s.active || s.playerColor === null || s.selected === null) return NONE
  if (sameSquare(s.selected, s.square)) return { kind: 'deselect' }
  return { kind: 'move', from: s.selected, to: s.square }
}
