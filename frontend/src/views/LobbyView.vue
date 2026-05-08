<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import * as api from '../services/api'
import type { Board, Cooldowns, Color, PieceInstance } from '../services/api'
import { gameSocket } from '../services/gameSocket'
import { pieceImages } from '../assets/pieceImages'
import { useSessionStore } from '../stores/session'
import { useCatalogStore } from '../stores/catalog'

const props = defineProps<{ name: string }>()

const session = useSessionStore()
const catalog = useCatalogStore()
const { pieceDefs, gameTypes } = storeToRefs(catalog)

const maxCooldown = ref<Record<string, number>>({
  Pawn: 3, Rook: 3, Knight: 3, Bishop: 3, Queen: 3, King: 3,
})
const pieceNames = ref<string[]>([])
const selectedPromotion = ref('Queen')

const board = ref<Board>([])
const cooldowns = ref<Cooldowns>([])
const selected = ref<[number, number] | null>(null)
const legalMoves = ref<Set<string>>(new Set())
const playerColor = ref<Color>('white')
const gameId = ref<string | null>(null)
const winner = ref<Color | null>(null)
const cooldownSettings = ref<Record<string, number>>({})
const selectedGameType = ref('orthodox')
const upsideDown = ref(false)
let unsubscribers: Array<() => void> = []

let serverCooldowns: Cooldowns = []
let serverCooldownTime = 0
let rafId = 0

function tickCooldowns() {
  const elapsed = (performance.now() - serverCooldownTime) / 1000
  cooldowns.value = serverCooldowns.map(row =>
    row.map(cd => Math.max(cd - elapsed, 0))
  )
  rafId = requestAnimationFrame(tickCooldowns)
}

async function connectToLobby(name: string) {
  unsubscribers.forEach((u) => u())
  unsubscribers = []

  gameSocket.connect(name, session.token)

  unsubscribers.push(
    gameSocket.on('board', (b) => { board.value = b }),
    gameSocket.on('cooldowns', (c) => {
      serverCooldowns = c
      serverCooldownTime = performance.now()
    }),
    gameSocket.on('maxCooldowns', (mc) => { maxCooldown.value = mc }),
    gameSocket.on('pieceNames', (names) => {
      pieceNames.value = names
      if (!names.includes(selectedPromotion.value)) {
        selectedPromotion.value = names.find((n) => n !== 'King' && n !== 'Pawn') ?? names[0]
      }
    }),
    gameSocket.on('color', (c) => { playerColor.value = c }),
    gameSocket.on('gameId', (id) => { gameId.value = id }),
    gameSocket.on('winner', (w) => { winner.value = w }),
  )

  rafId = requestAnimationFrame(tickCooldowns)

  await catalog.load()
  cooldownSettings.value = Object.fromEntries(
    catalog.pieceDefs.map((p) => [p.name, p.default_cooldown])
  )
}

function adjustAllCooldowns(delta: number) {
  for (const name in cooldownSettings.value) {
    cooldownSettings.value[name] = Math.max(0, cooldownSettings.value[name] + delta)
  }
}

function returnToSetup() {
  board.value = []
  cooldowns.value = []
  serverCooldowns = []
  gameId.value = null
  winner.value = null
  selected.value = null
  legalMoves.value = new Set()
}

async function newGame() {
  returnToSetup()
  await api.createGame(props.name, selectedGameType.value, cooldownSettings.value, upsideDown.value)
}

onMounted(() => {
  connectToLobby(props.name)
  window.addEventListener('keydown', onKeydown)
})
onUnmounted(() => {
  unsubscribers.forEach((u) => u())
  gameSocket.disconnect()
  cancelAnimationFrame(rafId)
  window.removeEventListener('keydown', onKeydown)
})

const displayBoard = computed<Board>(() => {
  if (playerColor.value === 'black') {
    return [...board.value].reverse().map(row => [...row].reverse())
  }
  return board.value
})

const displayCooldowns = computed<Cooldowns>(() => {
  if (playerColor.value === 'black') {
    return [...cooldowns.value].reverse().map(row => [...row].reverse())
  }
  return cooldowns.value
})

function displayToBoard(r: number, c: number): [number, number] {
  return playerColor.value === 'black' ? [7 - r, 7 - c] : [r, c]
}

