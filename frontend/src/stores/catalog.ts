import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '../services/api'
import type { PieceDef, GameType } from '../services/api'

export const useCatalogStore = defineStore('catalog', () => {
  const pieceDefs = ref<PieceDef[]>([])
  const gameTypes = ref<GameType[]>([])
  const loaded = ref(false)

  async function load(): Promise<void> {
    if (loaded.value) return
    const [defs, types] = await Promise.all([
      api.getPieceDefs(),
      api.getGameTypes(),
    ])
    pieceDefs.value = defs
    gameTypes.value = types
    loaded.value = true
  }

  return { pieceDefs, gameTypes, loaded, load }
})
