export type Color = 'white' | 'black'
export type PieceInstance = { name: string; owner: Color }
export type Board = (PieceInstance | null)[][]
export type Cooldowns = number[][]

export interface PieceDef {
  name: string
  default_cooldown: number
}

export interface GameType {
  id: string
  name: string
}

export async function createLobby(name?: string): Promise<string> {
  const url = name ? `/api/lobby?name=${encodeURIComponent(name)}` : '/api/lobby'
  const res = await fetch(url, { method: 'POST' })
  const data = await res.json()
  return String(data.lobby)
}

export async function getGameTypes(): Promise<GameType[]> {
  const res = await fetch('/api/game-types')
  const data = await res.json()
  return data.game_types
}

export async function getPieceDefs(gameType?: string): Promise<PieceDef[]> {
  const url = gameType ? `/api/piece-defs?game_type=${encodeURIComponent(gameType)}` : '/api/piece-defs'
  const res = await fetch(url)
  const data = await res.json()
  return data.pieces
}

export async function createGame(
  lobbyName: string,
  gameType?: string,
  cooldowns?: Record<string, number>,
  upsideDown?: boolean,
): Promise<string> {
  const body = JSON.stringify({ game_type: gameType ?? 'orthodox', cooldowns, upside_down: upsideDown ?? false })
  const res = await fetch(`/api/lobby/${lobbyName}/game`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body,
  })
  const data = await res.json()
  return String(data.game_id)
}

export async function getLegalMoves(
  lobbyName: string,
  gameId: string,
  r: number,
  c: number,
): Promise<number[][]> {
  const res = await fetch(`/api/lobby/${lobbyName}/game/${gameId}/legal-moves?r=${r}&c=${c}`)
  const data = await res.json()
  return data.moves
}

export async function sendMove(
  lobbyName: string,
  gameId: string,
  fromR: number, fromC: number,
  toR: number, toC: number,
  promotion?: string,
): Promise<void> {
  await fetch(`/api/lobby/${lobbyName}/game/${gameId}/move`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ src: { x: fromC, y: fromR }, dst: { x: toC, y: toR }, promotion }),
  })
}

// TODO: backend endpoint pending
export async function listLobbies(): Promise<string[]> {
  return []
}
