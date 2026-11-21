import { computed, ref, shallowRef } from 'vue'
import type { Cooldowns } from '@/services/types'
import type { Square } from '@/chakes/square'

/**
 * Cooldown clock. The single source of truth is the last server snapshot plus
 * the local time the server took it (receive time minus rtt/2). Everything
 * else is derived:
 *  - remaining([r, c]) / isOnCooldown([r, c]) for game logic, always exact;
 *  - `grid` for the UI: each cooling square holds its remaining seconds as of
 *    the snapshot (a fresh positive value per push, which restarts the
 *    square's CSS animation), and 0 once it has expired.
 */
export function useCooldownClock() {
  const snapshot = shallowRef<Cooldowns>([])
  let origin = 0 // performance.now() at which the server snapshot was taken
  let lagSec = 0 // seconds already elapsed when the snapshot arrived

  // Bumped whenever a square expires so `grid` re-derives; no per-frame work.
  const expiryTick = ref(0)
  let expiryTimer: ReturnType<typeof setTimeout> | null = null

  function elapsedSec(): number {
    return (performance.now() - origin) / 1000
  }

  function remaining([r, c]: Square): number {
    return Math.max(0, (snapshot.value[r]?.[c] ?? 0) - elapsedSec())
  }

  function isOnCooldown(sq: Square): boolean {
    return remaining(sq) > 0
  }

  const grid = computed<Cooldowns>(() => {
    void expiryTick.value
    const elapsed = elapsedSec()
    return snapshot.value.map((row) =>
      row.map((cd) => (cd - elapsed > 0 ? cd - lagSec : 0)),
    )
  })

  function scheduleNextExpiry(): void {
    if (expiryTimer !== null) clearTimeout(expiryTimer)
    expiryTimer = null
    const elapsed = elapsedSec()
    let next = Infinity
    for (const row of snapshot.value) {
      for (const cd of row) {
        const left = cd - elapsed
        if (left > 0 && left < next) next = left
      }
    }
    if (next === Infinity) return
    // +1ms so the timer never fires just before the deadline.
    expiryTimer = setTimeout(() => {
      expiryTick.value++
      scheduleNextExpiry()
    }, next * 1000 + 1)
  }

  function applySnapshot(cooldowns: Cooldowns, rttMs: number | null): void {
    lagSec = (rttMs ?? 0) / 2000
    origin = performance.now() - lagSec * 1000
    snapshot.value = cooldowns
    scheduleNextExpiry()
  }

  function reset(): void {
    if (expiryTimer !== null) clearTimeout(expiryTimer)
    expiryTimer = null
    origin = 0
    lagSec = 0
    snapshot.value = []
  }

  return { grid, remaining, isOnCooldown, applySnapshot, reset }
}
