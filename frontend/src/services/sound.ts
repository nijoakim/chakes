/**
 * Sound effects, synthesised on the fly with the Web Audio API (no assets).
 *
 * The palette is "wood and felt": every sound is a short band-passed noise
 * transient (the click of a piece touching the board) and/or a soft,
 * fast-decaying tone (the body of the knock). Tonal cues (start, end) use a
 * marimba-like voice: a sine fundamental plus a quickly dying 4th partial.
 *
 * Browsers block audio until a user gesture, so the AudioContext is created
 * lazily on the first pointer/key interaction. Every failure path is silent:
 * no audio support simply means no sound.
 */
import { reactive, watch } from 'vue'

export type SoundName =
  | 'moveOwn' | 'moveOpponent' | 'capture' | 'reject'
  | 'check' | 'antiCheck' | 'ready'
  | 'gameStart' | 'gameWin' | 'gameLoss' | 'gameEnd'

// --- Settings (persisted like `chakes_latency_hiding`) ---

const MUTED_KEY = 'chakes_sound_muted'
const VOLUME_KEY = 'chakes_sound_volume'
const DEFAULT_VOLUME = 0.5

function readStorage(key: string): string | null {
  try { return localStorage.getItem(key) } catch { return null }
}
function writeStorage(key: string, value: string): void {
  try { localStorage.setItem(key, value) } catch { /* storage unavailable */ }
}

function initialVolume(): number {
  const v = Number(readStorage(VOLUME_KEY))
  return readStorage(VOLUME_KEY) !== null && Number.isFinite(v) ? Math.min(1, Math.max(0, v)) : DEFAULT_VOLUME
}

export const soundSettings = reactive({
  muted: readStorage(MUTED_KEY) === 'true',
  /** 0..1, mapped to the master gain on a perceptual (squared) curve. */
  volume: initialVolume(),
})

watch(() => soundSettings.muted, (m) => writeStorage(MUTED_KEY, String(m)))
watch(() => soundSettings.volume, (v) => {
  writeStorage(VOLUME_KEY, String(v))
  applyMasterGain()
})

// --- Synthesis primitives ---

type Ctx = BaseAudioContext

const noiseBuffers = new WeakMap<Ctx, AudioBuffer>()
function noiseBuffer(ctx: Ctx): AudioBuffer {
  let buf = noiseBuffers.get(ctx)
  if (!buf) {
    buf = ctx.createBuffer(1, Math.ceil(ctx.sampleRate * 0.1), ctx.sampleRate)
    const data = buf.getChannelData(0)
    for (let i = 0; i < data.length; i++) data[i] = Math.random() * 2 - 1
    noiseBuffers.set(ctx, buf)
  }
  return buf
}

/** Gain node with a fast attack and exponential decay, starting at t. */
function envelope(ctx: Ctx, out: AudioNode, t: number, peak: number, dur: number): GainNode {
  const g = ctx.createGain()
  g.gain.setValueAtTime(0.0001, t)
  g.gain.exponentialRampToValueAtTime(peak, t + 0.002)
  g.gain.exponentialRampToValueAtTime(0.0001, t + dur)
  g.connect(out)
  return g
}

/** Band-passed noise burst: the "click" of wood on wood. */
function click(ctx: Ctx, out: AudioNode, t: number, freq: number, q: number, dur: number, peak: number): void {
  const src = ctx.createBufferSource()
  src.buffer = noiseBuffer(ctx)
  const bp = ctx.createBiquadFilter()
  bp.type = 'bandpass'
  bp.frequency.value = freq
  bp.Q.value = q
  src.connect(bp).connect(envelope(ctx, out, t, peak, dur))
  src.start(t)
  src.stop(t + dur + 0.01)
}

/** Short tone with a downward pitch glide: the "body" of a knock. */
function tone(
  ctx: Ctx, out: AudioNode, t: number, type: OscillatorType,
  f0: number, f1: number, dur: number, peak: number,
): void {
  const osc = ctx.createOscillator()
  osc.type = type
  osc.frequency.setValueAtTime(f0, t)
  if (f1 !== f0) osc.frequency.exponentialRampToValueAtTime(f1, t + dur * 0.6)
  osc.connect(envelope(ctx, out, t, peak, dur))
  osc.start(t)
  osc.stop(t + dur + 0.01)
}

/** Marimba-ish note: sine fundamental plus a quickly decaying 4th partial and a soft mallet tick. */
function mallet(ctx: Ctx, out: AudioNode, t: number, freq: number, dur: number, peak: number): void {
  tone(ctx, out, t, 'sine', freq, freq, dur, peak)
  tone(ctx, out, t, 'sine', freq * 4, freq * 4, dur * 0.25, peak * 0.18)
  click(ctx, out, t, 2500, 1.5, 0.012, peak * 0.4)
}

/** Lowpass bus, to darken a whole sound. */
function lowpass(ctx: Ctx, out: AudioNode, freq: number): BiquadFilterNode {
  const lp = ctx.createBiquadFilter()
  lp.type = 'lowpass'
  lp.frequency.value = freq
  lp.Q.value = 0.5
  lp.connect(out)
  return lp
}

