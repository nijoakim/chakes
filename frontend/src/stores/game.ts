import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import * as api from '../services/api'
import { gameSocket } from '../services/gameSocket'
import { RttMonitor } from '../services/rtt'
import { useSessionStore } from './session'
import type { Board, Cooldowns, Color, PieceInstance } from '../services/api'

interface PendingMove {
  id: string
  src: [number, number]
  dst: [number, number]
  pieceName: string
  promotion: string
  sentAt: number
  status: 'pending' | 'rejected'
}

export const useGameStore = defineStore('game', () => {
  // --- Server-pushed state ---
  const authoritativeBoard = ref<Board>([])
  const maxCooldowns = ref<Record<string, number>>({
    Pawn: 3, Rook: 3, Knight: 3, Bishop: 3, Queen: 3, King: 3,
  })
  const pieceNames = ref<string[]>([])
  const stablePromotionNames = ref<string[]>([])
  const playerColor = ref<Color>('white')
  const gameId = ref<string | null>(null)
  const winner = ref<Color | null>(null)
  const inCheck = ref<{ white: boolean; black: boolean }>({ white: false, black: false })
  const inAntiCheck = ref<{ white: boolean; black: boolean }>({ white: false, black: false })

  // --- Cooldowns: raw server snapshot; CSS transitions handle visual decay ---
  const cooldowns = ref<Cooldowns>([])
  let serverCooldowns: Cooldowns = []
  let serverCooldownTime = 0
  let cooldownTimeouts: ReturnType<typeof setTimeout>[] = []

  // --- Latency hiding ---
  const latencyHidingEnabled = ref(false)
  const pendingMoves = ref<Map<string, PendingMove>>(new Map())
  const rejectedSquares = ref<Set<string>>(new Set())

  // --- Optimistic board overlay ---
  const board = computed<Board>(() => {
    if (!latencyHidingEnabled.value || pendingMoves.value.size === 0) {
      return authoritativeBoard.value
    }
    const rows = authoritativeBoard.value.map((r) => r.slice())
    for (const m of pendingMoves.value.values()) {
      if (m.status !== 'pending') continue
      const [sr, sc] = m.src
      const [dr, dc] = m.dst
      const piece = rows[sr]?.[sc]
      if (!piece) continue
      rows[sr] = rows[sr].slice()
      rows[dr] = rows[dr].slice()
      rows[sr][sc] = null
      rows[dr][dc] = { ...piece, pending: true }
    }
    return rows
  })

  // --- UI selection state (lives here so it's cleared in one place) ---
  const selected = ref<[number, number] | null>(null)
  const legalMovesBySrc = ref<Record<string, Set<string>>>({})
  const legalMoves = computed<Set<string>>(() => {
    if (!selected.value) return new Set()
    const [r, c] = selected.value
    return legalMovesBySrc.value[`${r},${c}`] ?? new Set()
  })
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
      gameSocket.on('board', (b) => { authoritativeBoard.value = b }),
      gameSocket.on('cooldowns', (c) => {
        serverCooldowns = c
        serverCooldownTime = performance.now() - (rttMonitor.rtt ?? 0) / 2
        cooldownTimeouts.forEach(clearTimeout)
        cooldownTimeouts = []
        cooldowns.value = c
        const elapsed = (performance.now() - serverCooldownTime) / 1000
        for (let r = 0; r < c.length; r++) {
          for (let col = 0; col < c[r].length; col++) {
            const remaining = (c[r][col] ?? 0) - elapsed
            if (remaining > 0) {
              const t = setTimeout(() => { cooldowns.value[r][col] = 0 }, remaining * 1000)
              cooldownTimeouts.push(t)
            }
          }
        }
      }),
      gameSocket.on('maxCooldowns', (mc) => { maxCooldowns.value = mc }),
      gameSocket.on('pieceNames', (names) => {
        pieceNames.value = names
        if (stablePromotionNames.value.length === 0) {
          stablePromotionNames.value = names.filter((n) => !/pawn|king/i.test(n))
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
          inCheck.value = { white: false, black: false }
          inAntiCheck.value = { white: false, black: false }
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
        if (ok || !client_move_id) return
        const m = pendingMoves.value.get(client_move_id)
        if (!m) return
        pendingMoves.value.delete(client_move_id)
        const [sr, sc] = m.src
        const [dr, dc] = m.dst
        const next = new Set(rejectedSquares.value)
        next.add(`${sr},${sc}`)
        next.add(`${dr},${dc}`)
        rejectedSquares.value = next
        setTimeout(() => {
          const s = new Set(rejectedSquares.value)
          s.delete(`${sr},${sc}`)
          s.delete(`${dr},${dc}`)
          rejectedSquares.value = s
        }, 300)
      }),
    ]

    // Reconciliation: drop pending entries when authoritative state already reflects the move
    watch(authoritativeBoard, (b) => {
      for (const [id, m] of pendingMoves.value) {
        if (m.status !== 'pending') continue
        const [sr, sc] = m.src
        const [dr, dc] = m.dst
        const srcEmpty = b[sr]?.[sc] == null
        const dstPiece = b[dr]?.[dc]
        if (srcEmpty && dstPiece != null && dstPiece.owner === playerColor.value) {
          pendingMoves.value.delete(id)
        }
      }
    }, { deep: false })

    watch(authoritativeBoard, (b) => {
      if (!selected.value) return
      const [r, c] = selected.value
      const piece = b[r]?.[c]
      if (!piece || piece.owner !== playerColor.value) {
        deselect()
      }
    })
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
    cooldowns.value = []
    serverCooldowns = []
    serverCooldownTime = 0
    cooldownTimeouts.forEach(clearTimeout)
    cooldownTimeouts = []
    gameId.value = null
    winner.value = null
    inCheck.value = { white: false, black: false }
    inAntiCheck.value = { white: false, black: false }
    selected.value = null
    legalMovesBySrc.value = {}
    stablePromotionNames.value = []
    pendingMoves.value = new Map()
    latencyHidingEnabled.value = false
    rejectedSquares.value = new Set()
  }

  function setLatencyHiding(enabled: boolean): void {
    latencyHidingEnabled.value = enabled
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

  function selectPiece(r: number, c: number): void {
    if (!currentLobby || !gameId.value) return
    selected.value = [r, c]
  }

  function deselect(): void {
    selected.value = null
  }

  function isOwnPiece(p: PieceInstance): boolean {
    return p.owner === playerColor.value
  }

  function isOnCooldown(r: number, c: number): boolean {
    const elapsed = (performance.now() - serverCooldownTime) / 1000
    if ((serverCooldowns[r]?.[c] ?? 0) - elapsed > 0) return true

    if (latencyHidingEnabled.value) {
      for (const m of pendingMoves.value.values()) {
        if (m.status !== 'pending') continue
        if (m.dst[0] === r && m.dst[1] === c) {
          const maxCd = maxCooldowns.value[m.pieceName] ?? 0
          if (maxCd - (performance.now() - m.sentAt) / 1000 > 0) return true
        }
      }
    }
    return false
  }

  function isPendingPiece(r: number, c: number): boolean {
    return board.value[r]?.[c]?.pending === true
  }

  function attemptMove(toR: number, toC: number): void {
    if (!currentLobby || !gameId.value || !selected.value) return
    const [fr, fc] = selected.value
    deselect()

    const moveId = crypto.randomUUID()
    gameSocket.send({
      type: 'move',
      game_id: gameId.value,
      src: { x: fc, y: fr },
      dst: { x: toC, y: toR },
      promotion: selectedPromotion.value,
      client_move_id: moveId,
    })

    if (latencyHidingEnabled.value) {
      const piece = authoritativeBoard.value[fr]?.[fc]
      if (piece) {
        pendingMoves.value.set(moveId, {
          id: moveId,
          src: [fr, fc],
          dst: [toR, toC],
          pieceName: piece.name,
          promotion: selectedPromotion.value,
          sentAt: performance.now(),
          status: 'pending',
        })
      }
    }
  }

  // Left-click priority: execute move if the square is legal, otherwise select the piece on it.
  // Deselects after a move is executed. Clicking the selected piece deselects.
  function handleSquareClick(r: number, c: number): void {
    if (!gameId.value || winner.value) return
    const piece = board.value[r]?.[c]

    if (selected.value === null) {
      if (piece && isOwnPiece(piece) && !isOnCooldown(r, c) && !isPendingPiece(r, c)) selectPiece(r, c)
      return
    }

    if (piece && isOwnPiece(piece)) {
      const [fr, fc] = selected.value
      if (fr === r && fc === c) { deselect(); return }
      if (legalMoves.value.has(`${r},${c}`)) { attemptMove(r, c); return }
      if (!isOnCooldown(r, c) && !isPendingPiece(r, c)) selectPiece(r, c)
      return
    }

    if (legalMoves.value.has(`${r},${c}`)) attemptMove(r, c)
  }

  // Right-click priority: execute move if the square is legal. Always deselects regardless of outcome.
  function handleSquareRightClick(r: number, c: number): void {
    if (!gameId.value || winner.value || !selected.value) return
    const [fr, fc] = selected.value
    if (fr !== r || fc !== c) attemptMove(r, c)
  }

  return {
    // state
    board, cooldowns, maxCooldowns, pieceNames, stablePromotionNames, playerColor, gameId, winner,
    inCheck, inAntiCheck,
    selected, legalMoves, selectedPromotion, rtt,
    latencyHidingEnabled, rejectedSquares,
    // actions
    connect, disconnect, resetGameState, startNewGame,
    setLatencyHiding,
    selectPiece, deselect, attemptMove,
    handleSquareClick, handleSquareRightClick,
  }
})
