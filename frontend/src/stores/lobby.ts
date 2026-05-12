import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '../services/api'
import type { LobbySummary } from '../services/api'

export const useLobbyStore = defineStore('lobby', () => {
  const currentName = ref<string | null>(null)
  const openLobbies = ref<LobbySummary[]>([])
  const serverName = ref<string | null>(null)

  async function create(desiredName?: string): Promise<string> {
    const name = await api.createLobby(desiredName)
    return name
  }

  async function refreshList(): Promise<void> {
    const data = await api.listLobbies()
    serverName.value = data.server_name
    openLobbies.value = data.lobbies
  }

  function setCurrent(name: string | null): void {
    currentName.value = name
  }

  return { currentName, openLobbies, serverName, create, refreshList, setCurrent }
})