interface SoundDef {
  /** Nominal length in seconds (for voice accounting). */
  dur: number
  /** Minimum seconds between two plays of this sound; extra plays are dropped. */
  minInterval: number
  /** High-priority sounds may exceed the voice limit. */
  priority?: boolean
  /** Instead of dropping plays inside minInterval, play once at the end of the window. */
  coalesce?: boolean
  render: (ctx: Ctx, out: AudioNode, t: number) => void
}

const SOUNDS: Record<SoundName, SoundDef> = {
  // Own move: bright, dry "tock".
  moveOwn: {
    dur: 0.08, minInterval: 0.035,
    render: (c, o, t) => {
      click(c, o, t, 2600, 1.2, 0.022, 0.32)
      tone(c, o, t, 'triangle', 340, 210, 0.07, 0.3)
    },
  },
  // Opponent move: same family, lower and duller, a touch quieter.
  moveOpponent: {
    dur: 0.09, minInterval: 0.035,
    render: (c, o, t) => {
      const lp = lowpass(c, o, 1800)
      click(c, lp, t, 1400, 1.0, 0.028, 0.3)
      tone(c, lp, t, 'triangle', 230, 150, 0.08, 0.3)
    },
  },
  // Capture: heavier knock with a second, sharper tick on top.
  capture: {
    dur: 0.13, minInterval: 0.04, priority: true,
    render: (c, o, t) => {
      click(c, o, t, 1700, 0.8, 0.035, 0.42)
      tone(c, o, t, 'sine', 200, 90, 0.12, 0.42)
      click(c, o, t + 0.018, 3200, 2.0, 0.02, 0.22)
    },
  },
  // Rejected move: two muffled, descending bumps.
  reject: {
    dur: 0.14, minInterval: 0.12, priority: true,
    render: (c, o, t) => {
      const lp = lowpass(c, o, 900)
      tone(c, lp, t, 'triangle', 190, 140, 0.06, 0.32)
      tone(c, lp, t + 0.065, 'triangle', 150, 105, 0.07, 0.32)
    },
  },
  // Check: two crisp rising knocks.
  check: {
    dur: 0.2, minInterval: 0.3, priority: true,
    render: (c, o, t) => {
      for (const [dt, f] of [[0, 880], [0.1, 1046]] as const) {
        tone(c, o, t + dt, 'sine', f, f * 0.96, 0.09, 0.2)
        click(c, o, t + dt, 3400, 3, 0.014, 0.16)
      }
    },
  },
  // Anti-check: two softer falling knocks.
  antiCheck: {
    dur: 0.2, minInterval: 0.3, priority: true,
    render: (c, o, t) => {
      for (const [dt, f] of [[0, 784], [0.1, 622]] as const) {
        tone(c, o, t + dt, 'sine', f, f * 0.96, 0.09, 0.18)
        click(c, o, t + dt, 2800, 3, 0.014, 0.12)
      }
    },
  },
  // A piece came off cooldown: barely-there high tick, coalesced.
  ready: {
    dur: 0.03, minInterval: 0.2, coalesce: true,
    render: (c, o, t) => {
      click(c, o, t, 5200, 4, 0.008, 0.1)
      tone(c, o, t, 'sine', 1760, 1760, 0.025, 0.045)
    },
  },
  gameStart: {
    dur: 0.3, minInterval: 0.5, priority: true,
    render: (c, o, t) => {
      mallet(c, o, t, 392, 0.14, 0.22)
      mallet(c, o, t + 0.07, 523, 0.14, 0.22)
      mallet(c, o, t + 0.14, 659, 0.16, 0.22)
    },
  },
  gameWin: {
    dur: 0.6, minInterval: 0.5, priority: true,
    render: (c, o, t) => {
      mallet(c, o, t, 523, 0.14, 0.22)
      mallet(c, o, t + 0.08, 659, 0.14, 0.22)
      mallet(c, o, t + 0.16, 784, 0.14, 0.22)
      mallet(c, o, t + 0.24, 1046, 0.34, 0.24)
    },
  },
  gameLoss: {
    dur: 0.55, minInterval: 0.5, priority: true,
    render: (c, o, t) => {
      const lp = lowpass(c, o, 1400)
      mallet(c, lp, t, 392, 0.18, 0.24)
      mallet(c, lp, t + 0.12, 330, 0.18, 0.24)
      mallet(c, lp, t + 0.24, 262, 0.3, 0.26)
    },
  },
  // Neutral end (spectators).
  gameEnd: {
    dur: 0.4, minInterval: 0.5, priority: true,
    render: (c, o, t) => {
      mallet(c, o, t, 523, 0.16, 0.22)
      mallet(c, o, t + 0.11, 392, 0.28, 0.22)
    },
  },
}

export const SOUND_NAMES = Object.keys(SOUNDS) as SoundName[]

// --- Engine ---

const MAX_VOICES = 6
const MASTER_GAIN = 1.2

