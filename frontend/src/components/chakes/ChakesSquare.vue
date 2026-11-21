<!--
  ChakesSquare — a game board square: a BoardSquare with an optional piece
  sprite, a cooldown overlay and a rejected-move flash. Emits raw click and
  right-click events; all game-logic decisions are left to the parent.
-->

<script setup lang="ts">
import { ref, watch } from 'vue'
import BoardSquare from '@/components/board/BoardSquare.vue'
import PieceSprite from './PieceSprite.vue'
import type { DisplayPiece } from '@/chakes/types'

const props = defineProps<{
  piece: DisplayPiece | null
  isLight: boolean
  isSelected: boolean
  isLegalMove: boolean
  isRejected: boolean
  cooldown: number    // remaining cooldown in seconds as of the last server push; 0 when expired
  maxCooldown: number // full cooldown duration for this piece type
}>()

const emit = defineEmits<{
  (e: 'click'): void
  (e: 'rightClick', event: MouseEvent): void
}>()

// --- Cooldown animation ---

// The overlay is animated with a CSS transition driven by imperative style
// manipulation rather than a reactive binding. This lets a single linear
// transition run entirely in the browser's compositor between server pushes,
// without a JS animation loop. On each new value we snap to the current
// fraction (transition: none) then kick off a fresh transition to 0 over the
// remaining seconds. The forced reflow between the two style writes is
// required: without it the browser batches both writes and never sees the
// starting state, so the transition is skipped.
const overlayRef = ref<HTMLElement | null>(null)

watch(
  () => props.cooldown,
  (cd) => {
    const el = overlayRef.value
    if (!el || cd <= 0) return
    const frac = cd / (props.maxCooldown || 1)
    el.style.transition = 'none'
    el.style.transform = `scaleY(${frac})`
    void el.offsetHeight // force reflow so the starting transform is registered
    el.style.transition = `transform ${cd}s linear`
    el.style.transform = 'scaleY(0)'
  },
  { flush: 'post', immediate: true },
)
</script>

<template>
  <BoardSquare
    class="chakes-square"
    :class="{ piece: piece !== null, 'on-cooldown': cooldown > 0, 'legal-move': isLegalMove }"
    :light="isLight"
    :selected="isSelected"
    :legal="isLegalMove"
    @click="emit('click')"
    @contextmenu.prevent="emit('rightClick', $event)"
  >
    <PieceSprite
      v-if="piece"
      :name="piece.name"
      :color="piece.owner"
      :pending="piece.pending"
    />
    <div
      v-if="cooldown > 0"
      ref="overlayRef"
      class="cooldown-overlay"
    />
    <div
      v-if="isRejected"
      class="rejected-flash"
    />
  </BoardSquare>
</template>

<style scoped>
.chakes-square { cursor: default; }
.chakes-square.piece { cursor: pointer; }
.chakes-square.on-cooldown { cursor: not-allowed; }
.chakes-square.legal-move { cursor: pointer; }
.cooldown-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 100%;
  transform-origin: bottom;
  will-change: transform;
  background: var(--board-cooldown);
  pointer-events: none;
}
.rejected-flash {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: var(--board-rejected);
  animation: rejection-flash 0.3s ease-out forwards;
  z-index: 1;
}
@keyframes rejection-flash {
  from { opacity: 1; }
  to   { opacity: 0; }
}
</style>