function isSelected(displayR: number, displayC: number): boolean {
  if (!selected.value) return false
  const [br, bc] = displayToBoard(displayR, displayC)
  return selected.value[0] === br && selected.value[1] === bc
}

function isOnCooldown(r: number, c: number): boolean {
  return (cooldowns.value[r]?.[c] ?? 0) > 0
}

function isLegalMove(displayR: number, displayC: number): boolean {
  const [br, bc] = displayToBoard(displayR, displayC)
  return legalMoves.value.has(`${br},${bc}`)
}

async function selectPiece(r: number, c: number) {
  selected.value = [r, c]
  legalMoves.value = new Set()
  const moves = await api.getLegalMoves(props.name, gameId.value!, r, c)
  if (selected.value && selected.value[0] === r && selected.value[1] === c) {
    legalMoves.value = new Set(moves.map(([mr, mc]: number[]) => `${mr},${mc}`))
  }
}

const isOwnPiece = (p: PieceInstance) => p.owner === playerColor.value

function deselect() {
  selected.value = null
  legalMoves.value = new Set()
}

function handleClick(displayR: number, displayC: number) {
  if (!gameId.value || winner.value) return
  const [r, c] = displayToBoard(displayR, displayC)
  const piece = board.value[r][c]

  if (selected.value === null) {
    if (piece && isOwnPiece(piece) && !isOnCooldown(r, c))
      selectPiece(r, c)
  } else {
    if (piece && isOwnPiece(piece) && !isOnCooldown(r, c)) {
      const [fr, fc] = selected.value
      if (fr === r && fc === c) deselect()
      else selectPiece(r, c)
    } else if (legalMoves.value.has(`${r},${c}`)) {
      const [fr, fc] = selected.value
      deselect()
      api.sendMove(props.name, gameId.value, fr, fc, r, c, selectedPromotion.value)
    }
  }
}

function handleRightClick(e: MouseEvent, displayR: number, displayC: number) {
  if (!gameId.value || winner.value || !selected.value) return
  e.preventDefault()
  const [r, c] = displayToBoard(displayR, displayC)
  const [fr, fc] = selected.value
  if (fr !== r || fc !== c) {
    deselect()
    api.sendMove(props.name, gameId.value, fr, fc, r, c, selectedPromotion.value)
  }
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') deselect()
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
    <div
      v-if="!gameId"
      class="game-setup"
    >
      <template v-if="playerColor === 'white' && pieceDefs.length">
        <div class="game-type-picker">
          <label
            v-for="gt in gameTypes"
            :key="gt.id"
            :class="{ active: selectedGameType === gt.id }"
          >
            <input
              v-model="selectedGameType"
              type="radio"
              :value="gt.id"
            >
            {{ gt.name }}
          </label>
        </div>
        <div class="cooldown-all">
          <button @click="adjustAllCooldowns(-1)">
            −
          </button>
          <span>All cooldowns</span>
          <button @click="adjustAllCooldowns(1)">
            +
          </button>
        </div>
        <table class="cooldown-table">
          <thead>
            <tr>
              <th>Piece</th>
              <th>Cooldown (s)</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="p in pieceDefs"
              :key="p.name"
            >
              <td>{{ p.name }}</td>
              <td>
                <input
                  v-model.number="cooldownSettings[p.name]"
                  type="number"
                  min="0"
                  step="1"
                >
              </td>
            </tr>
          </tbody>
        </table>
      </template>
      <p
        v-if="playerColor !== 'white'"
        class="waiting-text"
      >
        Waiting for host to start the game…
      </p>
      <label
        v-if="playerColor === 'white'"
        class="checkbox-label"
      >
        <input
          v-model="upsideDown"
          type="checkbox"
        >
        Upside-down chess
      </label>
      <button
        v-if="playerColor === 'white'"
        @click="newGame"
      >
        Start game
      </button>
    </div>
    <div
      v-if="gameId && pieceNames.length"
      class="promotion-bar"
    >
      <span class="promotion-label">Promote to</span>
      <div class="promotion-squares">
        <div
          v-for="(pieceName, i) in pieceNames"
          :key="pieceName"
          class="square"
          :class="[
            i % 2 === 0 ? 'light' : 'dark',
            selectedPromotion === pieceName ? 'selected' : '',
          ]"
          @click="selectedPromotion = pieceName"
        >
          <img
            v-if="pieceImages[pieceName]"
            :src="pieceImages[pieceName]![playerColor]"
            class="piece-img"
            :alt="pieceName"
          >
          <span
            v-else
            class="piece-text"
          >{{ pieceName }}</span>
        </div>
      </div>
    </div>
    <div
      v-if="gameId"
      class="board"
    >
      <div
        v-for="(row, r) in displayBoard"
        :key="r"
        class="row"
      >
        <div
          v-for="(piece, c) in row"
          :key="c"
          class="square"
          :class="[
            (r + c) % 2 === 0 ? 'light' : 'dark',
            isSelected(r, c) ? 'selected' : '',
            isLegalMove(r, c) ? 'legal-move' : '',
            piece ? 'piece' : '',
            (displayCooldowns[r]?.[c] ?? 0) > 0 ? 'on-cooldown' : '',
          ]"
          @click="handleClick(r, c)"
          @contextmenu="handleRightClick($event, r, c)"
        >
          <img
            v-if="piece && pieceImages[piece.name]"
            :src="pieceImages[piece.name]![piece.owner]"
            class="piece-img"
            :alt="piece.name"
          >
          <span
            v-else-if="piece"
            class="piece-text"
          >{{ piece.name }}</span>
          <div
            v-if="(displayCooldowns[r]?.[c] ?? 0) > 0"
            class="cooldown-overlay"
            :style="{ height: (displayCooldowns[r][c] / (maxCooldown[piece?.name ?? ''] ?? 1) * 100) + '%' }"
          />
        </div>
      </div>
    </div>
    <div
      v-if="winner"
      class="winner-banner"
    >
      {{ winner === 'white' ? '♔ White' : '♚ Black' }} won!
    </div>

    <button
      v-if="playerColor === 'white' && gameId"
      class="new-game"
      @click="returnToSetup"
    >
      New Game
    </button>
  </section>
