<!--
  ChakesSquare — a game board square: a BoardSquare with an optional piece
  sprite, a cooldown indicator, a "ready" flash, a rejected-move flash and
  shake, a fading last-move highlight, a check pulse and a fading ghost of a
  just-captured piece. Emits raw click and right-click events; all game-logic
  decisions are left to the parent. Piece slides are driven by ChakesBoard,
  which finds the piece through its `square-piece` class.
-->

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import BoardSquare from '@/components/board/BoardSquare.vue'
import PieceSprite from './PieceSprite.vue'
import type { DisplayPiece } from '@/chakes/types'
import { MOVE_HIGHLIGHT_MS } from '@/composables/useRecentMoves'

/** Last-move highlight on this square; `id` changes restart the fade. */
export interface MoveMark {
  id: number
  own: boolean
  /** Destination (rather than source) of the move. */
  to: boolean
}

/** A just-captured piece, shown briefly while it fades out. */
export interface CaptureGhost {
  id: number
  piece: DisplayPiece
}

const props = defineProps<{
  piece: DisplayPiece | null
  isLight: boolean
  isSelected: boolean
  isLegalMove: boolean
  isRejected: boolean
  cooldown: number    // remaining cooldown in seconds as of the last server push; 0 when expired
  maxCooldown: number // full cooldown duration for this piece type
  moveMark?: MoveMark | null
  ghost?: CaptureGhost | null
  /** The piece here is a King in check, or an Anti-King in anti-check. */
  alert?: 'check' | 'anti-check' | null
}>()

const markStyle = { animationDuration: `${MOVE_HIGHLIGHT_MS}ms` }

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

function startCooldownAnimation(cd: number): void {
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
}

watch(() => props.cooldown, startCooldownAnimation, { flush: 'post' })
// A square that mounts already cooling (joining or reloading mid-game) has no
// elements yet when an immediate watcher would run, so start it once mounted.
onMounted(() => startCooldownAnimation(props.cooldown))

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
      v-if="moveMark"
      :key="moveMark.id"
      class="move-mark"
      :class="{ own: moveMark.own, to: moveMark.to }"
      :style="markStyle"
    />
    <div
      v-if="alert"
      class="check-pulse"
      :class="alert"
    />
    <div
      v-if="cooldown > 0"
      ref="fillRef"
      class="cooldown-fill"
    />
    <PieceSprite
      v-if="ghost"
      :key="ghost.id"
      class="capture-ghost"
      :name="ghost.piece.name"
      :color="ghost.piece.owner"
    />
    <PieceSprite
      v-if="piece"
      class="square-piece"
      :class="{ shake: isRejected }"
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
   (BoardSquare ::before/::after), last-move mark / check pulse / cooldown
   fill / ready flash, capture ghost and piece (z 1), cooldown bar (z 2),
   rejected flash (z 3); a sliding piece is lifted to z 5 by ChakesBoard. */
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

/* Rejected move: the piece shakes along with the flash. Uses the individual
   `translate` property so it composes with the slide, which animates
   `transform`. */
.square-piece.shake {
  animation: rejection-shake 0.3s ease-out;
}
@keyframes rejection-shake {
  0%, 100% { translate: 0; }
  20%      { translate: -9% 0; }
  40%      { translate: 7% 0; }
  60%      { translate: -5% 0; }
  80%      { translate: 2% 0; }
}

/* Last move: a tint on the source and destination that holds briefly, then
   fades (duration set from MOVE_HIGHLIGHT_MS). Opponent moves are warm amber,
   own moves a quieter blue, so the eye goes to what the opponent did. */
.move-mark {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: var(--board-last-move-from, rgba(255, 190, 30, 0.32));
  animation: move-mark-fade 1.8s ease-in forwards;
}
.move-mark.to {
  background: var(--board-last-move-to, rgba(255, 180, 0, 0.5));
}
.move-mark.own {
  background: var(--board-own-move-from, rgba(70, 140, 255, 0.2));
}
.move-mark.own.to {
  background: var(--board-own-move-to, rgba(70, 140, 255, 0.32));
}
@keyframes move-mark-fade {
  0%, 35% { opacity: 1; }
  100%    { opacity: 0; }
}

/* King in check: a pulsing red glow under the piece. Anti-check (an
   Anti-King that is NOT attacked, which it must be) pulses violet. */
.check-pulse {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: radial-gradient(
    circle,
    var(--board-check, rgba(255, 30, 30, 0.95)) 0 30%,
    var(--board-check-edge, rgba(230, 0, 0, 0.35)) 75%,
    transparent 100%
  );
  animation: check-pulse 0.8s ease-in-out infinite alternate;
}
.check-pulse.anti-check {
  background: radial-gradient(
    circle,
    var(--board-anti-check, rgba(170, 70, 255, 0.95)) 0 30%,
    var(--board-anti-check-edge, rgba(130, 30, 230, 0.35)) 75%,
    transparent 100%
  );
}
@keyframes check-pulse {
  from { opacity: 0.45; }
  to   { opacity: 1; }
}

/* Captured piece: shrinks and fades away under the arriving piece. */
.capture-ghost {
  position: absolute;
  z-index: 1;
  pointer-events: none;
  animation: capture-out 0.2s ease-in forwards;
}
@keyframes capture-out {
  from { opacity: 1; transform: scale(1); }
  to   { opacity: 0; transform: scale(0.6); }
}

@media (prefers-reduced-motion: reduce) {
  .square-piece.shake { animation: none; }
  /* Static highlights; ChakesBoard removes them on the same schedule. */
  .move-mark { animation: none; opacity: 0.7; }
  .check-pulse { animation: none; opacity: 0.85; }
  .capture-ghost { display: none; }
}
</style>
