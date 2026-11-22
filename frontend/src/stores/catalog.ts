import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/services/api'
import * as catalogApi from '@/services/catalogApi'
import type { PieceDef } from '@/services/types'
import type { GameTypeInfo, OptionDescriptions, PieceGuide } from '@/services/catalogTypes'

export const useCatalogStore = defineStore('catalog', () => {
  const pieceDefs = ref<PieceDef[]>([])
  const gameTypes = ref<GameTypeInfo[]>([])
  const optionDescriptions = ref<OptionDescriptions>({})
  /** Movement guides per game type, fetched on demand and kept for the session. */
  const pieceGuides = ref<Record<string, PieceGuide[]>>({})
  const loaded = ref(false)

  async function load(): Promise<void> {
    if (loaded.value) return
    const [defs, types] = await Promise.all([
      api.getPieceDefs(),
      catalogApi.getGameTypesInfo(),
    ])
    pieceDefs.value = defs
    gameTypes.value = types.game_types
    optionDescriptions.value = types.options ?? {}
    loaded.value = true
  }

  async function loadPieceGuide(gameType: string): Promise<PieceGuide[]> {
    const cached = pieceGuides.value[gameType]
    if (cached) return cached
    const guide = await catalogApi.getPieceGuide(gameType)
    pieceGuides.value[gameType] = guide
    return guide
  }

  return { pieceDefs, gameTypes, optionDescriptions, pieceGuides, loaded, load, loadPieceGuide }
})
