<script setup lang="ts">
import PieceSprite from './PieceSprite.vue'
import type { Color } from '../../services/api'

const props = defineProps<{
  pieceNames: string[]
  selected: string
  playerColor: Color
  cols?: number
}>()

const emit = defineEmits<{
  (e: 'select', name: string): void
}>()
</script>

<template>
  <div
    class="promotion-bar"
    :style="{ '--promo-cols': props.cols ?? 8 }"
  >
    <span class="promotion-label">Promote to</span>
    <div class="promotion-squares">
      <div
        v-for="(pieceName, i) in pieceNames"
        :key="pieceName"
        class="promo-square"
        :class="[
          i % 2 === 0 ? 'light' : 'dark',
          selected === pieceName ? 'active' : '',
        ]"
        @click="emit('select', pieceName)"
      >
        <PieceSprite
          :name="pieceName"
          :color="playerColor"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.promotion-bar {
  --sq: min(64px, calc((100vw - 44px) / var(--promo-cols, 8)));
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 8px 0;
  border: 2px solid #333;
  border-bottom: none;
  background: rgba(0, 0, 0, 0.04);
}
.promotion-label {
  font-size: 12px;
  color: #666;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
.promotion-squares {
  display: flex;
}
.promo-square {
  width: var(--sq);
  height: var(--sq);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  user-select: none;
  position: relative;
}
.light { background: #f0d9b5; }
.dark  { background: #b58863; }
.promo-square.active::after {
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(246, 246, 105, 0.6);
  pointer-events: none;
}
</style>
