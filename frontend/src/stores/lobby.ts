import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/services/api'
import type { LobbySummary } from '@/services/types'

export const useLobbyStore = defineStore('lobby', () => {
  const openLobbies = ref<LobbySummary[]>([])
  const serverName = ref<string | null>(null)

  async function refreshList(): Promise<void> {
    const data = await api.listLobbies()
    serverName.value = data.server_name
    openLobbies.value = data.lobbies
  }

  return { openLobbies, serverName, create: api.createLobby, refreshList }
})
