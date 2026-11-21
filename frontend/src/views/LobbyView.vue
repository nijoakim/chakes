<script setup lang="ts">
import { computed, onMounted, onUnmounted, shallowRef } from 'vue'
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
  board, cooldownGrid, maxCooldowns, stablePromotionNames, playerColor, isHost, gameId, winner,
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

function copyLobbyName() {
  navigator.clipboard.writeText(props.name)
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
        title="Copy lobby name"
        @click="copyLobbyName"
      >
        ⎘
      </button>
    </div>

    <GameSetup
      v-if="!gameId && isHost"
      :initial-settings="lastSettings"
      @start="onStartGame"
    />
    <p
      v-if="!gameId && !isHost"
      class="waiting-text"
    >
      Waiting for host to start the game…
    </p>

    <PromotionBar
      v-if="gameId && stablePromotionNames.length"
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
      :player-color="playerColor"
      :selected="selected"
      :legal-moves="legalMoves"
      :rejected-squares="rejectedSquares"
      @square-click="game.handleSquareClick"
      @square-right-click="game.handleSquareRightClick"
    />

    <StatusBanner
      :in-game="gameId !== null"
      :player-color="playerColor"
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
  padding: 0 5px;
  font-size: 12px;
  line-height: 1.4;
  cursor: pointer;
  background: none;
  border: 1px solid var(--border);
  border-radius: 3px;
  color: var(--text);
}
.copy-btn:hover {
  border-color: var(--text);
  color: var(--text-h);
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
