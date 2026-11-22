import { onScopeDispose, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useGameStore } from '@/stores/game'
import { gameSocket } from '@/services/gameSocket'
import { installAudioUnlock, playSound } from '@/services/sound'
import type { Color, Cooldowns, Role } from '@/services/types'
import type { DisplayBoard, SideFlags } from '@/chakes/types'

/** A game id that appears after the lobby sat game-less this long is a fresh start, not a join. */
const JOIN_SETTLE_MS = 250

interface Snapshot {
  board: DisplayBoard
  role: Role | null
  gameId: string | null
  winner: Color | null
  inCheck: SideFlags
  inAntiCheck: SideFlags
  cooldowns: Cooldowns
  rejected: ReadonlySet<string>
}

function countPieces(board: DisplayBoard): Record<Color, number> {
  const n = { white: 0, black: 0 }
  for (const row of board) for (const p of row) if (p) n[p.owner]++
  return n
}

/**
 * Derive sound events from the game store by diffing consecutive snapshots.
 * All store fields are watched together so one server push (board, cooldowns,
 * game id, winner and check flags arrive synchronously) is seen as one change.
 */
export function useGameSounds(): void {
  installAudioUnlock()
  const store = useGameStore()
  const { board, role, gameId, winner, inCheck, inAntiCheck, cooldownGrid, rejectedSquares } = storeToRefs(store)

  let lastKnownGameId: string | null = null
  let noGameSince: number | null = null
  /** We saw this game being played (not just joined it finished), so its end is news. */
  let sawLive = false

  function onChange(cur: Snapshot, prev: Snapshot): void {
    if (cur.role === null) {
      lastKnownGameId = null
      noGameSince = null
      sawLive = false
      return
    }
    const me: Color | null = cur.role === 'spectator' ? null : cur.role

    // --- Game lifecycle ---
    if (cur.gameId === null) {
      if (noGameSince === null) noGameSince = performance.now()
      return
    }
    if (cur.gameId !== prev.gameId) {
      // A different game than the last one we saw in this lobby, or the first
      // game after sitting in an empty lobby (rather than joining a running one).
      const isNewGame = lastKnownGameId !== null && cur.gameId !== lastKnownGameId
      const settled = noGameSince !== null && performance.now() - noGameSince >= JOIN_SETTLE_MS
      sawLive = false
      if (cur.gameId !== lastKnownGameId && (isNewGame || settled) && cur.winner === null) {
        playSound('gameStart')
        sawLive = true
      }
      lastKnownGameId = cur.gameId
      noGameSince = null
      return // the first board of a game is a reset, not a move
    }

    if (cur.winner !== null && prev.winner === null) {
      // The final move's own click/capture would only muddy the end cue.
      if (sawLive) playSound(me === null ? 'gameEnd' : cur.winner === me ? 'gameWin' : 'gameLoss')
      return
    }

    // --- Moves and captures ---
    const prevBoard = prev.board
    const curBoard = cur.board
    if (curBoard !== prevBoard && prevBoard.length > 0 && curBoard.length === prevBoard.length) {
      // A rejected optimistic move snaps back; that is the reject cue, not a move.
      const newlyRejected = new Set([...cur.rejected].filter((k) => !prev.rejected.has(k)))
      const perspective: Color = me ?? 'white'
      let ownMoved = false
      let oppMoved = false
      for (let r = 0; r < curBoard.length; r++) {
        for (let c = 0; c < curBoard[r].length; c++) {
          const now = curBoard[r][c]
          const before = prevBoard[r]?.[c]
          if (!now || newlyRejected.has(`${r},${c}`)) continue
          if (before && before.owner === now.owner) continue // unchanged, or promoted in place
          if (now.owner === perspective) ownMoved = true
          else oppMoved = true
        }
      }
      if (ownMoved || oppMoved) {
        sawLive = true
        const before = countPieces(prevBoard)
        const after = countPieces(curBoard)
        if (after.white < before.white || after.black < before.black) playSound('capture')
        else {
          if (ownMoved) playSound('moveOwn')
          if (oppMoved) playSound('moveOpponent')
        }
      }
    }

    if (cur.winner !== null || me === null) return

    // --- Check / anti-check for the side we play ---
    if (cur.inCheck[me] && !prev.inCheck[me]) playSound('check')
    else if (cur.inAntiCheck[me] && !prev.inAntiCheck[me]) playSound('antiCheck')

    // --- Own pieces coming off cooldown (coalesced by the engine) ---
    if (cur.cooldowns !== prev.cooldowns) {
      for (let r = 0; r < cur.cooldowns.length; r++) {
        for (let c = 0; c < cur.cooldowns[r].length; c++) {
          if (!((prev.cooldowns[r]?.[c] ?? 0) > 0 && cur.cooldowns[r][c] <= 0)) continue
          const piece = curBoard[r]?.[c]
          const before = prevBoard[r]?.[c]
          if (piece && piece.owner === me && !piece.pending && before?.owner === me && before.name === piece.name) {
            playSound('ready')
            return
          }
        }
      }
    }
  }

  const stop = watch(
    (): Snapshot => ({
      board: board.value,
      role: role.value,
      gameId: gameId.value,
      winner: winner.value,
      inCheck: inCheck.value,
      inAntiCheck: inAntiCheck.value,
      cooldowns: cooldownGrid.value,
      rejected: rejectedSquares.value,
    }),
    onChange,
  )

  // Rejections come straight from the server reply, so they sound with or
  // without latency hiding (only the latter marks rejectedSquares).
  const offReject = gameSocket.on('moveResult', ({ ok }) => {
    if (!ok) playSound('reject')
  })

  onScopeDispose(() => {
    stop()
    offReject()
  })
}
