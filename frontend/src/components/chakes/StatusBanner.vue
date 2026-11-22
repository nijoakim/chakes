<script setup lang="ts">
import { computed } from 'vue'
import type { Color } from '@/services/types'
import type { SideFlags } from '@/chakes/types'

// In-game check warnings for a player. The final result is shown by GameResult.
const props = defineProps<{
  /** Whether a game is running and undecided (warnings are only shown then). */
  inGame: boolean
  playerColor: Color
  inCheck: SideFlags
  inAntiCheck: SideFlags
}>()

type StatusKind = 'check' | 'anti-check' | 'both' | 'empty'

const status = computed<{ text: string; kind: StatusKind }>(() => {
  if (props.inGame) {
    const c = props.inCheck[props.playerColor]
    const a = props.inAntiCheck[props.playerColor]
    if (c && a) return { text: 'Check & Anti-check!', kind: 'both' }
    if (c)      return { text: 'Check!', kind: 'check' }
    if (a)      return { text: 'Anti-check!', kind: 'anti-check' }
  }
  return { text: '', kind: 'empty' }
})
</script>

<template>
  <!-- The slot keeps its height when empty so the controls below never jump. -->
  <div
    class="status-banner"
    :class="status.kind"
    role="status"
  >
    {{ status.text }}
  </div>
</template>

<style scoped>
.status-banner {
  padding: 6px 14px;
  font-size: 17px;
  font-weight: 700;
  line-height: 1.3;
  text-align: center;
  border: 1px solid transparent;
  border-radius: var(--radius);
  box-sizing: border-box;
  min-height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.status-banner.empty { visibility: hidden; }
.status-banner.check,
.status-banner.both {
  background: var(--status-check-bg);
  border-color: var(--status-check-border);
  color: var(--status-check-fg);
}
.status-banner.anti-check {
  background: var(--status-anti-bg);
  border-color: var(--status-anti-border);
  color: var(--status-anti-fg);
}
</style>
