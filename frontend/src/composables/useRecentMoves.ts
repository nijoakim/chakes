import { shallowRef, type Ref } from 'vue'
import type { Board, Color } from '@/services/types'
import type { Square } from '@/chakes/square'
import { diffBoards } from '@/chakes/moveDiff'

/** How long a last-move highlight stays up (it fades out over this time). */
export const MOVE_HIGHLIGHT_MS = 1800

export interface RecentMove {
  /** Unique per move, so a repeated highlight on a square restarts its fade. */
  id: number
  from: Square
  to: Square
  /** Made by this client's side (always false for spectators). */
  own: boolean
}

/**
 * Recently made moves, recovered by diffing consecutive authoritative boards
 * of the same game (the server does not say which move happened). Each move
 * is listed for MOVE_HIGHLIGHT_MS. The first board of a game, and any board of
 * a different game, only sets the baseline.
 */
export function useRecentMoves(playerColor: Ref<Color | null>) {
  const recentMoves = shallowRef<RecentMove[]>([])
  let lastBoard: Board = []
  let lastGameId: string | null = null
  let nextId = 1
  const timers = new Set<ReturnType<typeof setTimeout>>()

  /** Feed every authoritative board together with the game it belongs to. */
  function observe(gameId: string, board: Board): void {
    const diff = gameId === lastGameId ? diffBoards(lastBoard, board) : null
    lastBoard = board
    lastGameId = gameId
    if (!diff || diff.moves.length === 0) return

    const added = diff.moves.map(({ from, to, piece }) => ({
      id: nextId++, from, to, own: piece.owner === playerColor.value,
    }))
    recentMoves.value = [...recentMoves.value, ...added]
    const ids = new Set(added.map((m) => m.id))
    const timer = setTimeout(() => {
      timers.delete(timer)
      recentMoves.value = recentMoves.value.filter((m) => !ids.has(m.id))
    }, MOVE_HIGHLIGHT_MS)
    timers.add(timer)
  }

  function reset(): void {
    timers.forEach(clearTimeout)
    timers.clear()
    recentMoves.value = []
    lastBoard = []
    lastGameId = null
  }

  return { recentMoves, observe, reset }
}
