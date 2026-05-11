import type { GameSocket } from './gameSocket'

export class RttMonitor {
  rtt: number | null = null

  private socket: GameSocket
  private intervalMs: number
  private alpha: number
  private pending = new Map<string, number>()
  private timer: ReturnType<typeof setInterval> | null = null
  private unsubscribe: (() => void) | null = null

  constructor(socket: GameSocket, intervalMs = 3000, alpha = 0.2) {
    this.socket = socket
    this.intervalMs = intervalMs
    this.alpha = alpha
  }

  start(): void {
    if (this.timer !== null) return
    this.unsubscribe = this.socket.on('pong', ({ id }) => {
      const sent = this.pending.get(id)
      if (sent === undefined) return
      this.pending.delete(id)
      const sample = performance.now() - sent
      this.rtt = this.rtt === null ? sample : this.alpha * sample + (1 - this.alpha) * this.rtt
    })
    this.timer = setInterval(() => this.ping(), this.intervalMs)
  }

  stop(): void {
    if (this.timer !== null) { clearInterval(this.timer); this.timer = null }
    this.unsubscribe?.(); this.unsubscribe = null
    this.pending.clear()
  }

  private ping(): void {
    const id = crypto.randomUUID()
    this.pending.set(id, performance.now())
    this.socket.send({ type: 'ping', id })
  }
}
