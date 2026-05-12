<script setup lang="ts">
import { computed, onMounted, onUnmounted, shallowRef } from 'vue'
import { storeToRefs } from 'pinia'
import { useCatalogStore } from '../stores/catalog'
import { useGameStore } from '../stores/game'
import { useLobbyStore } from '../stores/lobby'
import { useKeyboardShortcuts } from '../composables/useKeyboardShortcuts'
import ChakesBoard from '../components/chess/ChakesBoard.vue'
import PromotionBar from '../components/chess/PromotionBar.vue'
import GameSetup from '../components/lobby/GameSetup.vue'

type Settings = { gameType: string; cooldowns: Record<string, number>; upsideDown: boolean; latencyHiding: boolean }

const props = defineProps<{ name: string }>()

const game = useGameStore()
const lobby = useLobbyStore()
const catalog = useCatalogStore()
const {
  board, cooldowns, maxCooldowns, stablePromotionNames, playerColor, gameId, winner,
  selected, legalMoves, selectedPromotion, rtt, inCheck, inAntiCheck, rejectedSquares,
} = storeToRefs(game)

type StatusKind = 'check' | 'anti-check' | 'both' | 'mate' | 'anti-mate' | 'win' | 'empty'
const statusMessage = computed<{ text: string; kind: StatusKind }>(() => {
  if (winner.value) {
    const loser = winner.value === 'white' ? 'black' : 'white'
    const sym = winner.value === 'white' ? '♔ White' : '♚ Black'
    const c = inCheck.value[loser]
    const a = inAntiCheck.value[loser]
    if (c && a) return { text: `Checkmate & Anti-checkmate — ${sym} wins`, kind: 'mate' }
    if (c)      return { text: `Checkmate — ${sym} wins`, kind: 'mate' }
    if (a)      return { text: `Anti-checkmate — ${sym} wins`, kind: 'anti-mate' }
    return { text: `${sym} won!`, kind: 'win' }
  }
  if (gameId.value) {
    const color = playerColor.value as 'white' | 'black'
    const c = inCheck.value[color]
    const a = inAntiCheck.value[color]
    if (c && a) return { text: 'Check & Anti-check!', kind: 'both' }
    if (c)      return { text: 'Check!', kind: 'check' }
    if (a)      return { text: 'Anti-check!', kind: 'anti-check' }
  }
  return { text: '', kind: 'empty' }
})

const rttColor = computed(() => {
  if (rtt.value === null) return '#888'
  if (rtt.value < 150) return '#4caf50'
  if (rtt.value < 500) return '#ffc107'
  return '#f44336'
})
const rttLabel = computed(() =>
  rtt.value === null ? '— ms' : `${Math.round(rtt.value)} ms`,
)

const boardCols = computed(() => board.value[0]?.length ?? 8)
const lastSettings = shallowRef<Settings | undefined>(undefined)

onMounted(async () => {
  lobby.setCurrent(props.name)
  game.connect(props.name)
  await catalog.load()
})

onUnmounted(() => {
  game.disconnect()
  lobby.setCurrent(null)
})

useKeyboardShortcuts({ Escape: () => game.deselect() })

async function onStartGame(payload: Settings) {
  lastSettings.value = payload
  game.setLatencyHiding(payload.latencyHiding)
  await game.startNewGame(payload.gameType, payload.cooldowns, payload.upsideDown)
}

function onNewGame() {
  game.resetGameState()
}

function copyLobbyName() {
  navigator.clipboard.writeText(props.name)
}
</script>

<template>
  <div
    class="rtt-badge"
    :style="{ color: rttColor }"
  >
    {{ rttLabel }}
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
      v-if="!gameId && playerColor === 'white'"
      :initial-settings="lastSettings"
      @start="onStartGame"
    />
    <p
      v-if="!gameId && playerColor !== 'white'"
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
      @select="(n) => (game.selectedPromotion = n)"
    />
    <ChakesBoard
      v-if="gameId"
      :board="board"
      :cooldowns="cooldowns"
      :max-cooldowns="maxCooldowns"
      :player-color="playerColor"
      :selected="selected"
      :legal-moves="legalMoves"
      :rejected-squares="rejectedSquares"
      @square-click="(r, c) => game.handleSquareClick(r, c)"
      @square-right-click="(r, c) => game.handleSquareRightClick(r, c)"
    />

    <div
      class="status-banner"
      :class="statusMessage.kind"
    >
      <span v-if="statusMessage.kind !== 'empty'">{{ statusMessage.text }}</span>
      <span v-else>&nbsp;</span>
    </div>
    <div
      class="new-game-slot"
      :class="{ hidden: playerColor !== 'white' || !gameId }"
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
  color: #666;
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
  border: 1px solid #ccc;
  border-radius: 3px;
  color: #888;
}
.copy-btn:hover {
  border-color: #888;
  color: #333;
}
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
.new-game-slot {
  margin-top: 12px;
}
.new-game-slot.hidden {
  visibility: hidden;
}
.waiting-text {
  color: #888;
  font-size: 15px;
}
.rtt-badge {
  position: fixed;
  top: 8px;
  right: 12px;
  font-size: 11px;
  font-family: monospace;
  opacity: 0.8;
}
</style>
