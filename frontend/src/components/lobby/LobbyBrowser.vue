<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { LobbyNameTakenError, useLobbyStore } from '@/stores/lobby'
import { ApiError } from '@/services/api'
import { useVisibilityPolling } from '@/composables/useVisibilityPolling'
import type { LobbySummary } from '@/services/types'
import {
  ACTION_LABELS, MAX_LOBBY_NAME_LENGTH, MAX_PLAYERS, STATE_LABELS,
  lobbyAction, settingsFullDescription, settingsSummaryParts, validateLobbyName,
} from './lobbySummary'

const POLL_INTERVAL_MS = 4000

const router = useRouter()
const lobby = useLobbyStore()

// --- Create -----------------------------------------------------------------

const nameInput = ref('')
const creating = ref(false)
const createError = ref<string | null>(null)
/** Set when the error is a name clash, so we can offer to join that lobby. */
const takenName = ref<string | null>(null)

function clearCreateError() {
  createError.value = null
  takenName.value = null
}

async function onCreate() {
  if (creating.value) return
  clearCreateError()
  const name = nameInput.value.trim()
  nameInput.value = name
  const invalid = validateLobbyName(name)
  if (invalid) {
    createError.value = invalid
    return
  }
  creating.value = true
  try {
    const created = await lobby.create(name)
    await router.push({ name: 'lobby', params: { name: created } })
  } catch (e) {
    if (e instanceof LobbyNameTakenError) {
      createError.value = `A lobby named “${e.lobbyName}” already exists.`
      takenName.value = e.lobbyName
    } else if (e instanceof ApiError && e.status < 500) {
      createError.value = `Couldn't create the lobby (${e.status}${e.detail ? `: ${e.detail}` : ''}).`
    } else {
      createError.value = "Couldn't reach the server. Please try again."
    }
  } finally {
    creating.value = false
  }
}

// --- Browse -----------------------------------------------------------------

const { runNow } = useVisibilityPolling(() => lobby.refreshList(), POLL_INTERVAL_MS)

const manualRefreshing = ref(false)
async function onRefresh() {
  manualRefreshing.value = true
  try {
    await runNow()
  } finally {
    manualRefreshing.value = false
  }
}

const rows = computed(() => lobby.openLobbies.map((row: LobbySummary) => {
  const action = lobbyAction(row)
  return {
    row,
    action,
    actionLabel: ACTION_LABELS[action],
    stateLabel: STATE_LABELS[row.state],
    summary: row.settings ? settingsSummaryParts(row.settings) : null,
    fullDescription: row.settings ? settingsFullDescription(row.settings) : 'No game started yet',
  }
}))
</script>

<template>
  <div class="browser">
    <!-- Create section -->
    <section
      class="create-section"
      aria-labelledby="create-heading"
    >
      <h2 id="create-heading">
        New lobby
      </h2>
      <form
        class="create-row"
        novalidate
        @submit.prevent="onCreate"
      >
        <label
          for="lobby-name-input"
          class="visually-hidden"
        >Lobby name</label>
        <input
          id="lobby-name-input"
          v-model="nameInput"
          placeholder="Leave empty for a random name"
          autocomplete="off"
          :maxlength="MAX_LOBBY_NAME_LENGTH + 10"
          :aria-invalid="createError ? 'true' : undefined"
          :aria-describedby="createError ? 'create-error' : undefined"
          @input="clearCreateError"
        >
        <button
          type="submit"
          class="create-btn"
          :disabled="creating"
          :aria-busy="creating ? 'true' : undefined"
        >
          {{ creating ? 'Creating…' : 'Create' }}
        </button>
      </form>
      <p
        v-if="createError"
        id="create-error"
        class="inline-error"
        role="alert"
      >
        {{ createError }}
        <RouterLink
          v-if="takenName"
          :to="{ name: 'lobby', params: { name: takenName } }"
        >
          Go to that lobby
        </RouterLink>
      </p>
    </section>

    <!-- Browse section -->
    <section
      class="browse-section"
      aria-labelledby="browse-heading"
    >
      <div class="browse-header">
        <h2 id="browse-heading">
          Open lobbies
        </h2>
        <button
          type="button"
          class="refresh-btn"
          :disabled="manualRefreshing"
          title="Lobbies refresh automatically"
          @click="onRefresh"
        >
          {{ manualRefreshing ? 'Refreshing…' : 'Refresh' }}
        </button>
      </div>

      <p
        v-if="lobby.listStatus === 'error'"
        class="conn-notice"
        role="status"
      >
        <span
          class="conn-dot"
          aria-hidden="true"
        />
        Couldn't reach the server — retrying…
      </p>

      <ul
        v-if="rows.length > 0"
        class="lobby-list"
        :class="{ stale: lobby.listStatus === 'error' }"
      >
        <li
          v-for="r in rows"
          :key="r.row.name"
        >
          <RouterLink
            class="lobby-row"
            :class="`action-${r.action}`"
            :to="{ name: 'lobby', params: { name: r.row.name } }"
          >
            <div class="row-main">
              <div class="row-primary">
                <span class="lobby-name">{{ r.row.name }}</span>
                <span
                  class="state-badge"
                  :class="`state-${r.row.state}`"
                >{{ r.stateLabel }}</span>
                <span class="player-count">
                  {{ r.row.players }}/{{ MAX_PLAYERS }} players<template v-if="r.row.spectators > 0">, {{ r.row.spectators }} watching</template>
                </span>
                <span
                  v-if="r.row.server_name !== lobby.serverName"
                  class="row-server"
                >@ {{ r.row.server_name }}</span>
              </div>
              <div
                class="row-secondary"
                :title="r.fullDescription"
              >
                <template v-if="r.summary">
                  <template
                    v-for="(part, i) in r.summary"
                    :key="i"
                  >
                    <span
                      v-if="i > 0"
                      class="sep"
                      aria-hidden="true"
                    > · </span><span class="summary-part">{{ part }}</span>
                  </template>
                </template>
                <span
                  v-else
                  class="muted"
                >No game started yet</span>
              </div>
            </div>
            <span class="row-action">{{ r.actionLabel }}<span aria-hidden="true"> →</span></span>
          </RouterLink>
        </li>
      </ul>

      <p
        v-else-if="lobby.hasLoaded"
        class="empty-state"
      >
        No open lobbies on this server. Create one above to get started.
      </p>
      <p
        v-else-if="lobby.listStatus === 'loading'"
        class="empty-state"
      >
        Loading lobbies…
      </p>

      <p
        v-if="lobby.serverName"
        class="server-tag"
      >
        Server: {{ lobby.serverName }}
      </p>
    </section>
  </div>
