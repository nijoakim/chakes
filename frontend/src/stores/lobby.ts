import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '../services/api'

export const useLobbyStore = defineStore('lobby', () => {
  const currentName = ref<string | null>(null)
  const openLobbies = ref<string[]>([])

  async function create(desiredName?: string): Promise<string> {
    const name = await api.createLobby(desiredName)
    return name
  }

  async function refreshList(): Promise<void> {
    // TODO: returns [] until backend implements /api/lobbies
    openLobbies.value = await api.listLobbies()
  }

  function setCurrent(name: string | null): void {
    currentName.value = name
  }

  return { currentName, openLobbies, create, refreshList, setCurrent }
})
