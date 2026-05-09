import { computed, type Ref } from 'vue'
import type { Board, Cooldowns, Color } from '../services/api'

export function useBoardOrientation(
  board: Ref<Board>,
  cooldowns: Ref<Cooldowns>,
  playerColor: Ref<Color>,
) {
  const displayBoard = computed<Board>(() => {
    if (playerColor.value === 'black') {
      return [...board.value].reverse().map((row) => [...row].reverse())
    }
    return board.value
  })

  const displayCooldowns = computed<Cooldowns>(() => {
    if (playerColor.value === 'black') {
      return [...cooldowns.value].reverse().map((row) => [...row].reverse())
    }
    return cooldowns.value
  })

  function displayToBoard(displayR: number, displayC: number): [number, number] {
    if (playerColor.value !== 'black') return [displayR, displayC]
    const rows = board.value.length
    const cols = board.value[0]?.length ?? 0
    return [rows - 1 - displayR, cols - 1 - displayC]
  }

  function boardToDisplay(r: number, c: number): [number, number] {
    if (playerColor.value !== 'black') return [r, c]
    const rows = board.value.length
    const cols = board.value[0]?.length ?? 0
    return [rows - 1 - r, cols - 1 - c]
  }

  return { displayBoard, displayCooldowns, displayToBoard, boardToDisplay }
}
