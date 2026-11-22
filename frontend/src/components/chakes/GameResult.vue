<script setup lang="ts">
import { computed } from 'vue'
import type { Color } from '@/services/types'
import type { SideFlags } from '@/chakes/types'
import { COLOR_LABELS, winReason } from '@/chakes/result'
import PieceSprite from './PieceSprite.vue'

const props = defineProps<{
  winner: Color
  /** The viewer's side, or null for spectators. */
  playerColor: Color | null
  isHost: boolean
  inCheck: SideFlags
  inAntiCheck: SideFlags
  /** A host action is in flight. */
  busy?: boolean
  error?: string
}>()

const emit = defineEmits<{
  (e: 'rematch'): void
  (e: 'changeSettings'): void
}>()

const outcome = computed<'won' | 'lost' | 'neutral'>(() => {
  if (!props.playerColor) return 'neutral'
  return props.playerColor === props.winner ? 'won' : 'lost'
})

const reason = computed(() => winReason(props.winner, props.inCheck, props.inAntiCheck))
const winnerWins = computed(() => `${COLOR_LABELS[props.winner]} wins`)

const headline = computed(() => {
  if (outcome.value === 'won') return 'You won!'
  if (outcome.value === 'lost') return 'You lost'
  return winnerWins.value
})

// Players: "White wins by checkmate". Spectators (headline already names the
// winner): "By checkmate", or just "Game over" when the reason is unknown.
const summary = computed(() => {
  if (outcome.value !== 'neutral') return reason.value ? `${winnerWins.value} ${reason.value}` : winnerWins.value
  return reason.value ? reason.value.charAt(0).toUpperCase() + reason.value.slice(1) : 'Game over'
})
</script>

<template>
  <section
    class="game-result"
    :class="outcome"
    aria-labelledby="game-result-title"
  >
    <div class="result-head">
      <span
        class="winner-piece"
        aria-hidden="true"
      >
        <PieceSprite
          name="King"
          :color="winner"
        />
      </span>
      <div class="result-text">
        <h2
          id="game-result-title"
          role="status"
        >
          {{ headline }}
        </h2>
        <p class="summary">
          {{ summary }}
        </p>
      </div>
    </div>

    <div
      v-if="isHost"
      class="actions"
    >
      <button
        type="button"
        class="primary"
        :disabled="busy"
        @click="emit('rematch')"
      >
        Rematch
      </button>
      <button
        type="button"
        :disabled="busy"
        @click="emit('changeSettings')"
      >
        Change settings
      </button>
    </div>
    <p
      v-else
      class="waiting"
    >
      Waiting for the host to start the next game&hellip;
    </p>
    <p
      v-if="error"
      class="error"
      role="alert"
    >
      {{ error }}
    </p>
  </section>
</template>

<style scoped>
.game-result {
  box-sizing: border-box;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid var(--border);
  border-top: 4px solid var(--accent);
  border-radius: var(--radius);
  background: var(--surface);
  box-shadow: var(--shadow);
  text-align: left;
}
.game-result.won {
  border-top-color: var(--status-win-border);
  background: var(--status-win-bg);
}
.game-result.lost {
  border-top-color: var(--border-strong);
}
.result-head {
  display: flex;
  align-items: center;
  gap: 12px;
}
.winner-piece {
  width: 44px;
  height: 44px;
  flex: none;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  /* A board square's colour keeps either side's piece legible in both themes. */
  background: var(--board-light);
  border: 1px solid var(--border-strong);
}
.winner-piece :deep(.piece-img) {
  width: 34px;
  height: 34px;
}
.result-text {
  min-width: 0;
}
h2 {
  margin: 0;
  font-size: 22px;
}
.won h2 {
  color: var(--status-win-fg);
}
.summary {
  font-size: 14px;
  color: var(--text);
}
.won .summary {
  color: var(--status-win-fg);
}
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.actions button {
  flex: 1 1 auto;
}
.waiting {
  font-size: 14px;
  line-height: 1.4;
  color: var(--text);
}
.error {
  font-size: 13px;
  color: var(--status-check-fg);
}
</style>
