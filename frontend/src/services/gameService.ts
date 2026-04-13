export type Board = string[][]
export type Color = 'white' | 'black'

export interface GameEvents {
  onBoard: (board: Board) => void
  onColor?: (color: Color) => void
}

class GameService {
  async createRoom(): Promise<string> {
    const res = await fetch('/api/rooms', { method: 'POST' })
    const data = await res.json()
    return String(data.room)
  }

  async sendMove(roomId: string, fromR: number, fromC: number, toR: number, toC: number): Promise<void> {
    await fetch(`/api/rooms/${roomId}/move`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ from_r: fromR, from_c: fromC, to_r: toR, to_c: toC }),
    })
  }

  connect(roomId: string, events: GameEvents): () => void {
    const ws = new WebSocket(`ws://${location.host}/api/rooms/${roomId}/ws`)
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data)
      console.log(data);
      if (data.board) events.onBoard(data.board)
      if (data.color) events.onColor?.(data.color)
    }
    return () => ws.close()
  }
}

export const gameService = new GameService()
