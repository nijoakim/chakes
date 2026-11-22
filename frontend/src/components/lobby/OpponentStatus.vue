<script setup lang="ts">
import { computed, ref } from 'vue'
import { listLobbies } from '@/services/api'
import type { LobbySummary } from '@/services/types'
import { useVisibilityPolling } from '@/composables/useVisibilityPolling'
import ShareLink from './ShareLink.vue'

// The lobby socket does not announce joins, so the host's setup screen polls
// the REST lobby list (lightly, only while this component is mounted).
const props = defineProps<{ lobbyName: string; url: string }>()

const POLL_INTERVAL_MS = 3000
const REQUEST_TIMEOUT_MS = 5000

const summary = ref<LobbySummary | null>(null)
const loaded = ref(false)

useVisibilityPolling(async () => {
  try {
    const data = await listLobbies({ signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS) })
    summary.value = data.lobbies.find((l) => l.name === props.lobbyName) ?? null
  } catch {
    summary.value = null
  } finally {
    loaded.value = true
  }
}, POLL_INTERVAL_MS)

// `players` counts seats assigned (host included), not live connections.
const opponentJoined = computed(() => (summary.value?.players ?? 0) >= 2)
const spectators = computed(() => summary.value?.spectators ?? 0)
</script>

<template>
  <div
    class="opponent-status"
    :class="{ joined: opponentJoined }"
  >
    <p
      class="status-line"
      role="status"
    >
      <span
        class="dot"
        aria-hidden="true"
      />
      <template v-if="opponentJoined">
        Opponent has joined &mdash; choose settings and start when ready.
      </template>
      <template v-else-if="loaded">
        Waiting for an opponent to join. Share this link:
      </template>
      <template v-else>
        Checking who is here&hellip;
      </template>
      <span
        v-if="spectators > 0"
        class="spectators"
      >{{ spectators }} watching</span>
    </p>
    <ShareLink
      v-if="!opponentJoined"
      :url="url"
    />
  </div>
</template>

<style scoped>
.opponent-status {
  width: min(560px, 100%);
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface);
  text-align: left;
}
.opponent-status.joined {
  border-color: var(--accent-border);
  background: var(--accent-bg);
}
.status-line {
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-size: 15px;
  color: var(--text-h);
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex: none;
  align-self: center;
  background: var(--border-strong);
  animation: pulse 1.4s ease-in-out infinite alternate;
}
.joined .dot {
  background: var(--accent);
  animation: none;
}
.spectators {
  margin-left: auto;
  white-space: nowrap;
  font-size: 13px;
  color: var(--text);
}
@keyframes pulse {
  from { opacity: 0.35; }
  to   { opacity: 1; }
}
@media (prefers-reduced-motion: reduce) {
  .dot { animation: none; }
}
</style>
