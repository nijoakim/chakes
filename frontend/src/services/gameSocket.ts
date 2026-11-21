import type { Board, Color, Cooldowns } from './types'
import type { SideFlags } from '@/chakes/types'
import { fromWireKey, fromWireTuple, squareKey, toWire, type Square } from '@/chakes/square'

export interface GameSocketEvents {
  board: Board
  cooldowns: Cooldowns
  maxCooldowns: Record<string, number>
  pieceNames: string[]
  color: Color
  gameId: string
  winner: Color | null
  pong: { id: string }
  /** Keyed by squareKey of the source square; values are squareKeys of destinations. */
  legalMoves: Record<string, Set<string>>
  moveResult: { ok: boolean; error?: string; client_move_id?: string | null }
  inCheck: SideFlags
  inAntiCheck: SideFlags
}

export interface OutgoingMove {
  gameId: string
  src: Square
  dst: Square
  promotion: string
  clientMoveId: string
}

type Listener<E extends keyof GameSocketEvents> = (payload: GameSocketEvents[E]) => void

// The backend sends two families of messages:
//  - typed replies: {type: 'pong' | 'move_result' | 'legal_moves' | 'error', ...}
//  - untyped pushes, told apart by their fields (None-valued fields are omitted):
//      lobby joined:   {color}
//      game state:     {board, cooldowns, game_id, white_in_check, ..., max_cooldowns?,
//                       piece_names?, winner?, legal_moves?}
//      all legal moves: {legal_moves}
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Incoming = Record<string, any>

export class GameSocket {
  private ws: WebSocket | null = null
  private listeners: { [E in keyof GameSocketEvents]?: Set<Listener<E>> } = {}

  connect(lobbyName: string, token: string): void {
    this.disconnect()
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    this.ws = new WebSocket(
      `${protocol}//${location.host}/api/lobby/${encodeURIComponent(lobbyName)}/ws?token=${encodeURIComponent(token)}`,
    )
    this.ws.onmessage = (e) => this.handleMessage(e)
  }

  disconnect(): void {
    this.ws?.close()
    this.ws = null
  }

  send(msg: object): void {
    this.ws?.send(JSON.stringify(msg))
  }

  sendMove(m: OutgoingMove): void {
    this.send({
      type: 'move',
      game_id: m.gameId,
      src: toWire(m.src),
      dst: toWire(m.dst),
      promotion: m.promotion,
      client_move_id: m.clientMoveId,
    })
  }

  on<E extends keyof GameSocketEvents>(event: E, listener: Listener<E>): () => void {
    if (!this.listeners[event]) {
      this.listeners[event] = new Set() as never
    }
    const set = this.listeners[event] as Set<Listener<E>>
    set.add(listener)
    return () => set.delete(listener)
  }

  private emit<E extends keyof GameSocketEvents>(event: E, payload: GameSocketEvents[E]): void {
    const set = this.listeners[event] as Set<Listener<E>> | undefined
    set?.forEach((l) => l(payload))
  }

  private handleMessage(e: MessageEvent): void {
    if (!e.data) return
    const data = JSON.parse(e.data) as Incoming
    switch (data.type) {
      case 'pong':
        this.emit('pong', { id: data.id })
        return
      case 'move_result':
        this.emit('moveResult', { ok: data.ok, error: data.error, client_move_id: data.client_move_id })
        return
      case 'legal_moves': // reply to a single-square query, which this client never sends
      case 'error':
        return
      case undefined:
        this.handlePush(data)
        return
    }
  }

  private handlePush(data: Incoming): void {
    if ('color' in data) this.emit('color', data.color)
    if ('board' in data) this.handleGameState(data)
    if ('legal_moves' in data) this.emit('legalMoves', parseLegalMoves(data.legal_moves))
  }

  // Emission order matters to listeners: 'board' clears cached legal moves and
  // 'gameId' resets per-game flags, so both run before 'winner' / 'legalMoves'.
  private handleGameState(data: Incoming): void {
    this.emit('board', data.board)
    this.emit('cooldowns', data.cooldowns)
    if ('max_cooldowns' in data) this.emit('maxCooldowns', data.max_cooldowns)
    if ('piece_names' in data) this.emit('pieceNames', data.piece_names)
    this.emit('gameId', data.game_id)
    // `winner` is omitted until decided; present means the game is over.
    if ('winner' in data) this.emit('winner', data.winner ?? null)
    this.emit('inCheck', { white: data.white_in_check ?? false, black: data.black_in_check ?? false })
    this.emit('inAntiCheck', { white: data.white_in_anti_check ?? false, black: data.black_in_anti_check ?? false })
  }
}

function parseLegalMoves(wire: Record<string, number[][]>): Record<string, Set<string>> {
  const out: Record<string, Set<string>> = {}
  for (const [src, dests] of Object.entries(wire)) {
    out[squareKey(fromWireKey(src))] = new Set(dests.map((d) => squareKey(fromWireTuple(d))))
  }
  return out
}

export const gameSocket = new GameSocket()
