<!--
  BoardSquare — a plain, presentational board square: light/dark background,
  optional selected / legal-move highlight, and arbitrary content in the
  default slot. Size comes from the inherited `--sq` CSS variable.

  Legal-move markers follow the usual chess-UI convention: a centred dot on an
  empty target square, and corner wedges (a ring cut off by the square) on a
  target that holds a capturable piece. Pass `occupied` to get the latter.
-->

<script setup lang="ts">
defineProps<{
  light: boolean
  selected?: boolean
  legal?: boolean
  occupied?: boolean
}>()
</script>

<template>
  <div
    class="board-square"
    :class="[light ? 'light' : 'dark', { selected, legal, occupied }]"
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

/* Selected tint on ::after, legal marker on ::before, so both can coexist. */
.selected::after,
.legal::before {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.selected::after { background: var(--board-selected); }

/* Empty target: centred dot. */
.legal::before {
  background: radial-gradient(
    circle,
    var(--board-legal-marker, rgba(20, 85, 30, 0.5)) 0 17%,
    transparent calc(17% + 1px)
  );
}
/* Capture target: corner wedges, leaving the piece unobscured. */
.legal.occupied::before {
  background: radial-gradient(
    circle,
    transparent 0 calc(78% - 1px),
    var(--board-legal-marker, rgba(20, 85, 30, 0.5)) 78%
  );
}
/* With a mouse, hovering a target fills the square to confirm the drop. */
@media (hover: hover) {
  .legal:hover::before {
    background: var(--board-legal-hover, rgba(20, 85, 30, 0.3));
  }
}
</style>
