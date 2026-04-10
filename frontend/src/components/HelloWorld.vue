<script setup lang="ts">
import { ref } from 'vue'

const message = ref('')
fetch('/api/hello').then(r => r.json()).then(data => { message.value = data.message })

const pieces: Record<string, string> = {
  K: '♔', Q: '♕', R: '♖', B: '♗', N: '♘', P: '♙',
  k: '♚', q: '♛', r: '♜', b: '♝', n: '♞', p: '♟',
}

const board = [
  ['r','n','b','q','k','b','n','r'],
  ['p','p','p','p','p','p','p','p'],
  Array(8).fill(''),
  Array(8).fill(''),
  Array(8).fill(''),
  Array(8).fill(''),
  ['P','P','P','P','P','P','P','P'],
  ['R','N','B','Q','K','B','N','R'],
]
</script>

<template>
  <section id="center">
    <h1>{{ message }}</h1>
    <div class="board">
      <div v-for="(row, r) in board" :key="r" class="row">
        <div
          v-for="(piece, c) in row"
          :key="c"
          class="square"
          :class="(r + c) % 2 === 0 ? 'light' : 'dark'"
        >{{ pieces[piece] ?? '' }}</div>
      </div>
    </div>
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
}
.light { background: #f0d9b5; }
.dark  { background: #b58863; }
</style>
