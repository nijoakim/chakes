// Wire types for the game-setup catalogue endpoints (/api/game-types, /api/piece-guide,
// /api/setup-preview). Kept apart from services/types.ts.

import type { GameType } from './types'

/** A game type with its rules summary, as served by /api/game-types. */
export interface GameTypeInfo extends GameType {
  description?: string
}

/** Descriptions of the setup options (keys: 'cooldown', 'upside_down'). */
export type OptionDescriptions = Partial<Record<'cooldown' | 'upside_down', string>>

export interface GameTypesResponse {
  game_types: GameTypeInfo[]
  options?: OptionDescriptions
}

/**
 * One reachable square of a piece's movement diagram, in board coordinates
 * (x = file, y = rank; the piece is white and moves towards +y).
 */
export interface GuideSquare {
  x: number
  y: number
  /** Can move here when the square is empty. */
  move: boolean
  /** Can capture an enemy piece standing here. */
  capture: boolean
  /** Can capture a friendly piece standing here. */
  friend: boolean
  /** Part of a slide/ride: a piece on the way can block it (otherwise a step or leap). */
  ride: boolean
  /** Only while the piece has not moved yet. */
  initial: boolean
  /** Only by jumping over a hurdle. */
  hop: boolean
}

export interface PieceMovement {
  size: number
  origin: { x: number; y: number }
  squares: GuideSquare[]
  /** Squares holding the example hurdles that hop moves jump over. */
  hurdles: { x: number; y: number }[]
}

export interface PieceGuide {
  name: string
  default_cooldown: number
  notes: string
  movement: PieceMovement
}
