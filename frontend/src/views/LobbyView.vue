<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useCatalogStore } from '../stores/catalog'
import { useGameStore } from '../stores/game'
import { useLobbyStore } from '../stores/lobby'
import { useKeyboardShortcuts } from '../composables/useKeyboardShortcuts'
import ChakesBoard from '../components/chess/ChakesBoard.vue'
import PromotionBar from '../components/chess/PromotionBar.vue'
import GameSetup from '../components/lobby/GameSetup.vue'

const props = defineProps<{ name: string }>()

const game = useGameStore()
const lobby = useLobbyStore()
const catalog = useCatalogStore()
const {
  board, cooldowns, maxCooldowns, pieceNames, playerColor, gameId, winner,
  selected, legalMoves, selectedPromotion,
} = storeToRefs(game)

const boardCols = computed(() => board.value[0]?.length ?? 8)

type StartPayload = { gameType: string; cooldowns: Record<string, number>; upsideDown: boolean }
let lastSettings: StartPayload | null = null

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

async function onStartGame(payload: StartPayload) {
  lastSettings = payload
  await game.startNewGame(payload.gameType, payload.cooldowns, payload.upsideDown)
}

async function onNewGame() {
  if (lastSettings) await onStartGame(lastSettings)
}

function copyLobbyName() {
  navigator.clipboard.writeText(props.name)
}
</script>

<template>
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
      @start="onStartGame"
    />
    <p
      v-if="!gameId && playerColor !== 'white'"
      class="waiting-text"
    >
      Waiting for host to start the game…
    </p>

    <PromotionBar
      v-if="gameId && pieceNames.length"
      :piece-names="pieceNames"
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
      @square-click="(r, c) => game.handleSquareClick(r, c)"
      @square-right-click="(r, c) => game.handleSquareRightClick(r, c)"
    />

    <div
      v-if="winner"
      class="winner-banner"
    >
      {{ winner === 'white' ? '♔ White' : '♚ Black' }} won!
    </div>
    <button
      v-if="playerColor === 'white' && lastSettings"
      class="new-game"
      @click="onNewGame"
    >
      New game
    </button>
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
.winner-banner {
  margin-top: 12px;
  padding: 12px 24px;
  font-size: 28px;
  font-weight: bold;
  text-align: center;
  background: #f6f669;
  border-radius: 6px;
}
.new-game {
  margin-top: 12px;
}
.waiting-text {
  color: #888;
  font-size: 15px;
}
</style>
