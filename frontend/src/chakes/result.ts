import type { Color } from '@/services/types'
import type { SideFlags } from './types'

export const COLOR_LABELS: Record<Color, string> = { white: 'White', black: 'Black' }

/** How the game was won, read from the loser's final check flags ('' if unknown). */
export function winReason(winner: Color, inCheck: SideFlags, inAntiCheck: SideFlags): string {
  const loser: Color = winner === 'white' ? 'black' : 'white'
  const c = inCheck[loser]
  const a = inAntiCheck[loser]
  if (c && a) return 'by checkmate & anti-checkmate'
  if (c) return 'by checkmate'
  if (a) return 'by anti-checkmate'
  return ''
}
