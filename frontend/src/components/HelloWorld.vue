<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { gameService, type Board, type Color } from '../services/gameService'

const message = ref('')
fetch('/api/hello').then(r => r.json()).then(data => { message.value = data.message })

const pieces: Record<string, string> = {
  K: '♔', Q: '♕', R: '♖', B: '♗', N: '♘', P: '♙',
  k: '♚', q: '♛', r: '♜', b: '♝', n: '♞', p: '♟',
}

const board = ref<Board>([
  ['r','n','b','q','k','b','n','r'],
  ['p','p','p','p','p','p','p','p'],
  Array(8).fill(''),
  Array(8).fill(''),
  Array(8).fill(''),
  Array(8).fill(''),
  ['P','P','P','P','P','P','P','P'],
  ['R','N','B','Q','K','B','N','R'],
])

const selected = ref<[number, number] | null>(null)
const gameId = ref<string | null>(null)
const playerColor = ref<Color>('white')
let disconnect: (() => void) | null = null

const displayBoard = computed<Board>(() => {
  if (playerColor.value === 'black') {
    return [...board.value].reverse().map(row => [...row].reverse())
  }
  return board.value
})

function displayToBoard(r: number, c: number): [number, number] {
  return playerColor.value === 'black' ? [7 - r, 7 - c] : [r, c]
}

function isSelected(displayR: number, displayC: number): boolean {
  if (!selected.value) return false
  const [br, bc] = displayToBoard(displayR, displayC)
  return selected.value[0] === br && selected.value[1] === bc
}

onMounted(async () => {
  gameId.value = await gameService.createGame()
  disconnect = gameService.connect(gameId.value, {
    onBoard: (b) => { board.value = b },
    onColor: (c) => { playerColor.value = c },
  })
})

onUnmounted(() => disconnect?.())

function handleClick(displayR: number, displayC: number) {
  const [r, c] = displayToBoard(displayR, displayC)
  const ownPiece = (p: string) =>
    playerColor.value === 'white' ? p === p.toUpperCase() : p === p.toLowerCase()

  if (selected.value === null) {
    if (board.value[r][c] && ownPiece(board.value[r][c])) selected.value = [r, c]
  } else {
    const [fr, fc] = selected.value
    selected.value = null
    if (fr !== r || fc !== c) {
      gameService.sendMove(gameId.value!, fr, fc, r, c)
    }
  }
}
</script>

<template>
  <section id="center">
    <h1>{{ message }}</h1>
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
          :class="[(r + c) % 2 === 0 ? 'light' : 'dark', isSelected(r, c) ? 'selected' : '', piece ? 'piece' : '']"
          @click="handleClick(r, c)"
        >
          {{ pieces[piece] ?? '' }}
        </div>
      </div>
    </div>
    <div class="color-label">{{ playerColor === 'white' ? '♔ White' : '♚ Black' }}</div>
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
.light { background: #f0d9b5; }
.dark  { background: #b58863; }
.selected { background: #f6f669; }
.color-label {
  margin-top: 6px;
  font-size: 18px;
  text-align: center;
}
</style>
