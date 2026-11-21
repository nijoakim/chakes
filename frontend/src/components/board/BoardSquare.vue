<!--
  BoardSquare — a plain, presentational board square: light/dark background,
  optional selected / legal-move highlight, and arbitrary content in the
  default slot. Size comes from the inherited `--sq` CSS variable.
-->

<script setup lang="ts">
defineProps<{
  light: boolean
  selected?: boolean
  legal?: boolean
}>()
</script>

<template>
  <div
    class="board-square"
    :class="[light ? 'light' : 'dark', { selected, legal }]"
  >
    <slot />
  </div>
</template>

<style scoped>
.board-square {
  width: var(--sq, 64px);
  height: var(--sq, 64px);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  user-select: none;
}
.light { background: var(--board-light); }
.dark  { background: var(--board-dark); }
.selected::after,
.legal::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.selected::after { background: var(--board-selected); }
.legal::after    { background: var(--board-legal); }
</style>
