<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, shallowRef } from 'vue'
import { storeToRefs } from 'pinia'
import { useCatalogStore } from '@/stores/catalog'
import { useGameStore } from '@/stores/game'
import { useKeyboardShortcuts } from '@/composables/useKeyboardShortcuts'
import type { GameSettings } from '@/chakes/types'
import ChakesBoard from '@/components/chakes/ChakesBoard.vue'
import PromotionBar from '@/components/chakes/PromotionBar.vue'
import StatusBanner from '@/components/chakes/StatusBanner.vue'
import GameSetup from '@/components/lobby/GameSetup.vue'
import LatencyToggle from '@/components/lobby/LatencyToggle.vue'
import RttBadge from '@/components/lobby/RttBadge.vue'

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

const boardCols = computed(() => board.value[0]?.length ?? 8)
const lastSettings = shallowRef<GameSettings | undefined>(undefined)

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

// Local only: returns the host to the setup screen; the server game is not ended
// until the host starts a new one.
function onNewGame() {
  game.resetGameState()
}

const ROLE_LABELS = { white: 'You are White', black: 'You are Black', spectator: 'Spectating' } as const
const roleLabel = computed(() => (role.value ? ROLE_LABELS[role.value] : ''))

const COPIED_FEEDBACK_MS = 1500
const copied = ref(false)
let copiedTimer: ReturnType<typeof setTimeout> | undefined

async function copyLobbyLink() {
  try {
    await navigator.clipboard.writeText(window.location.href)
  } catch {
    return // clipboard unavailable (e.g. insecure context or permission denied)
  }
  copied.value = true
  clearTimeout(copiedTimer)
  copiedTimer = setTimeout(() => { copied.value = false }, COPIED_FEEDBACK_MS)
}
</script>

<template>
  <div class="info-bar">
    <RttBadge :rtt="rtt" />
    <LatencyToggle v-model="latencyHiding" />
  </div>
  <section id="center">
    <div class="room-name">
      Lobby: {{ name }}
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
        v-if="roleLabel"
        class="role-badge"
        :class="role"
      >
        {{ roleLabel }}
      </span>
      <span
        class="visually-hidden"
        aria-live="polite"
      >{{ copied ? 'Lobby link copied' : '' }}</span>
    </div>

    <GameSetup
      v-if="!gameId && isHost"
      :initial-settings="lastSettings"
      @start="onStartGame"
    />
    <p
      v-if="!gameId && role && !isHost"
      class="waiting-text"
    >
      Waiting for host to start the game…
    </p>

    <PromotionBar
      v-if="gameId && playerColor && stablePromotionNames.length"
      :piece-names="stablePromotionNames"
      :selected="selectedPromotion"
      :player-color="playerColor"
      :cols="boardCols"
      @select="(n: string) => (selectedPromotion = n)"
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

    <!-- Spectators get no check warnings (they have no side), only the result. -->
    <StatusBanner
      :in-game="gameId !== null && !isSpectator"
      :player-color="viewColor"
      :winner="winner"
      :in-check="inCheck"
      :in-anti-check="inAntiCheck"
    />
    <div
      class="new-game-slot"
      :class="{ hidden: !isHost || !gameId }"
    >
      <button
        class="new-game"
        @click="onNewGame"
      >
        New game
      </button>
    </div>
  </section>
</template>

<style scoped>
.room-name {
  margin-bottom: 6px;
  font-size: 13px;
  color: var(--text);
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}
.copy-btn {
  min-width: 6.5em;
  padding: 0 6px;
  font-size: 12px;
  line-height: 1.4;
  cursor: pointer;
  background: none;
  border: 1px solid var(--border);
  border-radius: 3px;
  color: var(--text);
}
.copy-btn:hover,
.copy-btn.copied {
  border-color: var(--text);
  color: var(--text-h);
}
.role-badge {
  padding: 0 6px;
  font-size: 12px;
  line-height: 1.4;
  border: 1px solid var(--border);
  border-radius: 3px;
  background: var(--code-bg);
  color: var(--text-h);
}
.role-badge.spectator {
  color: var(--text);
  font-style: italic;
}
.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}
.new-game-slot {
  margin-top: 12px;
}
.new-game-slot.hidden {
  visibility: hidden;
}
.waiting-text {
  color: var(--text);
  font-size: 15px;
}
.info-bar {
  width: 100%;
  height: 30px;
  display: inline-flex;
  justify-content: end;
  flex-direction: row-reverse;
  align-items: center;
  gap: 10px;
}
</style>
