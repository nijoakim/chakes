<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, shallowRef } from 'vue'
import { storeToRefs } from 'pinia'
import { useCatalogStore } from '@/stores/catalog'
import { useGameStore } from '@/stores/game'
import { useKeyboardShortcuts } from '@/composables/useKeyboardShortcuts'
import { listLobbies } from '@/services/api'
import type { GameSettings } from '@/chakes/types'
import ChakesBoard from '@/components/chakes/ChakesBoard.vue'
import GameResult from '@/components/chakes/GameResult.vue'
import PromotionBar from '@/components/chakes/PromotionBar.vue'
import StatusBanner from '@/components/chakes/StatusBanner.vue'
import GameSetup from '@/components/lobby/GameSetup.vue'
import LatencyToggle from '@/components/lobby/LatencyToggle.vue'
import OpponentStatus from '@/components/lobby/OpponentStatus.vue'
import RttBadge from '@/components/lobby/RttBadge.vue'
import WaitingRoom from '@/components/lobby/WaitingRoom.vue'

const props = defineProps<{ name: string }>()

const game = useGameStore()
const catalog = useCatalogStore()
const {
  board, cooldownGrid, maxCooldowns, stablePromotionNames, role, playerColor, viewColor, isSpectator, isHost, gameId, winner,
  selected, legalMoves, selectedPromotion, rtt, inCheck, inAntiCheck, rejectedSquares,
  latencyHidingEnabled,
} = storeToRefs(game)

const latencyHiding = computed({
  get: () => latencyHidingEnabled.value,
  set: (v: boolean) => game.setLatencyHiding(v),
})

const lastSettings = shallowRef<GameSettings | undefined>(undefined)
const lobbyUrl = computed(() => `${window.location.origin}/lobby/${encodeURIComponent(props.name)}`)

onMounted(async () => {
  game.connect(props.name)
  await catalog.load()
})

onUnmounted(() => {
  game.disconnect()
  clearTimeout(copiedTimer)
})

useKeyboardShortcuts({ Escape: () => game.deselect() })

async function onStartGame(payload: GameSettings) {
  lastSettings.value = payload
  await game.startNewGame(payload.gameType, payload.cooldowns, payload.upsideDown)
}

// --- End of game (host actions) ---
const hostBusy = ref(false)
const hostError = ref('')

/**
 * The settings of the game just played. Known locally if this page started it;
 * otherwise (e.g. the host reloaded) read back from the lobby list.
 */
async function currentSettings(): Promise<GameSettings | undefined> {
  if (lastSettings.value) return lastSettings.value
  const data = await listLobbies()
  const s = data.lobbies.find((l) => l.name === props.name)?.settings
  if (!s) return undefined
  lastSettings.value = {
    gameType: s.game_type_id,
    cooldowns: Object.fromEntries(s.pieces.map((p) => [p.name, p.cooldown])),
    upsideDown: s.upside_down,
  }
  return lastSettings.value
}

async function onRematch() {
  hostBusy.value = true
  hostError.value = ''
  try {
    const settings = await currentSettings()
    if (!settings) {
      hostError.value = 'Could not read the last game settings — choose them again.'
      game.resetGameState()
      return
    }
    await onStartGame(settings)
  } catch {
    hostError.value = 'Could not start a rematch. Please try again.'
  } finally {
    hostBusy.value = false
  }
}

// Local only: returns the host to the setup screen; the server game is not ended
// until the host starts a new one.
async function onChangeSettings() {
  hostBusy.value = true
  hostError.value = ''
  try {
    await currentSettings()
  } catch {
    // Fall back to the setup screen's defaults.
  } finally {
    hostBusy.value = false
  }
  game.resetGameState()
}

// --- Header ---
const ROLE_LABELS = { white: 'You are White', black: 'You are Black', spectator: 'Spectating' } as const
const roleLabel = computed(() => (role.value ? ROLE_LABELS[role.value] : ''))

const COPIED_FEEDBACK_MS = 1500
const copied = ref(false)
let copiedTimer: ReturnType<typeof setTimeout> | undefined

async function copyLobbyLink() {
  try {
    await navigator.clipboard.writeText(lobbyUrl.value)
  } catch {
    return // clipboard unavailable (e.g. insecure context or permission denied)
  }
  copied.value = true
  clearTimeout(copiedTimer)
  copiedTimer = setTimeout(() => { copied.value = false }, COPIED_FEEDBACK_MS)
}
</script>

