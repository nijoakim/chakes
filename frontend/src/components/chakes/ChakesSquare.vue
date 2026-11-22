<!--
  ChakesSquare — a game board square: a BoardSquare with an optional piece
  sprite, a cooldown indicator, a "ready" flash and a rejected-move flash.
  Emits raw click and right-click events; all game-logic decisions are left
  to the parent.
-->

<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
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

// The cooldown indicator is drawn around the piece so the piece keeps its
// true colour:
//  - a translucent fill painted *behind* the piece that drains top-down
//    (scaleY), giving the whole square an obvious "not ready" state;
//  - a high-contrast bar along the bottom edge that drains right-to-left
//    (scaleX), so the remaining time reads at a glance even where the piece
//    hides most of the fill.
// Both are animated with a CSS transition driven by imperative style
// manipulation rather than a reactive binding. This lets a single linear
// transition run entirely in the browser's compositor between server pushes,
// without a JS animation loop. On each new value we snap to the current
// fraction (transition: none) then kick off a fresh transition to 0 over the
// remaining seconds. The forced reflow between the two style writes is
// required: without it the browser batches both writes and never sees the
// starting state, so the transition is skipped. One reflow covers both
// elements.
const fillRef = ref<HTMLElement | null>(null)
const barRef = ref<HTMLElement | null>(null)

watch(
  () => props.cooldown,
  (cd) => {
    const fill = fillRef.value
    const bar = barRef.value
    if (!fill || !bar || cd <= 0) return
    const frac = Math.min(1, cd / (props.maxCooldown || 1))
    fill.style.transition = 'none'
    bar.style.transition = 'none'
    fill.style.transform = `scaleY(${frac})`
    bar.style.transform = `scaleX(${frac})`
    void fill.offsetHeight // force reflow so the starting transforms are registered
    fill.style.transition = `transform ${cd}s linear`
    bar.style.transition = `transform ${cd}s linear`
    fill.style.transform = 'scaleY(0)'
    bar.style.transform = 'scaleX(0)'
  },
  { flush: 'post', immediate: true },
)

// --- "Ready" flash ---

// When a cooldown expires (> 0 -> 0) on a square that still holds a piece,
// show a short ring pulse. The element is keyed so back-to-back expiries
// restart the CSS animation; it is removed once the animation has run.
const READY_FLASH_MS = 350
const readyKey = ref(0)
const showReady = ref(false)
let readyTimer: ReturnType<typeof setTimeout> | null = null

watch(
  () => props.cooldown,
  (cd, prev) => {
    if (prev === undefined || prev <= 0 || cd > 0 || !props.piece) return
    readyKey.value++
    showReady.value = true
    if (readyTimer !== null) clearTimeout(readyTimer)
    readyTimer = setTimeout(() => {
      showReady.value = false
      readyTimer = null
    }, READY_FLASH_MS)
  },
)

onBeforeUnmount(() => {
  if (readyTimer !== null) clearTimeout(readyTimer)
})
</script>

<template>
  <BoardSquare
    class="chakes-square"
    :class="{ piece: piece !== null, 'on-cooldown': cooldown > 0, 'legal-move': isLegalMove }"
    :light="isLight"
    :selected="isSelected"
    :legal="isLegalMove"
    :occupied="piece !== null"
    @click="emit('click')"
    @contextmenu.prevent="emit('rightClick', $event)"
  >
    <div
      v-if="cooldown > 0"
      ref="fillRef"
      class="cooldown-fill"
    />
    <PieceSprite
      v-if="piece"
      class="square-piece"
      :name="piece.name"
      :color="piece.owner"
      :pending="piece.pending"
    />
    <div
      v-if="cooldown > 0"
      class="cooldown-track"
    >
      <div
        ref="barRef"
        class="cooldown-bar"
      />
    </div>
    <div
      v-if="showReady"
      :key="readyKey"
      class="ready-flash"
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

/* Stacking, bottom to top: square colour, selected / legal marker
   (BoardSquare ::before/::after), cooldown fill / ready flash, piece (z 1),
   cooldown bar (z 2), rejected flash (z 3). */
.square-piece {
  position: relative;
  z-index: 1;
}

.cooldown-fill {
  position: absolute;
  inset: 0;
  transform-origin: bottom;
  will-change: transform;
  background: var(--board-cooldown-fill, rgba(30, 50, 100, 0.26));
  pointer-events: none;
}

/* Bottom-edge timer bar. The track gives the bar a consistent dark backing so
   it reads on both light and dark squares. */
.cooldown-track {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: max(3px, calc(var(--sq, 64px) * 0.09));
  background: var(--board-cooldown-track, rgba(15, 20, 35, 0.55));
  pointer-events: none;
  z-index: 2;
}
.cooldown-bar {
  width: 100%;
  height: 100%;
  transform-origin: left;
  will-change: transform;
  background: var(--board-cooldown-bar, #ffb02e);
}

.ready-flash {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0; /* under the piece: the glow must not tint it */
  box-shadow: inset 0 0 0 max(2px, calc(var(--sq, 64px) * 0.07)) var(--board-ready, rgba(70, 205, 95, 0.95));
  background: var(--board-ready-glow, rgba(150, 255, 170, 0.25));
  animation: ready-flash 350ms ease-out forwards;
}
@keyframes ready-flash {
  0%   { opacity: 0; }
  25%  { opacity: 1; }
  100% { opacity: 0; }
}
@media (prefers-reduced-motion: reduce) {
  /* No pulse: a brief, static, softer highlight instead. */
  .ready-flash {
    animation: none;
    opacity: 0.6;
  }
}

.rejected-flash {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: var(--board-rejected);
  animation: rejection-flash 0.3s ease-out forwards;
  z-index: 3;
}
@keyframes rejection-flash {
  from { opacity: 1; }
  to   { opacity: 0; }
}
</style>
