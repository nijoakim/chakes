<!--
  ChakesSquare — a single board square.

  Renders the square background (light/dark), an optional piece sprite, and
  visual state overlays (selected, legal-move highlight, cooldown bar). Emits
  raw click and right-click events; all game-logic decisions are left to the
  parent.
-->

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import PieceSprite from './PieceSprite.vue'
import type { PieceInstance, Color } from '../../services/api'

// --- Props & emits ---

const props = defineProps<{
  piece: PieceInstance | null
  isLight: boolean
  isSelected: boolean
  isLegalMove: boolean
  cooldown: number    // remaining cooldown in seconds (raw server value)
  maxCooldown: number // full cooldown duration for this piece type
}>()

const emit = defineEmits<{
  (e: 'click'): void
  (e: 'rightClick', event: MouseEvent): void
}>()

// --- Derived state ---

const squareClasses = computed(() => [
  props.isLight ? 'light' : 'dark',
  props.isSelected ? 'selected' : '',
  props.isLegalMove ? 'legal-move' : '',
  props.piece ? 'piece' : '',
  props.cooldown > 0 ? 'on-cooldown' : '',
])

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
  <div
    class="square"
    :class="squareClasses"
    @click="emit('click')"
    @contextmenu.prevent="emit('rightClick', $event)"
  >
    <PieceSprite
      v-if="piece"
      :name="piece.name"
      :color="(piece.owner as Color)"
    />
    <div
      v-if="cooldown > 0"
      ref="overlayRef"
      class="cooldown-overlay"
    />
  </div>
</template>

<style scoped>
.square {
  --sq: var(--chakes-sq, min(64px, calc((100vw - 44px) / 8)));
  width: var(--sq);
  height: var(--sq);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: default;
  user-select: none;
  position: relative;
}
.square.piece { cursor: pointer; }
.square.on-cooldown { cursor: not-allowed; }
.light { background: #f0d9b5; }
.dark  { background: #b58863; }
.square.selected::after,
.square.legal-move::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.square.selected::after { background: rgba(246, 246, 105, 0.6); }
.square.legal-move::after { background: rgba(130, 190, 80, 0.45); }
.square.legal-move { cursor: pointer; }
.cooldown-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 100%;
  transform-origin: bottom;
  will-change: transform;
  background: rgba(80, 80, 80, 0.5);
  pointer-events: none;
}
</style>