<template>
  <div
    class="lobby-view"
    :class="{ 'in-game': gameId }"
  >
    <header class="lobby-bar">
      <div class="room-name">
        <RouterLink
          to="/"
          class="home-link"
          aria-label="Back to lobby list"
          title="Back to lobby list"
        >
          &larr;
        </RouterLink>
        <span class="lobby-label">Lobby <strong>{{ name }}</strong></span>
        <button
          class="copy-btn"
          :class="{ copied }"
          aria-label="Copy lobby link"
          title="Copy lobby link"
          @click="copyLobbyLink"
        >
          {{ copied ? 'Copied' : 'Copy link' }}
        </button>
        <span
          class="visually-hidden"
          aria-live="polite"
        >{{ copied ? 'Lobby link copied' : '' }}</span>
      </div>
      <span
        v-if="roleLabel"
        class="role-badge"
        :class="role"
      >
        {{ roleLabel }}
      </span>
      <div class="info-bar">
        <LatencyToggle v-model="latencyHiding" />
        <RttBadge :rtt="rtt" />
      </div>
    </header>

    <!-- Pre-game -->
    <main
      v-if="!gameId"
      class="pregame"
    >
      <template v-if="isHost">
        <OpponentStatus
          :lobby-name="name"
          :url="lobbyUrl"
        />
        <p
          v-if="hostError"
          class="host-error"
          role="alert"
        >
          {{ hostError }}
        </p>
        <GameSetup
          :initial-settings="lastSettings"
          @start="onStartGame"
        />
      </template>
      <WaitingRoom
        v-else-if="role"
        :role="role"
        :url="lobbyUrl"
      />
      <p
        v-else
        class="connecting"
        role="status"
      >
        Joining lobby&hellip;
      </p>
    </main>

    <!-- In game / game over. On wide screens these three sit in one grid row:
         an empty gutter, the board (centred on the page), and the side panel. -->
    <div
      v-if="gameId"
      class="gutter"
      aria-hidden="true"
    />
    <ChakesBoard
      v-if="gameId"
      :board="board"
      :cooldowns="cooldownGrid"
      :max-cooldowns="maxCooldowns"
      :viewer="viewColor"
      :selected="selected"
      :legal-moves="legalMoves"
      :rejected-squares="rejectedSquares"
      @square-click="game.handleSquareClick"
      @square-right-click="game.handleSquareRightClick"
    />
    <aside
      v-if="gameId"
      class="side-panel"
    >
      <GameResult
        v-if="winner"
        :winner="winner"
        :player-color="playerColor"
        :is-host="isHost"
        :in-check="inCheck"
        :in-anti-check="inAntiCheck"
        :busy="hostBusy"
        :error="hostError"
        @rematch="onRematch"
        @change-settings="onChangeSettings"
      />
      <template v-else>
        <!-- Spectators get no check warnings (they have no side). -->
        <StatusBanner
          v-if="!isSpectator"
          :in-game="true"
          :player-color="viewColor"
          :in-check="inCheck"
          :in-anti-check="inAntiCheck"
        />
        <PromotionBar
          v-if="playerColor && stablePromotionNames.length"
          :piece-names="stablePromotionNames"
          :selected="selectedPromotion"
          :player-color="playerColor"
          @select="(n: string) => (selectedPromotion = n)"
        />
        <p
          v-if="isSpectator"
          class="spectator-note"
        >
          Watching live from White's side.
        </p>
      </template>
    </aside>
  </div>
</template>

<style scoped>
.lobby-view {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  padding: 8px 16px 16px;
  gap: 12px;
}

/* ---- Header bar -------------------------------------------------------- */
.lobby-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 8px;
  min-height: 32px;
  align-self: stretch;
}
.room-name {
  font-size: 14px;
  color: var(--text);
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 8px;
}
.lobby-label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.lobby-label strong {
  color: var(--text-h);
  font-weight: 600;
}
.home-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius);
  color: var(--text);
  text-decoration: none;
  border: 1px solid transparent;
}
.home-link:hover {
  color: var(--text-h);
  border-color: var(--border);
  background: var(--surface-hover);
}
.home-link:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
.copy-btn {
  min-width: 6.5em;
  padding: 2px 8px;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.4;
  border-radius: 4px;
  background: none;
  border-color: var(--border);
  color: var(--text);
}
.copy-btn:hover,
.copy-btn.copied {
  border-color: var(--accent-border);
  color: var(--text-h);
}
.role-badge {
  padding: 2px 8px;
  font-size: 12px;
  line-height: 1.4;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--code-bg);
  color: var(--text-h);
}
.role-badge.spectator {
  color: var(--text);
  font-style: italic;
}
.info-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: auto;
}
.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}

/* ---- Pre-game ---------------------------------------------------------- */
.pregame {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}
.pregame > :deep(.waiting-room) {
  margin-top: max(16px, 10vh);
}
.connecting {
  margin-top: 20vh;
  color: var(--text);
}
.host-error {
  font-size: 14px;
  color: var(--status-check-fg);
}

/* ---- In game ----------------------------------------------------------- */
/* Narrow: board on top, controls in a column underneath. */
.lobby-view.in-game {
  align-items: center;
}
.gutter {
  display: none;
}
.side-panel {
  width: min(400px, 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}
.side-panel > :deep(.status-banner) {
  align-self: stretch;
}
.spectator-note {
  font-size: 14px;
  color: var(--text);
}

/* Wide: board centred on the page, controls in the right-hand gutter. */
@media (min-width: 960px) {
  .lobby-view.in-game {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    grid-template-rows: auto 1fr;
    align-items: center;
    column-gap: 24px;
  }
  .lobby-view.in-game > .lobby-bar {
    grid-column: 1 / -1;
    align-self: start;
  }
  .gutter {
    display: block;
  }
  .side-panel {
    justify-self: start;
    width: min(280px, 100%);
    align-items: stretch;
  }
  .spectator-note {
    text-align: left;
  }
}
</style>
