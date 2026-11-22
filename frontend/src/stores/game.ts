import { defineStore } from 'pinia'
import { ref, shallowRef, computed, watch } from 'vue'
import * as api from '@/services/api'
import { gameSocket, type AllLegalMoves, type SquareLegalMoves } from '@/services/gameSocket'
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

/** Legal destinations of one source square, valid only for board `version`. */
interface LegalMovesEntry {
  version: number
  moves: ReadonlySet<string>
}

const NO_MOVES: ReadonlySet<string> = new Set()

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
  // Version of authoritativeBoard (-1: none yet). Bumped by the server per move.
  const boardVersion = ref(-1)
  // Per-source-square cache. Never blanket-cleared on a board update: an entry
  // is usable only while entry.version === boardVersion, so stale ones simply
  // stop matching and get overwritten by newer replies/pushes.
  // shallowRef: always replaced wholesale, never mutated in place.
  const legalMovesBySrc = shallowRef<Record<string, LegalMovesEntry>>({})

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
  /** Legal moves of `sq` on the current board, or null if not known yet. */
  function knownMovesFor(sq: Square): ReadonlySet<string> | null {
    const entry = legalMovesBySrc.value[squareKey(sq)]
    return entry && entry.version === boardVersion.value ? entry.moves : null
  }
  /** Targets of the selection; null = selection's moves not known yet. */
  const legalMoves = computed<ReadonlySet<string> | null>(() =>
    selected.value ? knownMovesFor(selected.value) : NO_MOVES,
  )
  const selectedPromotion = ref('Queen')

  // Drop the selection when the selected piece is captured or otherwise gone.
  watch(authoritativeBoard, (b) => {
    if (!selected.value) return
    const [r, c] = selected.value
    const piece = b[r]?.[c]
    if (!piece || piece.owner !== playerColor.value) selected.value = null
  })

  // --- Legal-move cache ---
  // Replies and pushes may arrive before the board message of their version,
  // so accept anything not older than the current board.
  function isFreshFor(id: string, version: number): boolean {
    return id === gameId.value && version >= boardVersion.value
  }

  function storeMoves(cache: Record<string, LegalMovesEntry>, key: string, version: number, moves: ReadonlySet<string>): void {
    const existing = cache[key]
    if (!existing || existing.version <= version) cache[key] = { version, moves }
  }

  function applyAllLegalMoves({ gameId: id, version, moves, winner: w }: AllLegalMoves): void {
    if (id !== gameId.value) return
    if (w !== undefined) winner.value = w // latched server-side, so apply even if stale
    if (!isFreshFor(id, version)) return
    const cache = { ...legalMovesBySrc.value }
    for (const [key, dests] of Object.entries(moves)) storeMoves(cache, key, version, dests)
    legalMovesBySrc.value = cache
  }

  function applySquareLegalMoves({ gameId: id, version, square, moves }: SquareLegalMoves): void {
    if (!isFreshFor(id, version)) return
    const cache = { ...legalMovesBySrc.value }
    storeMoves(cache, squareKey(square), version, moves)
    legalMovesBySrc.value = cache
  }

  /** Ask the server for the selection's moves if they're not known for this board. */
  function requestSelectedMovesIfUnknown(): void {
    const sq = selected.value
    if (!sq || !gameId.value || knownMovesFor(sq) !== null) return
    // Selection is about to be dropped (see watch above) if its piece is gone.
    if (authoritativeBoard.value[sq[0]]?.[sq[1]]?.owner !== playerColor.value) return
    gameSocket.requestLegalMoves(gameId.value, sq)
  }

  function clearLegalMoves(): void {
    boardVersion.value = -1
    legalMovesBySrc.value = {}
  }

  // --- WS subscription lifecycle ---
  let unsubscribers: Array<() => void> = []
  let currentLobby: string | null = null

  function connect(lobbyName: string): void {
    disconnect()
    currentLobby = lobbyName
    gameSocket.connect(lobbyName, useSessionStore().token)
    rttMonitor.start()

    unsubscribers = [
      gameSocket.on('board', (b) => { authoritativeBoard.value = b }),
      gameSocket.on('boardVersion', (v) => {
        boardVersion.value = v
        requestSelectedMovesIfUnknown()
      }),
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
          clearLegalMoves()
        }
        gameId.value = id
      }),
      gameSocket.on('winner', (w) => { winner.value = w }),
      gameSocket.on('inCheck', (v) => { inCheck.value = v }),
      gameSocket.on('inAntiCheck', (v) => { inAntiCheck.value = v }),
      gameSocket.on('pong', () => { rtt.value = rttMonitor.rtt }),
      gameSocket.on('legalMoves', applyAllLegalMoves),
      gameSocket.on('squareLegalMoves', applySquareLegalMoves),
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
    clearLegalMoves()
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
        if (currentLobby && gameId.value) {
          selected.value = action.square
          requestSelectedMovesIfUnknown()
        }
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
