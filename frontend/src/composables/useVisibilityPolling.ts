import { onBeforeUnmount, onMounted } from 'vue'

/**
 * Calls `tick` on mount and then every `intervalMs` while the component is
 * mounted and the tab is visible. Polling pauses while `document.hidden`,
 * fires immediately when the tab becomes visible again, and never overlaps
 * requests (the next tick is scheduled only after the previous one settles).
 */
export function useVisibilityPolling(tick: () => Promise<unknown>, intervalMs: number) {
  let timer: ReturnType<typeof setTimeout> | null = null
  let active = false
  let running: Promise<void> | null = null

  function clear() {
    if (timer !== null) {
      clearTimeout(timer)
      timer = null
    }
  }

  function schedule() {
    clear()
    if (active && !document.hidden) timer = setTimeout(() => void runNow(), intervalMs)
  }

  /** Run a tick now (or join the one in flight) and restart the interval. */
  function runNow(): Promise<void> {
    if (running) return running
    clear()
    if (!active) return Promise.resolve()
    running = (async () => {
      try {
        await tick()
      } catch {
        // `tick` is expected to handle its own errors; keep polling regardless.
      } finally {
        running = null
        schedule()
      }
    })()
    return running
  }

  function onVisibilityChange() {
    if (document.hidden) clear()
    else void runNow()
  }

  onMounted(() => {
    active = true
    document.addEventListener('visibilitychange', onVisibilityChange)
    void runNow()
  })

  onBeforeUnmount(() => {
    active = false
    clear()
    document.removeEventListener('visibilitychange', onVisibilityChange)
  })

  return { runNow }
}
