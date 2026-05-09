<script setup lang="ts">
import { toRef } from 'vue'
import ChakesSquare from './ChakesSquare.vue'
import type { Board, Cooldowns, Color } from '../../services/api'
import { useBoardOrientation } from '../../composables/useBoardOrientation'

const props = defineProps<{
  board: Board
  cooldowns: Cooldowns
  maxCooldowns: Record<string, number>
  playerColor: Color
  selected: [number, number] | null
  legalMoves: Set<string>
}>()

const emit = defineEmits<{
  (e: 'squareClick', r: number, c: number): void
  (e: 'squareRightClick', r: number, c: number, event: MouseEvent): void
}>()

const { displayBoard, displayCooldowns, displayToBoard } = useBoardOrientation(
  toRef(props, 'board'),
  toRef(props, 'cooldowns'),
  toRef(props, 'playerColor'),
)

function isSelected(displayR: number, displayC: number): boolean {
  if (!props.selected) return false
  const [br, bc] = displayToBoard(displayR, displayC)
  return props.selected[0] === br && props.selected[1] === bc
}

function isLegalMove(displayR: number, displayC: number): boolean {
  const [br, bc] = displayToBoard(displayR, displayC)
  return props.legalMoves.has(`${br},${bc}`)
}

function onSquareClick(displayR: number, displayC: number) {
  const [r, c] = displayToBoard(displayR, displayC)
  emit('squareClick', r, c)
}

function onSquareRightClick(displayR: number, displayC: number, event: MouseEvent) {
  const [r, c] = displayToBoard(displayR, displayC)
  emit('squareRightClick', r, c, event)
}
</script>

<template>
  <div class="board">
    <div
      v-for="(row, r) in displayBoard"
      :key="r"
      class="row"
    >
      <ChakesSquare
        v-for="(piece, c) in row"
        :key="c"
        :piece="piece"
        :is-light="(r + c) % 2 === 0"
        :is-selected="isSelected(r, c)"
        :is-legal-move="isLegalMove(r, c)"
        :cooldown="displayCooldowns[r]?.[c] ?? 0"
        :max-cooldown="maxCooldowns[piece?.name ?? ''] ?? 1"
        @click="onSquareClick(r, c)"
        @right-click="onSquareRightClick(r, c, $event)"
      />
    </div>
  </div>
</template>

<style scoped>
.board {
  --chakes-sq: min(64px, calc((100vw - 44px) / 8));
  display: inline-block;
  border: 2px solid #333;
}
.row {
  display: flex;
}
</style>
