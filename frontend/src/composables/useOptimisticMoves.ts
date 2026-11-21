import { computed, ref, watch, type Ref } from 'vue'
import type { Board, Color } from '@/services/types'
import type { DisplayBoard } from '@/chakes/types'
import { squareKey, type Square } from '@/chakes/square'

const REJECTION_FLASH_MS = 300

interface PendingMove {
  src: Square
  dst: Square
  pieceName: string
  sentAt: number
}

interface Options {
  authoritativeBoard: Ref<Board>
  playerColor: Ref<Color>
  maxCooldowns: Ref<Record<string, number>>
  enabled: Ref<boolean>
}

/**
 * Latency hiding: moves sent but not yet confirmed are overlaid on the
 * authoritative board, dropped once the server board reflects them, and
 * flashed red when the server rejects them.
 */
export function useOptimisticMoves({ authoritativeBoard, playerColor, maxCooldowns, enabled }: Options) {
  const pendingMoves = ref(new Map<string, PendingMove>())
  const rejectedSquares = ref(new Set<string>())
  const flashTimers = new Set<ReturnType<typeof setTimeout>>()

  const board = computed<DisplayBoard>(() => {
    if (!enabled.value || pendingMoves.value.size === 0) {
      return authoritativeBoard.value
    }
    const rows: DisplayBoard = authoritativeBoard.value.map((r) => r.slice())
    for (const { src: [sr, sc], dst: [dr, dc] } of pendingMoves.value.values()) {
      const piece = rows[sr]?.[sc]
      if (!piece) continue
      rows[sr][sc] = null
      rows[dr][dc] = { ...piece, pending: true }
    }
    return rows
  })

  // Reconciliation: drop pending entries once the authoritative board reflects the move.
  watch(authoritativeBoard, (b) => {
    for (const [id, { src: [sr, sc], dst: [dr, dc] }] of pendingMoves.value) {
      const dstPiece = b[dr]?.[dc]
      if (b[sr]?.[sc] == null && dstPiece != null && dstPiece.owner === playerColor.value) {
        pendingMoves.value.delete(id)
      }
    }
  })

  function track(id: string, src: Square, dst: Square): void {
    if (!enabled.value) return
    const piece = authoritativeBoard.value[src[0]]?.[src[1]]
    if (!piece) return
    pendingMoves.value.set(id, { src, dst, pieceName: piece.name, sentAt: performance.now() })
  }

  function reject(id: string): void {
    const m = pendingMoves.value.get(id)
    if (!m) return
    pendingMoves.value.delete(id)
    const keys = [squareKey(m.src), squareKey(m.dst)]
    rejectedSquares.value = new Set([...rejectedSquares.value, ...keys])
    const timer = setTimeout(() => {
      flashTimers.delete(timer)
      const s = new Set(rejectedSquares.value)
      keys.forEach((k) => s.delete(k))
      rejectedSquares.value = s
    }, REJECTION_FLASH_MS)
    flashTimers.add(timer)
  }

  /** A pending move's destination is treated as on cooldown from the moment it was sent. */
  function isPendingCooldown([r, c]: Square): boolean {
    if (!enabled.value) return false
    for (const m of pendingMoves.value.values()) {
      if (m.dst[0] !== r || m.dst[1] !== c) continue
      const maxCd = maxCooldowns.value[m.pieceName] ?? 0
      if (maxCd - (performance.now() - m.sentAt) / 1000 > 0) return true
    }
    return false
  }

  function isPending([r, c]: Square): boolean {
    return board.value[r]?.[c]?.pending === true
  }

  function reset(): void {
    flashTimers.forEach(clearTimeout)
    flashTimers.clear()
    pendingMoves.value = new Map()
    rejectedSquares.value = new Set()
  }

  return { board, rejectedSquares, track, reject, isPendingCooldown, isPending, reset }
}
