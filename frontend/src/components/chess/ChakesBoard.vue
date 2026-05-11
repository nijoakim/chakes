<script setup lang="ts">
import { computed, toRef } from 'vue'
import ChakesSquare from './ChakesSquare.vue'
import type { Board, Cooldowns, Color } from '../../services/api'
import { useBoardOrientation } from '../../composables/useBoardOrientation'

// Coordinate label alphabet: a-z, A-Z, then Greek α-ω (76 total, covers up to 64 columns)
const FILE_LABELS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZαβγδεζηθικλμνξοπρστυφχψω'

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

const fileLabelsOnBottom = computed(() => props.playerColor === 'white')

function fileLabel(displayC: number): string {
  const [, bc] = displayToBoard(0, displayC)
  return FILE_LABELS[bc] ?? '?'
}

function rankLabel(displayR: number): string {
  const [br] = displayToBoard(displayR, 0)
  return String(br + 1)
}
</script>

<template>
  <div
    class="board-with-labels"
    :style="{ '--chakes-cols': displayBoard[0]?.length ?? 8 }"
  >
    <!-- Top row: file labels for black, empty spacers for white -->
    <div class="col-labels-row">
      <div class="label-corner" />
      <div v-for="(_, c) in displayBoard[0] ?? []" :key="c" class="label-cell">
        {{ fileLabelsOnBottom ? '' : fileLabel(c) }}
      </div>
      <div class="label-corner" />
    </div>

    <!-- Middle: rank labels | board | empty rank column -->
    <div class="board-and-ranks">
      <div class="rank-labels">
        <div v-for="(_, r) in displayBoard" :key="r" class="label-cell">
          {{ rankLabel(r) }}
        </div>
      </div>
      <div class="board">
        <div v-for="(row, r) in displayBoard" :key="r" class="row">
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
      <div class="rank-labels">
        <div v-for="(_, r) in displayBoard" :key="r" class="label-cell" />
      </div>
    </div>

    <!-- Bottom row: file labels for white, empty spacers for black -->
    <div class="col-labels-row">
      <div class="label-corner" />
      <div v-for="(_, c) in displayBoard[0] ?? []" :key="c" class="label-cell">
        {{ fileLabelsOnBottom ? fileLabel(c) : '' }}
      </div>
      <div class="label-corner" />
    </div>
  </div>
</template>

<style scoped>
.board-with-labels {
  /* +2 reserves space for rank label columns on both sides */
  --chakes-sq: min(64px, calc((100vw - 44px) / (var(--chakes-cols, 8) + 2)));
  display: inline-flex;
  flex-direction: column;
}
.col-labels-row {
  display: flex;
}
.board-and-ranks {
  display: flex;
  flex-direction: row;
}
.rank-labels {
  display: flex;
  flex-direction: column;
}
.label-corner {
  width: var(--chakes-sq);
  height: var(--chakes-sq);
}
.label-cell {
  width: var(--chakes-sq);
  height: var(--chakes-sq);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: calc(var(--chakes-sq) * 0.32);
  font-weight: 600;
  color: #555;
  user-select: none;
}
.board {
  display: inline-block;
  border: 2px solid #333;
}
.row {
  display: flex;
}
</style>
