// REST calls for the game-setup screen: game types with descriptions, per-piece
// movement guides and the starting-position preview.

import { ApiError } from './api'
import type { InitialBoardResponse } from './types'
import type { GameTypesResponse, PieceGuide } from './catalogTypes'

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) {
    const detail = await res.text().catch(() => '')
    throw new ApiError(`GET ${url} failed: ${res.status} ${res.statusText}`, res.status, detail)
  }
  return (await res.json()) as T
}

export function getGameTypesInfo(): Promise<GameTypesResponse> {
  return getJson<GameTypesResponse>('/api/game-types')
}

export async function getPieceGuide(gameType: string): Promise<PieceGuide[]> {
  const data = await getJson<{ pieces: PieceGuide[] }>(
    `/api/piece-guide?game_type=${encodeURIComponent(gameType)}`,
  )
  return data.pieces
}

/** Starting position exactly as the game will be created (honours upside-down). */
export function getSetupPreview(gameType: string, upsideDown: boolean): Promise<InitialBoardResponse> {
  const params = new URLSearchParams({ game_type: gameType })
  if (upsideDown) params.set('upside_down', 'true')
  return getJson<InitialBoardResponse>(`/api/setup-preview?${params}`)
}
