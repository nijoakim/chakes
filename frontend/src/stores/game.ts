import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import * as api from '@/services/api'
import { gameSocket } from '@/services/gameSocket'
import { RttMonitor } from '@/services/rtt'
import type { Board, Color } from '@/services/types'
import type { SideFlags } from '@/chakes/types'
import { squareKey, type Square } from '@/chakes/square'
import { promotablePieces } from '@/chakes/promotion'
import { decideLeftClick, decideRightClick, type ClickAction, type ClickState } from '@/chakes/input'
import { useCooldownClock } from '@/composables/useCooldownClock'
import { useOptimisticMoves } from '@/composables/useOptimisticMoves'
import { useSessionStore } from './session'

const LATENCY_HIDING_KEY = 'chakes_latency_hiding'

const noFlags = (): SideFlags => ({ white: false, black: false })

export const useGameStore = defineStore('game', () => {
  // --- Server-pushed state ---
  const authoritativeBoard = ref<Board>([])
  const maxCooldowns = ref<Record<string, number>>({})
  const stablePromotionNames = ref<string[]>([])
  const playerColor = ref<Color>('white')
  const gameId = ref<string | null>(null)
  const winner = ref<Color | null>(null)
  const inCheck = ref<SideFlags>(noFlags())
  const inAntiCheck = ref<SideFlags>(noFlags())
  const legalMovesBySrc = ref<Record<string, Set<string>>>({})

  // The lobby host is the player assigned white.
  const isHost = computed(() => playerColor.value === 'white')

  // --- RTT monitor ---
  const rtt = ref<number | null>(null)
  const rttMonitor = new RttMonitor(gameSocket)

  // --- Derived game-time state ---
  const clock = useCooldownClock()
  const latencyHidingEnabled = ref(localStorage.getItem(LATENCY_HIDING_KEY) === 'true')
  const optimistic = useOptimisticMoves({
    authoritativeBoard, playerColor, maxCooldowns, enabled: latencyHidingEnabled,
  })
  const board = optimistic.board

  // --- UI selection state (lives here so it's cleared in one place) ---
  const selected = ref<Square | null>(null)
  const legalMoves = computed<Set<string>>(() =>
    selected.value ? legalMovesBySrc.value[squareKey(selected.value)] ?? new Set() : new Set(),
  )
  const selectedPromotion = ref('Queen')

  // Drop the selection when the selected piece is captured or otherwise gone.
  watch(authoritativeBoard, (b) => {
    if (!selected.value) return
    const [r, c] = selected.value
    const piece = b[r]?.[c]
    if (!piece || piece.owner !== playerColor.value) selected.value = null
  })

  // --- WS subscription lifecycle ---
  let unsubscribers: Array<() => void> = []
  let currentLobby: string | null = null

  function connect(lobbyName: string): void {
    disconnect()
    currentLobby = lobbyName
    gameSocket.connect(lobbyName, useSessionStore().token)
    rttMonitor.start()

    unsubscribers = [
      gameSocket.on('board', (b) => { authoritativeBoard.value = b; legalMovesBySrc.value = {} }),
      gameSocket.on('cooldowns', (c) => clock.applySnapshot(c, rttMonitor.rtt)),
      gameSocket.on('maxCooldowns', (mc) => { maxCooldowns.value = mc }),
      gameSocket.on('pieceNames', (names) => {
        if (stablePromotionNames.value.length === 0) {
          stablePromotionNames.value = promotablePieces(names)
        }
        const promotable = stablePromotionNames.value
        if (!promotable.includes(selectedPromotion.value)) {
          selectedPromotion.value = promotable[0] ?? ''
        }
      }),
      gameSocket.on('color', (c) => { playerColor.value = c }),
      gameSocket.on('gameId', (id) => {
        if (id !== gameId.value) {
          winner.value = null
          inCheck.value = noFlags()
          inAntiCheck.value = noFlags()
          selected.value = null
          legalMovesBySrc.value = {}
        }
        gameId.value = id
      }),
      gameSocket.on('winner', (w) => { winner.value = w }),
      gameSocket.on('inCheck', (v) => { inCheck.value = v }),
      gameSocket.on('inAntiCheck', (v) => { inAntiCheck.value = v }),
      gameSocket.on('pong', () => { rtt.value = rttMonitor.rtt }),
      gameSocket.on('legalMoves', (m) => { legalMovesBySrc.value = m }),
      gameSocket.on('moveResult', ({ ok, client_move_id }) => {
        if (!ok && client_move_id) optimistic.reject(client_move_id)
      }),
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
    authoritativeBoard.value = []
    clock.reset()
    optimistic.reset()
    gameId.value = null
    winner.value = null
    inCheck.value = noFlags()
    inAntiCheck.value = noFlags()
    selected.value = null
    legalMovesBySrc.value = {}
    stablePromotionNames.value = []
  }

  function setLatencyHiding(enabled: boolean): void {
    latencyHidingEnabled.value = enabled
    localStorage.setItem(LATENCY_HIDING_KEY, String(enabled))
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

  function isOnCooldown(sq: Square): boolean {
    return clock.isOnCooldown(sq) || optimistic.isPendingCooldown(sq)
  }

  function deselect(): void {
    selected.value = null
  }

  function attemptMove(from: Square, to: Square): void {
    if (!currentLobby || !gameId.value) return
    deselect()
    const clientMoveId = crypto.randomUUID()
    gameSocket.sendMove({
      gameId: gameId.value,
      src: from,
      dst: to,
      promotion: selectedPromotion.value,
      clientMoveId,
    })
    optimistic.track(clientMoveId, from, to)
  }

  function clickState(square: Square): ClickState {
    return {
      active: gameId.value !== null && winner.value === null,
      square,
      piece: board.value[square[0]]?.[square[1]] ?? null,
      selected: selected.value,
      legalTargets: legalMoves.value,
      playerColor: playerColor.value,
      selectable: !isOnCooldown(square) && !optimistic.isPending(square),
    }
  }

  function apply(action: ClickAction): void {
    switch (action.kind) {
      case 'select':
        if (currentLobby && gameId.value) selected.value = action.square
        return
      case 'deselect':
        deselect()
        return
      case 'move':
        attemptMove(action.from, action.to)
        return
    }
  }

  function handleSquareClick(square: Square): void {
    apply(decideLeftClick(clickState(square)))
  }

  function handleSquareRightClick(square: Square): void {
    apply(decideRightClick(clickState(square)))
  }

  return {
    // state
    board, cooldownGrid: clock.grid, maxCooldowns, stablePromotionNames, playerColor, isHost,
    gameId, winner, inCheck, inAntiCheck,
    selected, legalMoves, selectedPromotion, rtt,
    latencyHidingEnabled, rejectedSquares: optimistic.rejectedSquares,
    // actions
    connect, disconnect, resetGameState, startNewGame,
    setLatencyHiding,
    deselect, handleSquareClick, handleSquareRightClick,
  }
})
