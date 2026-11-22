<!--
  MoveMarker — the symbol drawn on a square of a piece-movement diagram:
  filled dot = move or capture, ring = move only, cross = capture only.
  A dashed outline marks a first-move-only square; an inner diamond a square
  where the piece may capture one of its own pieces.
-->

<script lang="ts">
export type MarkerKind = 'both' | 'move' | 'capture'
</script>

<script setup lang="ts">
defineProps<{
  kind: MarkerKind
  initial?: boolean
  friend?: boolean
}>()
</script>

<template>
  <svg
    class="move-marker"
    viewBox="0 0 100 100"
    aria-hidden="true"
  >
    <circle
      v-if="kind === 'both'"
      cx="50"
      cy="50"
      r="20"
      :class="{ dashed: initial }"
      class="fill"
    />
    <circle
      v-else-if="kind === 'move'"
      cx="50"
      cy="50"
      :r="initial ? 26 : 19"
      class="ring"
      :class="{ dashed: initial }"
    />
    <path
      v-else
      d="M32 32 L68 68 M68 32 L32 68"
      class="cross"
    />
    <path
      v-if="friend"
      d="M50 40 L60 50 L50 60 L40 50 Z"
      class="fill"
    />
  </svg>
</template>

<style scoped>
.move-marker {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  /* The board colours are the same in light and dark mode, so fixed ink works. */
  color: #12282e;
}
.fill {
  fill: currentColor;
  opacity: 0.8;
}
.ring {
  fill: none;
  stroke: currentColor;
  stroke-width: 8;
  opacity: 0.8;
}
.ring.dashed {
  stroke-dasharray: 9 6;
  stroke-width: 7;
}
.fill.dashed {
  fill: none;
  stroke: currentColor;
  stroke-width: 7;
  stroke-dasharray: 9 6;
}
.cross {
  fill: none;
  stroke: currentColor;
  stroke-width: 10;
  stroke-linecap: round;
  opacity: 0.8;
}
</style>
