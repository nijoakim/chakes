<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { gameService, type Board, type Cooldowns, type Color, type PieceDef } from '../services/gameService'

const pieces: Record<string, string> = {
  K: '♔', Q: '♕', R: '♖', B: '♗', N: '♘', P: '♙',
  k: '♚', q: '♛', r: '♜', b: '♝', n: '♞', p: '♟',
}

const maxCooldown = ref<Record<string, number>>({
  P: 3, R: 3, N: 3, B: 3, Q: 3, K: 3,
  p: 3, r: 3, n: 3, b: 3, q: 3, k: 3,
})

const board = ref<Board>([])
const cooldowns = ref<Cooldowns>([])
const selected = ref<[number, number] | null>(null)
const legalMoves = ref<Set<string>>(new Set())
const playerColor = ref<Color>('white')
const lobbyName = ref<string | null>(null)
const gameId = ref<string | null>(null)
const winner = ref<Color | null>(null)
const joinLobbyName = ref('')
const pieceDefs = ref<PieceDef[]>([])
const cooldownSettings = ref<Record<string, number>>({})
let disconnect: (() => void) | null = null

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
  disconnect?.()
  lobbyName.value = name
  history.pushState(null, '', `/lobby/${encodeURIComponent(name)}`)
  disconnect = gameService.connect(name, {
    onBoard: (b) => { board.value = b },
    onCooldowns: (c) => {
      serverCooldowns = c
      serverCooldownTime = performance.now()
    },
    onMaxCooldowns: (mc) => { maxCooldown.value = mc },
    onColor: (c) => { playerColor.value = c },
    onGameId: (id) => { gameId.value = id },
    onWinner: (w) => { winner.value = w },
  })
  rafId = requestAnimationFrame(tickCooldowns)
  pieceDefs.value = await gameService.getPieceDefs()
  cooldownSettings.value = Object.fromEntries(
    pieceDefs.value.map(p => [p.name, p.default_cooldown])
  )
}

async function createLobby() {
  const customName = joinLobbyName.value.trim() || undefined
  const name = await gameService.createLobby(customName)
  connectToLobby(name)
}

function adjustAllCooldowns(delta: number) {
  for (const name in cooldownSettings.value) {
    cooldownSettings.value[name] = Math.max(0, cooldownSettings.value[name] + delta)
  }
}

async function newGame() {
  if (lobbyName.value) {
    board.value = []
    cooldowns.value = []
    serverCooldowns = []
    gameId.value = null
    winner.value = null
    selected.value = null
    await gameService.createGame(lobbyName.value, cooldownSettings.value)
  }
}

function joinLobby() {
  if (joinLobbyName.value.trim()) connectToLobby(joinLobbyName.value.trim())
}

const lobbyFromUrl = window.location.pathname.match(/^\/lobby\/([^/]+)/)?.[1]
if (lobbyFromUrl) {
  connectToLobby(decodeURIComponent(lobbyFromUrl))
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => {
  disconnect?.()
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
  const moves = await gameService.getLegalMoves(lobbyName.value!, gameId.value!, r, c)
  if (selected.value && selected.value[0] === r && selected.value[1] === c) {
    legalMoves.value = new Set(moves.map(([mr, mc]: number[]) => `${mr},${mc}`))
  }
}

const isOwnPiece = (p: string) =>
  playerColor.value === 'white' ? p === p.toUpperCase() : p === p.toLowerCase()

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
      gameService.sendMove(lobbyName.value!, gameId.value, fr, fc, r, c)
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
    gameService.sendMove(lobbyName.value!, gameId.value, fr, fc, r, c)
  }
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') deselect()
}
</script>

<template>
  <section id="center">
    <div
      v-if="!lobbyName"
      class="lobby"
    >
      <button @click="createLobby">
        Create lobby
      </button>
      <div class="join">
        <input
          v-model="joinLobbyName"
          placeholder="Lobby name"
          @keyup.enter="joinLobby"
        >
        <button @click="joinLobby">
          Join lobby
        </button>
      </div>
    </div>
    <template v-else>
      <div class="room-name">
        Lobby: {{ lobbyName }}
      </div>
      <div
        v-if="!gameId"
        class="game-setup"
      >
        <template v-if="playerColor === 'white' && pieceDefs.length">
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
        <button @click="newGame">
          Start game
        </button>
      </div>
      <div
        v-else
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
            {{ pieces[piece] ?? '' }}
            <div
              v-if="(displayCooldowns[r]?.[c] ?? 0) > 0"
              class="cooldown-overlay"
              :style="{ height: (displayCooldowns[r][c] / (maxCooldown[piece] ?? 1) * 100) + '%' }"
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
      <div class="color-label">
        {{ playerColor === 'white' ? '♔ White' : '♚ Black' }}
      </div>
      <button
        class="new-game"
        @click="newGame"
      >
        New Game
      </button>
    </template>
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
  font-size: calc(var(--sq) * 0.656);
  line-height: 1;
  cursor: default;
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
.color-label {
  margin-top: 6px;
  font-size: 18px;
  text-align: center;
}
.lobby {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: center;
}
.join {
  display: flex;
  gap: 8px;
}
.room-name {
  margin-bottom: 6px;
  font-size: 13px;
  color: #666;
  text-align: center;
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
