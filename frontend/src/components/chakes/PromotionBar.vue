<script setup lang="ts">
import BoardSquare from '@/components/board/BoardSquare.vue'
import PieceSprite from './PieceSprite.vue'
import type { Color } from '@/services/types'
import { responsiveSquareSize } from '@/chakes/boardSize'

const props = defineProps<{
  pieceNames: string[]
  selected: string
  playerColor: Color
  /** Width of the game board in squares, so the promotion squares match its size. */
  cols?: number
}>()

const emit = defineEmits<{
  (e: 'select', name: string): void
}>()
</script>

<template>
  <div
    class="promotion-bar"
    :style="{ '--sq': responsiveSquareSize(props.cols ?? 8) }"
  >
    <span class="promotion-label">Promote to</span>
    <div class="promotion-squares">
      <BoardSquare
        v-for="(pieceName, i) in pieceNames"
        :key="pieceName"
        class="promo-square"
        :light="i % 2 === 0"
        :selected="selected === pieceName"
        @click="emit('select', pieceName)"
      >
        <PieceSprite
          :name="pieceName"
          :color="playerColor"
        />
      </BoardSquare>
    </div>
  </div>
</template>

<style scoped>
.promotion-bar {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 8px 0;
  border: 2px solid var(--board-border);
  border-bottom: none;
  background: var(--code-bg);
}
.promotion-label {
  font-size: 12px;
  color: var(--text);
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
.promotion-squares {
  display: flex;
}
.promo-square {
  cursor: pointer;
}
</style>
