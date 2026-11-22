import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/services/api'
import type { LobbySummary } from '@/services/types'

export type ListStatus = 'loading' | 'ok' | 'error'

/** Thrown by `create` when a lobby with the requested name already exists. */
export class LobbyNameTakenError extends Error {
  readonly lobbyName: string

  constructor(lobbyName: string) {
    super(`A lobby named "${lobbyName}" already exists`)
    this.name = 'LobbyNameTakenError'
    this.lobbyName = lobbyName
  }
}

const LIST_TIMEOUT_MS = 8000

function sameRow(a: LobbySummary, b: LobbySummary): boolean {
  return JSON.stringify(a) === JSON.stringify(b)
}

/**
 * Merge a fresh list into the current one without reordering rows the user
 * already sees: known lobbies keep their position (updated in place), new
 * lobbies are appended in server order, vanished lobbies are dropped.
 * Returns `current` itself when nothing changed, so nothing re-renders.
 */
function mergeLobbies(current: LobbySummary[], fresh: LobbySummary[]): LobbySummary[] {
  const freshByName = new Map(fresh.map(l => [l.name, l]))
  const kept: LobbySummary[] = []
  let changed = false
  for (const old of current) {
    const next = freshByName.get(old.name)
    if (!next) {
      changed = true
      continue
    }
    if (sameRow(old, next)) {
      kept.push(old)
    } else {
      kept.push(next)
      changed = true
    }
    freshByName.delete(old.name)
  }
  if (freshByName.size > 0) changed = true
  return changed ? [...kept, ...freshByName.values()] : current
}

export const useLobbyStore = defineStore('lobby', () => {
  const openLobbies = ref<LobbySummary[]>([])
  const serverName = ref<string | null>(null)
  /** 'loading' until the first fetch settles; 'error' while the latest fetch failed. */
  const listStatus = ref<ListStatus>('loading')
  const hasLoaded = ref(false)

  let inFlight: Promise<boolean> | null = null

  function applyList(data: { server_name: string, lobbies: LobbySummary[] }) {
    serverName.value = data.server_name
    openLobbies.value = mergeLobbies(openLobbies.value, data.lobbies)
    listStatus.value = 'ok'
    hasLoaded.value = true
  }

  /** Fetch the lobby list. Never rejects; resolves to whether it succeeded. */
  function refreshList(): Promise<boolean> {
    if (inFlight) return inFlight
    inFlight = (async () => {
      try {
        applyList(await api.listLobbies({ signal: AbortSignal.timeout(LIST_TIMEOUT_MS) }))
        return true
      } catch (e) {
        console.warn('Failed to fetch lobby list:', e)
        listStatus.value = 'error'
        return false
      } finally {
        inFlight = null
      }
    })()
    return inFlight
  }

  /**
   * Create a lobby and return its name. An empty name asks the server for a
   * random one. The server refuses a taken name with 409, which surfaces as
   * LobbyNameTakenError; other failures propagate as ApiError / fetch errors.
   */
  async function create(name: string): Promise<string> {
    try {
      return await api.createLobby(name || undefined)
    } catch (e) {
      if (name && e instanceof api.ApiError && e.status === 409) throw new LobbyNameTakenError(name)
      throw e
    }
  }

  return { openLobbies, serverName, listStatus, hasLoaded, create, refreshList }
})
