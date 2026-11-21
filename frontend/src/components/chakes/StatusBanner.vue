<script setup lang="ts">
import { computed } from 'vue'
import type { Color } from '@/services/types'
import type { SideFlags } from '@/chakes/types'

const props = defineProps<{
  /** Whether a game is running (in-check warnings are only shown then). */
  inGame: boolean
  playerColor: Color
  winner: Color | null
  inCheck: SideFlags
  inAntiCheck: SideFlags
}>()

type StatusKind = 'check' | 'anti-check' | 'both' | 'mate' | 'anti-mate' | 'win' | 'empty'

const status = computed<{ text: string; kind: StatusKind }>(() => {
  if (props.winner) {
    const loser = props.winner === 'white' ? 'black' : 'white'
    const sym = props.winner === 'white' ? '♔ White' : '♚ Black'
    const c = props.inCheck[loser]
    const a = props.inAntiCheck[loser]
    if (c && a) return { text: `Checkmate & Anti-checkmate — ${sym} wins`, kind: 'mate' }
    if (c)      return { text: `Checkmate — ${sym} wins`, kind: 'mate' }
    if (a)      return { text: `Anti-checkmate — ${sym} wins`, kind: 'anti-mate' }
    return { text: `${sym} won!`, kind: 'win' }
  }
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
  <div
    class="status-banner"
    :class="status.kind"
  >
    <span v-if="status.kind !== 'empty'">{{ status.text }}</span>
    <span v-else>&nbsp;</span>
  </div>
</template>

<style scoped>
.status-banner {
  margin-top: 12px;
  padding: 12px 24px;
  font-size: 24px;
  font-weight: 700;
  text-align: center;
  border-radius: 6px;
  box-sizing: border-box;
  min-height: 56px;
  min-width: 360px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.status-banner.empty      { visibility: hidden; }
.status-banner.check      { background: #fde2e2; color: #7a1f1f; }
.status-banner.anti-check { background: #ffe7c2; color: #6b3a07; }
.status-banner.both       { background: #fde2e2; color: #5a0b0b; }
.status-banner.mate       { background: #f6f669; color: #3d3a00; }
.status-banner.anti-mate  { background: #f6f669; color: #3d3a00; }
.status-banner.win        { background: #f6f669; color: #3d3a00; }
</style>
