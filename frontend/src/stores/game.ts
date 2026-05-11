import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '../services/api'
import { gameSocket } from '../services/gameSocket'
import { RttMonitor } from '../services/rtt'
import { useSessionStore } from './session'
import type { Board, Cooldowns, Color, PieceInstance } from '../services/api'

export const useGameStore = defineStore('game', () => {
  // --- Server-pushed state ---
  const board = ref<Board>([])
  const maxCooldowns = ref<Record<string, number>>({
    Pawn: 3, Rook: 3, Knight: 3, Bishop: 3, Queen: 3, King: 3,
  })
  const pieceNames = ref<string[]>([])
  const playerColor = ref<Color>('white')
  const gameId = ref<string | null>(null)
  const winner = ref<Color | null>(null)

  // --- Cooldowns: raw server snapshot; CSS transitions handle visual decay ---
  const cooldowns = ref<Cooldowns>([])
  let serverCooldowns: Cooldowns = []
  let serverCooldownTime = 0

  // --- UI selection state (lives here so it's cleared in one place) ---
  const selected = ref<[number, number] | null>(null)
  const legalMoves = ref<Set<string>>(new Set())
  const selectedPromotion = ref('Queen')

  // --- RTT monitor ---
  const rtt = ref<number | null>(null)
  const rttMonitor = new RttMonitor(gameSocket)

  // --- WS subscription lifecycle ---
  let unsubscribers: Array<() => void> = []
  let currentLobby: string | null = null

  function connect(lobbyName: string): void {
    disconnect()
    currentLobby = lobbyName
    const session = useSessionStore()

    gameSocket.connect(lobbyName, session.token)
    rttMonitor.start()

    unsubscribers = [
      gameSocket.on('board', (b) => { board.value = b }),
      gameSocket.on('cooldowns', (c) => {
        serverCooldowns = c
        serverCooldownTime = performance.now() - (rttMonitor.rtt ?? 0) / 2
        cooldowns.value = c
      }),
      gameSocket.on('maxCooldowns', (mc) => { maxCooldowns.value = mc }),
      gameSocket.on('pieceNames', (names) => {
        pieceNames.value = names
        if (!names.includes(selectedPromotion.value)) {
          selectedPromotion.value =
            names.find((n) => n !== 'King' && n !== 'Pawn') ?? names[0]
        }
      }),
      gameSocket.on('color', (c) => { playerColor.value = c }),
      gameSocket.on('gameId', (id) => { gameId.value = id }),
      gameSocket.on('winner', (w) => { winner.value = w }),
      gameSocket.on('pong', () => { rtt.value = rttMonitor.rtt }),
    ]
  }

  function disconnect(): void {
    unsubscribers.forEach((u) => u())
    unsubscribers = []
    rttMonitor.stop()
    rtt.value = null
    gameSocket.disconnect()
    currentLobby = null
    resetGameState()
  }

  function resetGameState(): void {
    board.value = []
    cooldowns.value = []
    serverCooldowns = []
    serverCooldownTime = 0
    gameId.value = null
    winner.value = null
    selected.value = null
    legalMoves.value = new Set()
  }

  // --- Game actions ---
  async function startNewGame(
    gameType: string,
    cooldownSettings: Record<string, number>,
    upsideDown: boolean,
  ): Promise<void> {
    if (!currentLobby) return
    resetGameState()
    await api.createGame(currentLobby, gameType, cooldownSettings, upsideDown)
  }

  async function selectPiece(r: number, c: number): Promise<void> {
    if (!currentLobby || !gameId.value) return
    selected.value = [r, c]
    legalMoves.value = new Set()
    const moves = await api.getLegalMoves(currentLobby, gameId.value, r, c)
    if (selected.value && selected.value[0] === r && selected.value[1] === c) {
      legalMoves.value = new Set(moves.map(([mr, mc]) => `${mr},${mc}`))
    }
  }

  function deselect(): void {
    selected.value = null
    legalMoves.value = new Set()
  }

  function isOwnPiece(p: PieceInstance): boolean {
    return p.owner === playerColor.value
  }

  function isOnCooldown(r: number, c: number): boolean {
    const elapsed = (performance.now() - serverCooldownTime) / 1000
    return (serverCooldowns[r]?.[c] ?? 0) - elapsed > 0
  }

  async function attemptMove(toR: number, toC: number): Promise<void> {
    if (!currentLobby || !gameId.value || !selected.value) return
    const [fr, fc] = selected.value
    deselect()
    await api.sendMove(currentLobby, gameId.value, fr, fc, toR, toC, selectedPromotion.value)
  }

  // Click semantics from the original handleClick — preserve exactly.
  async function handleSquareClick(r: number, c: number): Promise<void> {
    if (!gameId.value || winner.value) return
    const piece = board.value[r]?.[c]

    if (selected.value === null) {
      if (piece && isOwnPiece(piece) && !isOnCooldown(r, c)) await selectPiece(r, c)
      return
    }

    if (piece && isOwnPiece(piece) && !isOnCooldown(r, c)) {
      const [fr, fc] = selected.value
      if (fr === r && fc === c) deselect()
      else await selectPiece(r, c)
      return
    }

    if (legalMoves.value.has(`${r},${c}`)) await attemptMove(r, c)
  }

  async function handleSquareRightClick(r: number, c: number): Promise<void> {
    if (!gameId.value || winner.value || !selected.value) return
    const [fr, fc] = selected.value
    if (fr !== r || fc !== c) await attemptMove(r, c)
  }

  return {
    // state
    board, cooldowns, maxCooldowns, pieceNames, playerColor, gameId, winner,
    selected, legalMoves, selectedPromotion, rtt,
    // actions
    connect, disconnect, resetGameState, startNewGame,
    selectPiece, deselect, attemptMove,
    handleSquareClick, handleSquareRightClick,
  }
})
