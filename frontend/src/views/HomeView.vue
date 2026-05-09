<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useLobbyStore } from '../stores/lobby'
import LobbyForm from '../components/lobby/LobbyForm.vue'

const router = useRouter()
const lobby = useLobbyStore()

async function onCreate(desiredName: string | undefined) {
  const name = await lobby.create(desiredName)
  router.push({ name: 'lobby', params: { name } })
}

function onJoin(name: string) {
  router.push({ name: 'lobby', params: { name } })
}
</script>

<template>
  <section id="center">
    <LobbyForm
      @create="onCreate"
      @join="onJoin"
    />
  </section>
</template>
