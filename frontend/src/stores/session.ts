import { defineStore } from 'pinia'
import { ref } from 'vue'

const TOKEN_KEY = 'chakes_client_token'

export const useSessionStore = defineStore('session', () => {
  const token = ref<string>(loadOrCreateToken())

  function loadOrCreateToken(): string {
    let t = sessionStorage.getItem(TOKEN_KEY)
    if (!t) {
      t = crypto.randomUUID()
      sessionStorage.setItem(TOKEN_KEY, t)
    }
    return t
  }

  return { token }
})