let ctx: AudioContext | null = null
let master: GainNode | null = null
const lastPlayed = new Map<SoundName, number>()
const pendingCoalesced = new Map<SoundName, ReturnType<typeof setTimeout>>()
let voiceEnds: number[] = []

function applyMasterGain(): void {
  if (!ctx || !master) return
  const v = soundSettings.volume
  master.gain.setTargetAtTime(MASTER_GAIN * v * v, ctx.currentTime, 0.01)
}

function ensureContext(): void {
  try {
    if (!ctx) {
      const Ctor = window.AudioContext
        ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
      if (!Ctor) return
      ctx = new Ctor({ latencyHint: 'interactive' })
      // Gentle limiter so overlapping sounds can never clip.
      const limiter = ctx.createDynamicsCompressor()
      limiter.threshold.value = -6
      limiter.knee.value = 6
      limiter.ratio.value = 12
      limiter.attack.value = 0.002
      limiter.release.value = 0.1
      limiter.connect(ctx.destination)
      master = ctx.createGain()
      master.gain.value = 0
      master.connect(limiter)
      applyMasterGain()
    }
    if (ctx.state === 'suspended') void ctx.resume().catch(() => {})
  } catch {
    ctx = null
    master = null
  }
}

const UNLOCK_EVENTS = ['pointerdown', 'keydown', 'touchstart'] as const
let unlockInstalled = false

function onGesture(): void {
  ensureContext()
  if (ctx?.state === 'running') {
    UNLOCK_EVENTS.forEach((e) => window.removeEventListener(e, onGesture, true))
    unlockInstalled = false
  }
}

/** Create/resume the AudioContext on the first user gesture (idempotent). */
export function installAudioUnlock(): void {
  if (unlockInstalled || typeof window === 'undefined') return
  unlockInstalled = true
  UNLOCK_EVENTS.forEach((e) => window.addEventListener(e, onGesture, { capture: true, passive: true }))
}

// Dev-only event log for automated checks (nothing is exposed in production).
type DebugStatus = 'played' | 'muted' | 'locked' | 'throttled' | 'coalesced' | 'voice-limit' | 'error'
interface DebugEntry { name: SoundName; status: DebugStatus; at: number }
const debugLog: DebugEntry[] | null = import.meta.env.DEV ? [] : null
function debug(name: SoundName, status: DebugStatus): void {
  if (!debugLog) return
  debugLog.push({ name, status, at: Math.round(performance.now()) })
  if (debugLog.length > 500) debugLog.splice(0, debugLog.length - 500)
}

function render(name: SoundName): void {
  if (!ctx || !master || ctx.state !== 'running') return debug(name, 'locked')
  const def = SOUNDS[name]
  const now = ctx.currentTime
  voiceEnds = voiceEnds.filter((end) => end > now)
  if (voiceEnds.length >= MAX_VOICES && !def.priority) return debug(name, 'voice-limit')
  try {
    def.render(ctx, master, now + 0.005)
    voiceEnds.push(now + def.dur)
    lastPlayed.set(name, performance.now())
    debug(name, 'played')
  } catch {
    debug(name, 'error')
  }
}

/** Play a sound effect, subject to mute, rate limits and the voice limit. Never throws. */
export function playSound(name: SoundName): void {
  if (soundSettings.muted || soundSettings.volume <= 0) return debug(name, 'muted')
  const def = SOUNDS[name]
  const sinceMs = performance.now() - (lastPlayed.get(name) ?? -Infinity)
  const minMs = def.minInterval * 1000
  if (sinceMs >= minMs) return render(name)
  if (!def.coalesce) return debug(name, 'throttled')
  if (pendingCoalesced.has(name)) return debug(name, 'coalesced')
  debug(name, 'coalesced')
  pendingCoalesced.set(name, setTimeout(() => {
    pendingCoalesced.delete(name)
    if (!soundSettings.muted) render(name)
  }, minMs - sinceMs))
}

/** Render a sound offline and measure it (dev tooling for checking levels without ears). */
async function analyse(name: SoundName): Promise<{ duration: number; audible: number; peak: number; rms: number }> {
  const rate = 44100
  const len = Math.ceil(rate * (SOUNDS[name].dur + 0.3))
  const off = new OfflineAudioContext(1, len, rate)
  const gain = off.createGain()
  gain.gain.value = MASTER_GAIN * DEFAULT_VOLUME * DEFAULT_VOLUME
  gain.connect(off.destination)
  SOUNDS[name].render(off, gain, 0)
  const data = (await off.startRendering()).getChannelData(0)
  let peak = 0, sumSq = 0, lastAudible = 0
  for (let i = 0; i < data.length; i++) {
    const a = Math.abs(data[i])
    if (a > peak) peak = a
    if (a > 0.001) lastAudible = i
    sumSq += data[i] * data[i]
  }
  return { duration: len / rate, audible: lastAudible / rate, peak, rms: Math.sqrt(sumSq / data.length) }
}

if (import.meta.env.DEV && typeof window !== 'undefined') {
  (window as unknown as Record<string, unknown>).__chakesSound = {
    log: debugLog, play: playSound, analyse, names: SOUND_NAMES, settings: soundSettings,
  }
}
