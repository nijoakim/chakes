import { onMounted, onUnmounted } from 'vue'

type Handler = (e: KeyboardEvent) => void

export function useKeyboardShortcuts(handlers: Record<string, Handler>): void {
  function onKeydown(e: KeyboardEvent) {
    const handler = handlers[e.key]
    if (handler) handler(e)
  }
  onMounted(() => window.addEventListener('keydown', onKeydown))
  onUnmounted(() => window.removeEventListener('keydown', onKeydown))
}
