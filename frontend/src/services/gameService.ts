export type Board = string[][]
export type Color = 'white' | 'black'

export interface GameEvents {
  onBoard: (board: Board) => void
  onColor?: (color: Color) => void
}

class GameService {
  async createGame(): Promise<string> {
    const res = await fetch('/api/games', { method: 'POST' })
    const data = await res.json()
    return String(data.game)
  }

  async sendMove(gameId: string, fromR: number, fromC: number, toR: number, toC: number): Promise<void> {
    await fetch(`/api/games/${gameId}/move`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ from_r: fromR, from_c: fromC, to_r: toR, to_c: toC }),
    })
  }

  connect(gameId: string, events: GameEvents): () => void {
    const ws = new WebSocket(`ws://${location.host}/api/games/${gameId}/ws`)
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data)
      if (data.board) events.onBoard(data.board)
      if (data.color) events.onColor?.(data.color)
    }
    return () => ws.close()
  }
}

export const gameService = new GameService()
