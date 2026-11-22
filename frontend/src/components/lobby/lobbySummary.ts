// Pure helpers for presenting lobby rows in the lobby browser.

import type { GameSettingsSummary, LobbySummary, PieceCooldown } from '@/services/types'

export type LobbyAction = 'join' | 'watch' | 'view'

export const MAX_PLAYERS = 2
export const MAX_LOBBY_NAME_LENGTH = 40

/** What clicking a lobby row will let you do. */
export function lobbyAction(row: LobbySummary): LobbyAction {
  if (row.state === 'ended') return 'view'
  if (row.state === 'waiting' && row.players < MAX_PLAYERS) return 'join'
  return 'watch'
}

export const ACTION_LABELS: Record<LobbyAction, string> = {
  join: 'Join',
  watch: 'Watch',
  view: 'View',
}

export const STATE_LABELS: Record<LobbySummary['state'], string> = {
  waiting: 'Waiting',
  in_progress: 'In progress',
  ended: 'Ended',
}

export function formatSeconds(s: number): string {
  return `${Number(s.toFixed(2))}s`
}

/**
 * The cooldown most pieces share. Ties are broken towards the smaller value,
 * so the result is deterministic regardless of piece order.
 */
export function baseCooldown(pieces: PieceCooldown[]): number | null {
  if (pieces.length === 0) return null
  const counts = new Map<number, number>()
  for (const p of pieces) counts.set(p.cooldown, (counts.get(p.cooldown) ?? 0) + 1)
  let best: number | null = null
  let bestCount = 0
  for (const [value, count] of counts) {
    if (count > bestCount || (count === bestCount && best !== null && value < best)) {
      best = value
      bestCount = count
    }
  }
  return best
}

/**
 * Compact settings summary parts, e.g.
 *   ["Orthodox", "3s cooldown"]                       (all pieces equal)
 *   ["Orthodox", "3s", "Queen 6s", "King 1s"]          (base + exceptions)
 *   [..., "Upside-down"]                               (when set)
 */
export function settingsSummaryParts(settings: GameSettingsSummary): string[] {
  const parts = [settings.game_type_label]
  const base = baseCooldown(settings.pieces)
  if (base !== null) {
    const exceptions = settings.pieces.filter(p => p.cooldown !== base)
    if (exceptions.length === 0) {
      parts.push(`${formatSeconds(base)} cooldown`)
    } else {
      parts.push(formatSeconds(base))
      for (const p of exceptions) parts.push(`${p.name} ${formatSeconds(p.cooldown)}`)
    }
  }
  if (settings.upside_down) parts.push('Upside-down')
  return parts
}

/** Full, uncompressed description (used as a tooltip). */
export function settingsFullDescription(settings: GameSettingsSummary): string {
  const pieces = settings.pieces.map(p => `${p.name} ${formatSeconds(p.cooldown)}`)
  return [settings.game_type_label, ...pieces, ...(settings.upside_down ? ['Upside-down'] : [])].join(' · ')
}

/** Returns an error message, or null if the (already trimmed) name is acceptable. Empty means "random". */
export function validateLobbyName(name: string): string | null {
  if (name.length > MAX_LOBBY_NAME_LENGTH) {
    return `Keep the name to ${MAX_LOBBY_NAME_LENGTH} characters or fewer.`
  }
  if (name && !/^[\p{L}\p{N} _.-]+$/u.test(name)) {
    return 'Use only letters, numbers, spaces, dashes, underscores and dots.'
  }
  return null
}
