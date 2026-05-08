<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import * as api from '../services/api'

const router = useRouter()
const joinLobbyName = ref('')

async function createLobby() {
  const customName = joinLobbyName.value.trim() || undefined
  const name = await api.createLobby(customName)
  router.push({ name: 'lobby', params: { name } })
}

function joinLobby() {
  const name = joinLobbyName.value.trim()
  if (name) router.push({ name: 'lobby', params: { name } })
}
</script>

<template>
  <section id="center">
    <div class="lobby">
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
  </section>
</template>

<style scoped>
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
</style>
