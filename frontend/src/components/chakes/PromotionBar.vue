<script setup lang="ts">
import { nextTick, ref } from 'vue'
import PieceSprite from './PieceSprite.vue'
import type { Color } from '@/services/types'

// A standing preference, not a modal picker: the game is real-time, so the
// chosen piece is sent with every move and applied whenever a pawn promotes.
const props = defineProps<{
  pieceNames: string[]
  selected: string
  playerColor: Color
}>()

const emit = defineEmits<{
  (e: 'select', name: string): void
}>()

const chips = ref<HTMLButtonElement[]>([])

const NEXT_KEYS = new Set(['ArrowRight', 'ArrowDown'])
const PREV_KEYS = new Set(['ArrowLeft', 'ArrowUp'])

async function onKeydown(e: KeyboardEvent, i: number) {
  const n = props.pieceNames.length
  let target: number
  if (NEXT_KEYS.has(e.key)) target = (i + 1) % n
  else if (PREV_KEYS.has(e.key)) target = (i - 1 + n) % n
  else if (e.key === 'Home') target = 0
  else if (e.key === 'End') target = n - 1
  else return
  e.preventDefault()
  const name = props.pieceNames[target]
  if (name === undefined) return
  emit('select', name)
  await nextTick()
  chips.value[target]?.focus()
}

// Roving tabindex: the checked chip (or the first, if none) is the tab stop.
function tabIndexFor(name: string, i: number): number {
  const anyChecked = props.pieceNames.includes(props.selected)
  return (anyChecked ? name === props.selected : i === 0) ? 0 : -1
}
</script>

<template>
  <div class="promotion-bar">
    <span
      id="promotion-label"
      class="promotion-label"
    >Promote to</span>
    <div
      class="promotion-chips"
      role="radiogroup"
      aria-labelledby="promotion-label"
    >
      <button
        v-for="(pieceName, i) in pieceNames"
        :key="pieceName"
        ref="chips"
        type="button"
        role="radio"
        class="chip"
        :aria-checked="selected === pieceName"
        :aria-label="pieceName"
        :title="`Promote pawns to ${pieceName}`"
        :tabindex="tabIndexFor(pieceName, i)"
        @click="emit('select', pieceName)"
        @keydown="onKeydown($event, i)"
      >
        <PieceSprite
          :name="pieceName"
          :color="playerColor"
        />
      </button>
    </div>
  </div>
</template>

<style scoped>
.promotion-bar {
  display: flex;
  align-items: center;
  gap: 8px;
}
.promotion-label {
  font-size: 13px;
  color: var(--text);
  white-space: nowrap;
}
.promotion-chips {
  display: flex;
  gap: 4px;
}
.chip {
  width: 34px;
  height: 34px;
  padding: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--surface);
}
.chip:hover {
  background: var(--surface-hover);
  border-color: var(--accent-border);
}
.chip[aria-checked='true'] {
  background: var(--accent-bg);
  border-color: var(--accent);
  box-shadow: inset 0 0 0 1px var(--accent);
}
.chip:not([aria-checked='true']) :deep(.piece-img) {
  opacity: 0.7;
}
</style>
