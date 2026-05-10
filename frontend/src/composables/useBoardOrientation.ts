import { computed, type Ref } from 'vue'
import type { Board, Cooldowns, Color } from '../services/api'

export function useBoardOrientation(
  board: Ref<Board>,
  cooldowns: Ref<Cooldowns>,
  playerColor: Ref<Color>,
) {
  // Backend board[r][c] has r=0 at rank 1 (engine y=0, white's back rank).
  // Display convention: white sees rank 8 at top, black sees rank 1 at top with mirrored columns.
  const displayBoard = computed<Board>(() => {
    if (playerColor.value === 'black') {
      return board.value.map((row) => [...row].reverse())
    }
    return [...board.value].reverse()
  })

  const displayCooldowns = computed<Cooldowns>(() => {
    if (playerColor.value === 'black') {
      return cooldowns.value.map((row) => [...row].reverse())
    }
    return [...cooldowns.value].reverse()
  })

  function displayToBoard(displayR: number, displayC: number): [number, number] {
    const rows = board.value.length
    const cols = board.value[0]?.length ?? 0
    if (playerColor.value === 'black') return [displayR, cols - 1 - displayC]
    return [rows - 1 - displayR, displayC]
  }

  function boardToDisplay(r: number, c: number): [number, number] {
    const rows = board.value.length
    const cols = board.value[0]?.length ?? 0
    if (playerColor.value === 'black') return [r, cols - 1 - c]
    return [rows - 1 - r, c]
  }

  return { displayBoard, displayCooldowns, displayToBoard, boardToDisplay }
}
