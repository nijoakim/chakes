<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useLobbyStore } from '../../stores/lobby'
import type { LobbySummary } from '../../services/api'

const router = useRouter()
const lobby = useLobbyStore()

const nameInput = ref('')

async function onCreate() {
  const name = await lobby.create(nameInput.value.trim() || undefined)
  router.push({ name: 'lobby', params: { name } })
}

function onJoin(row: LobbySummary) {
  router.push({ name: 'lobby', params: { name: row.name } })
}

lobby.refreshList()
</script>

<template>
  <div class="browser">
    <!-- Create section -->
    <section class="create-section">
      <h2>New lobby</h2>
      <div class="create-row">
        <input
          v-model="nameInput"
          placeholder="Leave empty for a random name"
          @keyup.enter="onCreate"
        >
        <button @click="onCreate">
          Create
        </button>
      </div>
    </section>

    <!-- Browse section -->
    <section class="browse-section">
      <div class="browse-header">
        <h2>Open lobbies</h2>
        <button
          class="refresh-btn"
          @click="lobby.refreshList()"
        >
          Refresh
        </button>
      </div>

      <ul
        v-if="lobby.openLobbies.length > 0"
        class="lobby-list"
      >
        <li
          v-for="row in lobby.openLobbies"
          :key="row.name"
          class="lobby-row"
          @click="onJoin(row)"
        >
          <div class="row-primary">
            <span class="lobby-name">{{ row.name }}</span>
            <span
              class="state-badge"
              :class="`state-${row.state}`"
            >{{ row.state === 'in_progress' ? 'In progress' : row.state === 'waiting' ? 'Waiting' : 'Ended' }}</span>
            <span class="player-count">{{ row.players }} players, {{ row.spectators }} watching</span>
            <span class="server-tag">@ {{ row.server_name }}</span>
          </div>
          <div class="row-secondary">
            <template v-if="row.settings">
              {{ row.settings.game_type_label }}
              <template
                v-for="p in row.settings.pieces"
                :key="p.name"
              >
                <span class="sep"> · </span>{{ p.name }} {{ p.cooldown }}s
              </template>
              <template v-if="row.settings.upside_down">
                <span class="sep"> · </span>Upside-down
              </template>
            </template>
            <template v-else>
              <span class="muted">(no game started yet)</span>
            </template>
          </div>
        </li>
      </ul>

      <p
        v-else
        class="empty-state"
      >
        No open lobbies on this server. Create one above to get started.
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
}

h2 {
  margin: 0 0 12px;
}

/* Create section */
.create-row {
  display: flex;
  gap: 8px;
}

.create-row input {
  flex: 1;
  padding: 6px 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg);
  color: var(--text-h);
  font: inherit;
}

.create-row input:focus {
  outline: 2px solid var(--accent);
  outline-offset: 1px;
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

button:hover {
  box-shadow: var(--shadow);
}

/* Browse section */
.browse-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}

.refresh-btn {
  font-size: 14px;
  padding: 4px 10px;
}

.lobby-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.lobby-row {
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  cursor: pointer;
  transition: box-shadow 0.15s;
  text-align: left;
}

.lobby-row:hover {
  box-shadow: var(--shadow);
}

.row-primary {
  display: flex;
  align-items: baseline;
  gap: 10px;
  flex-wrap: wrap;
}

.lobby-name {
  font-weight: 500;
  color: var(--text-h);
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
  color: #16a34a;
}

.state-in_progress {
  background: rgba(249, 115, 22, 0.15);
  color: #ea580c;
}

.state-ended {
  background: var(--code-bg);
  color: var(--text);
}

@media (prefers-color-scheme: dark) {
  .state-waiting { color: #4ade80; }
  .state-in_progress { color: #fb923c; }
}

.player-count {
  font-size: 14px;
  color: var(--text);
}

.server-tag {
  margin-left: auto;
  font-size: 12px;
  color: var(--text);
  white-space: nowrap;
}

.row-secondary {
  margin-top: 3px;
  font-size: 13px;
  color: var(--text);
}

.sep {
  color: var(--border);
}

.muted {
  color: var(--text);
  font-style: italic;
}

.empty-state {
  color: var(--text);
  font-size: 15px;
  text-align: center;
  padding: 24px 0;
}
</style>
