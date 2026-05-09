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
    return playerColor.value === 'black' ? [7 - displayR, 7 - displayC] : [displayR, displayC]
  }

  function boardToDisplay(r: number, c: number): [number, number] {
    return playerColor.value === 'black' ? [7 - r, 7 - c] : [r, c]
  }

  return { displayBoard, displayCooldowns, displayToBoard, boardToDisplay }
}
