export type Board = string[][]
export type Cooldowns = number[][]
export type Color = 'white' | 'black'

export interface PieceDef {
  name: string
  default_cooldown: number
}

export interface GameEvents {
  onBoard: (board: Board) => void
  onCooldowns?: (cooldowns: Cooldowns) => void
  onMaxCooldowns?: (maxCooldowns: Record<string, number>) => void
  onColor?: (color: Color) => void
  onGameId?: (gameId: string) => void
  onWinner?: (winner: Color | null) => void
}

class GameService {
  async createLobby(name?: string): Promise<string> {
    const url = name ? `/api/lobby?name=${encodeURIComponent(name)}` : '/api/lobby'
    const res = await fetch(url, { method: 'POST' })
    const data = await res.json()
    return String(data.lobby)
  }

  async getPieceDefs(): Promise<PieceDef[]> {
    const res = await fetch('/api/piece-defs')
    const data = await res.json()
    return data.pieces
  }

  async createGame(lobbyName: string, cooldowns?: Record<string, number>): Promise<string> {
    const body = cooldowns ? JSON.stringify({ cooldowns }) : undefined
    const res = await fetch(`/api/lobby/${lobbyName}/game`, {
      method: 'POST',
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body,
    })
    const data = await res.json()
    return String(data.game_id)
  }

  async getLegalMoves(lobbyName: string, gameId: string, r: number, c: number): Promise<number[][]> {
    const res = await fetch(`/api/lobby/${lobbyName}/game/${gameId}/legal-moves?r=${r}&c=${c}`)
    const data = await res.json()
    return data.moves
  }

  async sendMove(lobbyName: string, gameId: string, fromR: number, fromC: number, toR: number, toC: number): Promise<void> {
    await fetch(`/api/lobby/${lobbyName}/game/${gameId}/move`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ from_r: fromR, from_c: fromC, to_r: toR, to_c: toC }),
    })
  }

  connect(lobbyName: string, events: GameEvents): () => void {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${protocol}//${location.host}/api/lobby/${lobbyName}/ws`)
    ws.onmessage = (e) => {
      if (!e.data) return
      const data = JSON.parse(e.data)
      console.log(data);
      if (data.board) events.onBoard(data.board)
      if (data.cooldowns) events.onCooldowns?.(data.cooldowns)
      if (data.max_cooldowns) events.onMaxCooldowns?.(data.max_cooldowns)
      if (data.color) events.onColor?.(data.color)
      if (data.game_id) events.onGameId?.(data.game_id)
      events.onWinner?.(data.winner ?? null)
    }
    return () => ws.close()
  }
}

export const gameService = new GameService()
