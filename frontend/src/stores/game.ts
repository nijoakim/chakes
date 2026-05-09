import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '../services/api'
import { gameSocket } from '../services/gameSocket'
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

  // --- Live cooldowns: derived from server snapshot + elapsed time ---
  const cooldowns = ref<Cooldowns>([])
  let serverCooldowns: Cooldowns = []
  let serverCooldownTime = 0
  let rafId = 0

  function tickCooldowns() {
    const elapsed = (performance.now() - serverCooldownTime) / 1000
    cooldowns.value = serverCooldowns.map((row) =>
      row.map((cd) => Math.max(cd - elapsed, 0)),
    )
    rafId = requestAnimationFrame(tickCooldowns)
  }

  // --- UI selection state (lives here so it's cleared in one place) ---
  const selected = ref<[number, number] | null>(null)
  const legalMoves = ref<Set<string>>(new Set())
  const selectedPromotion = ref('Queen')

  // --- WS subscription lifecycle ---
  let unsubscribers: Array<() => void> = []
  let currentLobby: string | null = null

  function connect(lobbyName: string): void {
    disconnect()
    currentLobby = lobbyName
    const session = useSessionStore()

    gameSocket.connect(lobbyName, session.token)

    unsubscribers = [
      gameSocket.on('board', (b) => { board.value = b }),
      gameSocket.on('cooldowns', (c) => {
        serverCooldowns = c
        serverCooldownTime = performance.now()
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
    ]

    rafId = requestAnimationFrame(tickCooldowns)
  }

  function disconnect(): void {
    unsubscribers.forEach((u) => u())
    unsubscribers = []
    gameSocket.disconnect()
    cancelAnimationFrame(rafId)
    rafId = 0
    currentLobby = null
    resetGameState()
  }

  function resetGameState(): void {
    board.value = []
    cooldowns.value = []
    serverCooldowns = []
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
    return (cooldowns.value[r]?.[c] ?? 0) > 0
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
    selected, legalMoves, selectedPromotion,
    // actions
    connect, disconnect, resetGameState, startNewGame,
    selectPiece, deselect, attemptMove,
    handleSquareClick, handleSquareRightClick,
  }
})
