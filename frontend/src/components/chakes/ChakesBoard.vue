<script setup lang="ts">
import { computed } from 'vue'
import BoardGrid from '@/components/board/BoardGrid.vue'
import ChakesSquare from './ChakesSquare.vue'
import type { Color, Cooldowns } from '@/services/types'
import type { DisplayBoard } from '@/chakes/types'
import { isLightSquare, sameSquare, squareKey, type Square } from '@/chakes/square'
import { orientedSquares } from '@/chakes/orientation'
import { responsiveSquareSize } from '@/chakes/boardSize'

// Coordinate label alphabet: a-z, A-Z, then Greek α-ω (76 total, covers up to 64 columns)
const FILE_LABELS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZαβγδεζηθικλμνξοπρστυφχψω'

const props = defineProps<{
  board: DisplayBoard
  cooldowns: Cooldowns
  maxCooldowns: Record<string, number>
  /** Side the board is viewed from (spectators pass 'white'). */
  viewer: Color
  selected: Square | null
  legalMoves: Set<string>
  rejectedSquares: Set<string>
}>()

const emit = defineEmits<{
  (e: 'squareClick', square: Square): void
  (e: 'squareRightClick', square: Square, event: MouseEvent): void
}>()

const rows = computed(() => props.board.length)
const cols = computed(() => props.board[0]?.length ?? 0)

// Display-ordered grid of board-space squares; every lookup below is in board space.
const squares = computed(() => orientedSquares(rows.value, cols.value, props.viewer))

const fileLabels = computed(() => (squares.value[0] ?? []).map(([, c]) => FILE_LABELS[c] ?? '?'))
const rankLabels = computed(() => squares.value.map(([[r]]) => String(r + 1)))
// Files sit on the edge nearest rank 1, which is the bottom unless viewing as black.
const fileLabelsOnBottom = computed(() => props.viewer !== 'black')

function pieceAt([r, c]: Square) {
  return props.board[r]?.[c] ?? null
}
</script>

<template>
  <div
    class="board-with-labels"
    :style="{ '--sq': responsiveSquareSize(cols || 8) }"
  >
    <!-- Top row: file labels when viewing as black, else empty spacers -->
    <div class="col-labels-row">
      <div class="label-cell" />
      <div
        v-for="(label, c) in fileLabels"
        :key="c"
        class="label-cell"
      >
        {{ fileLabelsOnBottom ? '' : label }}
      </div>
      <div class="label-cell" />
    </div>

    <!-- Middle: rank labels | board | empty rank column -->
    <div class="board-and-ranks">
      <div class="rank-labels">
        <div
          v-for="(label, r) in rankLabels"
          :key="r"
          class="label-cell"
        >
          {{ label }}
        </div>
      </div>
      <BoardGrid
        v-slot="{ cell: sq }"
        :cells="squares"
      >
        <ChakesSquare
          :piece="pieceAt(sq)"
          :is-light="isLightSquare(sq)"
          :is-selected="sameSquare(selected, sq)"
          :is-legal-move="legalMoves.has(squareKey(sq))"
          :is-rejected="rejectedSquares.has(squareKey(sq))"
          :cooldown="cooldowns[sq[0]]?.[sq[1]] ?? 0"
          :max-cooldown="maxCooldowns[pieceAt(sq)?.name ?? ''] ?? 1"
          @click="emit('squareClick', sq)"
          @right-click="emit('squareRightClick', sq, $event)"
        />
      </BoardGrid>
      <div class="rank-labels">
        <div
          v-for="(_, r) in rankLabels"
          :key="r"
          class="label-cell"
        />
      </div>
    </div>

    <!-- Bottom row: file labels when viewing as white, else empty spacers -->
    <div class="col-labels-row">
      <div class="label-cell" />
      <div
        v-for="(label, c) in fileLabels"
        :key="c"
        class="label-cell"
      >
        {{ fileLabelsOnBottom ? label : '' }}
      </div>
      <div class="label-cell" />
    </div>
  </div>
</template>

<style scoped>
.board-with-labels {
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
.label-cell {
  width: var(--sq);
  height: var(--sq);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: calc(var(--sq) * 0.32);
  font-weight: 600;
  color: var(--board-label);
  user-select: none;
}
</style>
