import type { PieceInstance } from '@/services/types'

/** A piece as rendered: `pending` marks an optimistic, not yet confirmed move. */
export type DisplayPiece = PieceInstance & { pending?: boolean }
export type DisplayBoard = (DisplayPiece | null)[][]

/** Game settings chosen by the host in the setup screen. */
export interface GameSettings {
  gameType: string
  cooldowns: Record<string, number>
  upsideDown: boolean
}

export type SideFlags = { white: boolean; black: boolean }
