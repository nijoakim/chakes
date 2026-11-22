import type {
  GameType, InitialBoardResponse, LobbyListResponse, PieceDef,
} from './types'

/** Thrown for non-2xx responses. Network failures surface as the `fetch` TypeError. */
export class ApiError extends Error {
  readonly status: number
  readonly detail: string

  constructor(message: string, status: number, detail: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init)
  if (!res.ok) {
    const detail = await res.text().catch(() => '')
    throw new ApiError(
      `${init?.method ?? 'GET'} ${url} failed: ${res.status} ${res.statusText}${detail ? ` — ${detail}` : ''}`,
      res.status,
      detail,
    )
  }
  return (await res.json()) as T
}

export async function createLobby(name?: string): Promise<string> {
  const url = name ? `/api/lobby?name=${encodeURIComponent(name)}` : '/api/lobby'
  const data = await fetchJson<{ lobby: string }>(url, { method: 'POST' })
  return String(data.lobby)
}

export async function getGameTypes(): Promise<GameType[]> {
  const data = await fetchJson<{ game_types: GameType[] }>('/api/game-types')
  return data.game_types
}

export async function getPieceDefs(gameType?: string): Promise<PieceDef[]> {
  const url = gameType ? `/api/piece-defs?game_type=${encodeURIComponent(gameType)}` : '/api/piece-defs'
  const data = await fetchJson<{ pieces: PieceDef[] }>(url)
  return data.pieces
}

export async function createGame(
  lobbyName: string,
  gameType?: string,
  cooldowns?: Record<string, number>,
  upsideDown?: boolean,
): Promise<string> {
  const body = JSON.stringify({ game_type: gameType ?? 'orthodox', cooldowns, upside_down: upsideDown ?? false })
  const data = await fetchJson<{ game_id: string }>(`/api/lobby/${encodeURIComponent(lobbyName)}/game`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body,
  })
  return String(data.game_id)
}

export function listLobbies(init?: RequestInit): Promise<LobbyListResponse> {
  return fetchJson<LobbyListResponse>('/api/lobby', { cache: 'no-store', ...init })
}

export function getInitialBoard(gameType?: string, upsideDown?: boolean): Promise<InitialBoardResponse> {
  const params = new URLSearchParams()
  if (gameType) params.set('game_type', gameType)
  if (upsideDown) params.set('upside_down', 'true')
  const query = params.size ? `?${params}` : ''
  return fetchJson<InitialBoardResponse>(`/api/initial-board${query}`)
}
