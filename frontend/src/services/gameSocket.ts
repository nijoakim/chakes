import type { Board, Color, Cooldowns } from './types'
import type { SideFlags } from '@/chakes/types'
import { fromWire, fromWireKey, fromWireTuple, squareKey, toWire, type Square } from '@/chakes/square'

export interface GameSocketEvents {
  board: Board
  cooldowns: Cooldowns
  maxCooldowns: Record<string, number>
  pieceNames: string[]
  color: Color
  gameId: string
  winner: Color | null
  /** Version of the board just emitted; emitted last for a game-state message. */
  boardVersion: number
  pong: { id: string }
  /** All pieces' legal moves for board `version` (bundled with game state, or pushed after a move). */
  legalMoves: AllLegalMoves
  /** Reply to requestLegalMoves(): one square's legal moves for board `version`. */
  squareLegalMoves: SquareLegalMoves
  moveResult: { ok: boolean; error?: string; client_move_id?: string | null }
  inCheck: SideFlags
  inAntiCheck: SideFlags
}

export interface AllLegalMoves {
  gameId: string
  version: number
  /** Keyed by squareKey of the source square; values are squareKeys of destinations. */
  moves: Record<string, Set<string>>
  /** Only on the background push: present once a winner is decided (see handlePush). */
  winner?: Color | null
}

export interface SquareLegalMoves {
  gameId: string
  version: number
  square: Square
  /** squareKeys of destinations. */
  moves: Set<string>
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
//      game state:     {board, cooldowns, game_id, version, white_in_check, ...,
//                       max_cooldowns?, piece_names?, winner?, legal_moves?}
//      all legal moves: {legal_moves, game_id, version, winner?}  (pushed after a move)
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

  requestLegalMoves(gameId: string, square: Square): void {
    this.send({ type: 'legal_moves', game_id: gameId, pos: toWire(square) })
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
      case 'legal_moves':
        // Error replies (e.g. game_not_found) carry no moves; nothing to do.
        if (Array.isArray(data.moves)) {
          this.emit('squareLegalMoves', {
            gameId: data.game_id,
            version: data.version,
            square: fromWire(data.pos),
            moves: parseDests(data.moves),
          })
        }
        return
      case 'error':
        return
      case undefined:
        this.handlePush(data)
        return
    }
  }

  private handlePush(data: Incoming): void {
    if ('color' in data) this.emit('color', data.color)
    const isState = 'board' in data
    if (isState) this.handleGameState(data)
    if ('legal_moves' in data) {
      const all: AllLegalMoves = {
        gameId: data.game_id,
        version: data.version,
        moves: parseLegalMoves(data.legal_moves),
      }
      // A game-state message already emitted its winner; the move push carries
      // it separately (omitted until decided, like in game state).
      if (!isState && 'winner' in data) all.winner = data.winner ?? null
      this.emit('legalMoves', all)
    }
    // Last, so listeners see the complete state (incl. bundled legal moves).
    if (isState) this.emit('boardVersion', data.version)
  }

  // Emission order matters to listeners: 'gameId' resets per-game state, so it
  // runs before 'winner' and before the legal moves / version emitted after.
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

function parseDests(wire: number[][]): Set<string> {
  return new Set(wire.map((d) => squareKey(fromWireTuple(d))))
}

function parseLegalMoves(wire: Record<string, number[][]>): Record<string, Set<string>> {
  const out: Record<string, Set<string>> = {}
  for (const [src, dests] of Object.entries(wire)) {
    out[squareKey(fromWireKey(src))] = parseDests(dests)
  }
  return out
}

export const gameSocket = new GameSocket()