</template>

<style scoped>
.browser {
  display: flex;
  flex-direction: column;
  gap: 32px;
  width: 100%;
  max-width: 640px;
  box-sizing: border-box;
}

h2 {
  margin: 0 0 12px;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}

/* Create section */
.create-row {
  display: flex;
  gap: 8px;
}

.create-row input {
  flex: 1;
  min-width: 0;
  padding: 6px 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg);
  color: var(--text-h);
  font: inherit;
}

.create-row input:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 1px;
}

.create-row input[aria-invalid='true'] {
  border-color: #dc2626;
}

button {
  padding: 6px 14px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg);
  color: var(--text-h);
  font: inherit;
  cursor: pointer;
  transition: box-shadow 0.2s;
}

button:hover:not(:disabled) {
  box-shadow: var(--shadow);
}

button:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

button:disabled {
  cursor: default;
  opacity: 0.6;
}

.create-btn {
  min-width: 6.5em;
}

.inline-error {
  margin-top: 8px;
  font-size: 14px;
  color: #dc2626;
  text-align: left;
}

.inline-error a {
  color: var(--accent);
  margin-left: 4px;
}

/* Browse section */
.browse-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}

/* Secondary: the list refreshes on its own. */
.refresh-btn {
  font-size: 13px;
  padding: 2px 8px;
  border-color: transparent;
  background: transparent;
  color: var(--text);
}

.refresh-btn:hover:not(:disabled) {
  box-shadow: none;
  color: var(--text-h);
  text-decoration: underline;
}

.conn-notice {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 10px;
  padding: 6px 10px;
  border: 1px solid rgba(249, 115, 22, 0.4);
  border-radius: 6px;
  background: rgba(249, 115, 22, 0.08);
  font-size: 14px;
  color: var(--text-h);
  text-align: left;
}

.conn-dot {
  flex: none;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ea580c;
  animation: pulse 1.4s ease-in-out infinite;
}

@keyframes pulse {
  50% { opacity: 0.3; }
}

@media (prefers-reduced-motion: reduce) {
  .conn-dot { animation: none; }
}

.lobby-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  transition: opacity 0.2s;
}

.lobby-list.stale {
  opacity: 0.6;
}

.lobby-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  color: inherit;
  text-decoration: none;
  text-align: left;
  transition: box-shadow 0.15s, border-color 0.15s;
}

.lobby-row:hover {
  box-shadow: var(--shadow);
}

.lobby-row:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
  border-color: var(--accent);
}

.row-main {
  flex: 1;
  min-width: 0;
}

.row-primary {
  display: flex;
  align-items: baseline;
  gap: 4px 10px;
  flex-wrap: wrap;
}

.lobby-name {
  font-weight: 500;
  color: var(--text-h);
  overflow-wrap: anywhere;
}

.state-badge {
  font-size: 12px;
  padding: 1px 7px;
  border-radius: 999px;
  font-weight: 500;
  white-space: nowrap;
}

.state-waiting {
  background: rgba(34, 197, 94, 0.15);
  color: #15803d;
}

.state-in_progress {
  background: rgba(249, 115, 22, 0.15);
  color: #c2410c;
}

.state-ended {
  background: var(--code-bg);
  color: var(--text);
}

@media (prefers-color-scheme: dark) {
  .state-waiting { color: #4ade80; }
  .state-in_progress { color: #fb923c; }
  .inline-error { color: #f87171; }
  .create-row input[aria-invalid='true'] { border-color: #f87171; }
  .conn-dot { background: #fb923c; }
}

.player-count {
  font-size: 14px;
  color: var(--text);
  white-space: nowrap;
}

.row-server {
  font-size: 12px;
  color: var(--text);
  white-space: nowrap;
}

.row-secondary {
  margin-top: 3px;
  font-size: 13px;
  color: var(--text);
}

.summary-part {
  white-space: nowrap;
}

.sep {
  color: var(--text);
  opacity: 0.6;
}

.muted {
  font-style: italic;
}

.row-action {
  flex: none;
  padding: 4px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-h);
  white-space: nowrap;
}

.action-join .row-action {
  border-color: var(--accent);
  color: var(--accent);
}

.lobby-row:hover .row-action,
.lobby-row:focus-visible .row-action {
  background: var(--code-bg);
}

.empty-state {
  color: var(--text);
  font-size: 15px;
  text-align: center;
  padding: 24px 0;
}

.server-tag {
  margin-top: 10px;
  font-size: 12px;
  color: var(--text);
  text-align: right;
}
</style>
