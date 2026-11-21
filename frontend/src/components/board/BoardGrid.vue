<!--
  BoardGrid — lays out a 2D grid (rows of cells, already in display order)
  inside a board border. Each cell is rendered by the default scoped slot,
  usually as a BoardSquare. `squareSize` sets `--sq` (any CSS length);
  without it the size is inherited from the parent.
-->

<script setup lang="ts" generic="T">
defineProps<{
  cells: T[][]
  squareSize?: string
}>()

defineSlots<{
  default(props: { cell: T; row: number; col: number }): unknown
}>()
</script>

<template>
  <div
    class="board-grid"
    :style="squareSize ? { '--sq': squareSize } : undefined"
  >
    <div
      v-for="(rowCells, r) in cells"
      :key="r"
      class="row"
    >
      <template
        v-for="(cell, c) in rowCells"
        :key="c"
      >
        <slot
          :cell="cell"
          :row="r"
          :col="c"
        />
      </template>
    </div>
  </div>
</template>

<style scoped>
.board-grid {
  display: inline-block;
  border: 2px solid var(--board-border);
}
.row {
  display: flex;
}
</style>
