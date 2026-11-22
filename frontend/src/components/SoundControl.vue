<script setup lang="ts">
import { computed } from 'vue'
import { playSound, soundSettings } from '@/services/sound'

const muted = computed(() => soundSettings.muted || soundSettings.volume <= 0)
const percent = computed(() => Math.round(soundSettings.volume * 100))

function toggleMute(): void {
  if (soundSettings.volume <= 0) {
    soundSettings.volume = 0.5
    soundSettings.muted = false
  } else {
    soundSettings.muted = !soundSettings.muted
  }
  if (!soundSettings.muted) playSound('moveOwn')
}

function onVolume(e: Event): void {
  soundSettings.volume = Number((e.target as HTMLInputElement).value) / 100
  if (soundSettings.volume > 0) soundSettings.muted = false
}

// Preview the level once the slider is released, not on every step.
function onVolumeCommit(): void {
  playSound('moveOwn')
}
</script>

<template>
  <div
    class="sound-control"
    role="group"
    aria-label="Sound"
  >
    <button
      type="button"
      class="mute-btn"
      :aria-pressed="muted"
      aria-label="Mute sounds"
      :title="muted ? 'Sounds off' : 'Sounds on'"
      @click="toggleMute"
    >
      <svg
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          class="speaker"
          d="M3 9h4l5-4.5v15L7 15H3z"
        />
        <template v-if="muted">
          <path
            class="wave"
            d="M16 9.5l5 5M21 9.5l-5 5"
          />
        </template>
        <template v-else>
          <path
            class="wave"
            d="M15.5 8.5a5 5 0 0 1 0 7"
          />
          <path
            v-if="soundSettings.volume > 0.5"
            class="wave"
            d="M18.5 5.5a9 9 0 0 1 0 13"
          />
        </template>
      </svg>
    </button>
    <input
      class="volume"
      type="range"
      min="0"
      max="100"
      step="5"
      :value="percent"
      aria-label="Sound volume"
      :aria-valuetext="`${percent}%`"
      :class="{ dimmed: soundSettings.muted }"
      @input="onVolume"
      @change="onVolumeCommit"
    >
  </div>
</template>

<style scoped>
.sound-control {
  position: fixed;
  left: 12px;
  bottom: 12px;
  z-index: 50;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px 3px 3px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--surface);
  color: var(--text);
  box-shadow: var(--shadow);
}
.mute-btn {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: var(--text-h);
  cursor: pointer;
}
.mute-btn:hover {
  background: var(--surface-hover);
}
.mute-btn:focus-visible,
.volume:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
.mute-btn[aria-pressed='true'] {
  color: var(--text);
}
svg {
  width: 22px;
  height: 22px;
}
.speaker {
  fill: currentColor;
}
.wave {
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
}
.volume {
  width: 72px;
  margin: 0;
  accent-color: var(--accent);
  cursor: pointer;
}
.volume.dimmed {
  opacity: 0.45;
}
</style>

<!-- Unscoped: on narrow screens the game-setup's sticky start bar occupies the
     bottom edge, so lift the control above it rather than covering its text. -->
<style>
@media (max-width: 860px) {
  body:has(.start-bar) .sound-control {
    bottom: calc(76px + env(safe-area-inset-bottom));
  }
}
</style>
