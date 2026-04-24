<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { gameService, type Board, type Cooldowns, type Color } from '../services/gameService'

const pieces: Record<string, string> = {
  K: '♔', Q: '♕', R: '♖', B: '♗', N: '♘', P: '♙',
  k: '♚', q: '♛', r: '♜', b: '♝', n: '♞', p: '♟',
}

const maxCooldown: Record<string, number> = {
  P: 3, R: 3, N: 3, B: 3, Q: 3, K: 3,
  p: 3, r: 3, n: 3, b: 3, q: 3, k: 3,
}

const board = ref<Board>([])
const cooldowns = ref<Cooldowns>([])
const selected = ref<[number, number] | null>(null)
const playerColor = ref<Color>('white')
const preferredColor = ref<Color>('white')
const roomId = ref<string | null>(null)
const joinRoomId = ref('')
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

function connectToRoom(id: string) {
  disconnect?.()
  roomId.value = id
  playerColor.value = preferredColor.value
  disconnect = gameService.connect(id, {
    onBoard: (b) => { board.value = b },
    onCooldowns: (c) => {
      serverCooldowns = c
      serverCooldownTime = performance.now()
    },
  })
  rafId = requestAnimationFrame(tickCooldowns)
}

async function createRoom() {
  const id = await gameService.createRoom()
  connectToRoom(id)
}

function joinRoom() {
  if (joinRoomId.value.trim()) connectToRoom(joinRoomId.value.trim())
}

onUnmounted(() => {
  disconnect?.()
  cancelAnimationFrame(rafId)
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

function handleClick(displayR: number, displayC: number) {
  const [r, c] = displayToBoard(displayR, displayC)
  const ownPiece = (p: string) =>
    playerColor.value === 'white' ? p === p.toUpperCase() : p === p.toLowerCase()

  if (selected.value === null) {
    if (board.value[r][c] && ownPiece(board.value[r][c]) && !isOnCooldown(r, c))
      selected.value = [r, c]
  } else {
    const [fr, fc] = selected.value
    selected.value = null
    if (fr !== r || fc !== c) {
      gameService.sendMove(roomId.value!, fr, fc, r, c)
    }
  }
}
</script>

<template>
  <section id="center">
    <div v-if="!roomId" class="lobby">
      <div class="color-picker">
        <button :class="{ active: preferredColor === 'white' }" @click="preferredColor = 'white'">♔ White</button>
        <button :class="{ active: preferredColor === 'black' }" @click="preferredColor = 'black'">♚ Black</button>
      </div>
      <button @click="createRoom">Create game</button>
      <div class="join">
        <input v-model="joinRoomId" placeholder="Room ID" @keyup.enter="joinRoom" />
        <button @click="joinRoom">Join game</button>
      </div>
    </div>
    <template v-else>
    <div class="room-name">Room: {{ roomId }}</div>
    <div class="board">
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
            piece ? 'piece' : '',
            (displayCooldowns[r]?.[c] ?? 0) > 0 ? 'on-cooldown' : '',
          ]"
          @click="handleClick(r, c)"
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
    <div class="color-label">{{ playerColor === 'white' ? '♔ White' : '♚ Black' }}</div>
    </template>
  </section>
</template>

<style scoped>
.board {
  display: inline-block;
  border: 2px solid #333;
}
.row {
  display: flex;
}
.square {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 42px;
  line-height: 1;
  cursor: default;
}
.square.piece {
  cursor: pointer;
}
.square.on-cooldown {
  cursor: not-allowed;
  position: relative;
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
.selected { background: #f6f669; }
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
.color-picker {
  display: flex;
  gap: 8px;
}
.color-picker button.active {
  outline: 2px solid #333;
  font-weight: bold;
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
</style>
