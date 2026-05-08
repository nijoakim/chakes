import type { Board, Cooldowns, Color } from './api'

export interface GameSocketEvents {
  board: Board
  cooldowns: Cooldowns
  maxCooldowns: Record<string, number>
  pieceNames: string[]
  color: Color
  gameId: string
  winner: Color | null
}

type Listener<E extends keyof GameSocketEvents> = (payload: GameSocketEvents[E]) => void

export class GameSocket {
  private ws: WebSocket | null = null
  private listeners: { [E in keyof GameSocketEvents]?: Set<Listener<E>> } = {}

  connect(lobbyName: string, token: string): void {
    this.disconnect()
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    this.ws = new WebSocket(
      `${protocol}//${location.host}/api/lobby/${lobbyName}/ws?token=${token}`,
    )
    this.ws.onmessage = (e) => this.handleMessage(e)
  }

  disconnect(): void {
    this.ws?.close()
    this.ws = null
  }

  on<E extends keyof GameSocketEvents>(event: E, listener: Listener<E>): () => void {
    const set = (this.listeners[event] ??= new Set()) as Set<Listener<E>>
    set.add(listener)
    return () => set.delete(listener)
  }

  private emit<E extends keyof GameSocketEvents>(event: E, payload: GameSocketEvents[E]): void {
    const set = this.listeners[event] as Set<Listener<E>> | undefined
    set?.forEach((l) => l(payload))
  }

  private handleMessage(e: MessageEvent): void {
    if (!e.data) return
    const data = JSON.parse(e.data)
    if (data.board) this.emit('board', data.board)
    if (data.cooldowns) this.emit('cooldowns', data.cooldowns)
    if (data.max_cooldowns) this.emit('maxCooldowns', data.max_cooldowns)
    if (data.piece_names) this.emit('pieceNames', data.piece_names)
    if (data.color) this.emit('color', data.color)
    if (data.game_id) this.emit('gameId', data.game_id)
    // BUG FIX: only emit winner if the server actually sent the field.
    if ('winner' in data) this.emit('winner', data.winner ?? null)
  }
}

export const gameSocket = new GameSocket()
