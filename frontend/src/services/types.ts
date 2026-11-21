// Wire types: shapes exchanged with the backend over REST and WebSocket.

export type Color = 'white' | 'black'
export type PieceInstance = { name: string; owner: Color }
export type Board = (PieceInstance | null)[][]
export type Cooldowns = number[][]

/** Engine coordinate: x = column, y = row (y = 0 is white's back rank). */
export interface WirePos {
  x: number
  y: number
}

export interface PieceDef {
  name: string
  default_cooldown: number
}

export interface GameType {
  id: string
  name: string
}

export interface PieceCooldown {
  name: string
  cooldown: number
}

export interface GameSettingsSummary {
  game_type_id: string
  game_type_label: string
  pieces: PieceCooldown[]
  upside_down: boolean
}

export interface LobbySummary {
  name: string
  server_name: string
  state: 'waiting' | 'in_progress' | 'ended'
  players: number
  spectators: number
  settings: GameSettingsSummary | null
}

export interface LobbyListResponse {
  server_name: string
  lobbies: LobbySummary[]
}

export interface InitialBoardResponse {
  board: Board
  size_x: number
  size_y: number
}