</template>

<style scoped>
.board {
  --sq: min(64px, calc((100vw - 44px) / 8));
  display: inline-block;
  border: 2px solid #333;
}
.row {
  display: flex;
}
.square {
  width: var(--sq);
  height: var(--sq);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: default;
  user-select: none;
}
.piece-img {
  width: calc(var(--sq) * 0.9);
  height: calc(var(--sq) * 0.9);
  pointer-events: none;
  user-select: none;
  display: block;
}
.piece-text {
  font-size: calc(var(--sq) * 0.35);
  line-height: 1;
  text-align: center;
  font-weight: bold;
  pointer-events: none;
  user-select: none;
}
.square.piece {
  cursor: pointer;
}
.square {
  position: relative;
}
.square.on-cooldown {
  cursor: not-allowed;
}
.cooldown-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  background: rgba(80, 80, 80, 0.5);
  pointer-events: none;
}
.promotion-bar {
  --sq: min(64px, calc((100vw - 44px) / 8));
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 8px 0;
  border: 2px solid #333;
  border-bottom: none;
  background: rgba(0, 0, 0, 0.04);
}
.promotion-label {
  font-size: 12px;
  color: #666;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
.promotion-squares {
  display: flex;
}
.light { background: #f0d9b5; }
.dark  { background: #b58863; }
.square.selected::after,
.square.legal-move::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.square.selected::after { background: rgba(246, 246, 105, 0.6); }
.square.legal-move::after { background: rgba(130, 190, 80, 0.45); }
.square.legal-move { cursor: pointer; }
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
.game-setup {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: center;
  padding: 24px;
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
.checkbox-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  cursor: pointer;
}
.waiting-text {
  color: #888;
  font-size: 15px;
}
.game-type-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: center;
}
.game-type-picker label {
  padding: 4px 10px;
  border: 1px solid #aaa;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}
.game-type-picker label.active {
  border-color: #333;
  font-weight: bold;
  background: #f0f0f0;
}
.game-type-picker input[type=radio] {
  display: none;
}
.cooldown-all {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
}
.cooldown-table {
  border-collapse: collapse;
  font-size: 14px;
}
.cooldown-table th,
.cooldown-table td {
  padding: 4px 10px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}
.cooldown-table input[type=number] {
  width: 60px;
}
</style>
