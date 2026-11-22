<script setup lang="ts">
import { computed } from 'vue'
import type { Role } from '@/services/types'
import PieceSprite from '@/components/chakes/PieceSprite.vue'
import ShareLink from './ShareLink.vue'

/** Pre-game screen for everyone except the host. */
const props = defineProps<{ role: Role; url: string }>()

const heading = computed(() => {
  if (props.role === 'white') return 'You are playing White'
  if (props.role === 'black') return 'You are playing Black'
  return 'You are spectating'
})
</script>

<template>
  <div class="waiting-room">
    <div
      class="identity"
      aria-hidden="true"
    >
      <PieceSprite
        name="King"
        :color="role === 'spectator' ? 'white' : role"
      />
    </div>
    <h2>{{ heading }}</h2>
    <p
      class="waiting"
      role="status"
    >
      <span
        class="spinner"
        aria-hidden="true"
      />
      The host is choosing the game settings&hellip;
    </p>
    <p class="hint">
      The board appears here as soon as the game starts.
      <template v-if="role === 'spectator'">
        Both seats are taken, so you will watch from White's side.
      </template>
    </p>
    <div class="share">
      <span class="share-label">Invite others to watch with this link</span>
      <ShareLink :url="url" />
    </div>
  </div>
</template>

<style scoped>
.waiting-room {
  width: min(460px, 100%);
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 28px 24px 22px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface);
  box-shadow: var(--shadow);
}
.identity {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  /* A board square's colour keeps either side's piece legible in both themes. */
  background: var(--board-light);
  border: 1px solid var(--border-strong);
}
.identity :deep(.piece-img) {
  width: 48px;
  height: 48px;
}
h2 {
  margin: 4px 0 0;
}
.waiting {
  font-size: 16px;
  text-wrap: balance;
  color: var(--text-h);
}
.spinner {
  display: inline-block;
  vertical-align: -2px;
  margin-right: 8px;
  box-sizing: border-box;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid var(--accent-border);
  border-top-color: var(--accent);
  animation: spin 0.9s linear infinite;
}
.hint {
  font-size: 14px;
  color: var(--text);
  text-wrap: balance;
}
.share {
  width: 100%;
  margin-top: 8px;
  padding-top: 14px;
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 6px;
  text-align: left;
}
.share-label {
  font-size: 13px;
  color: var(--text);
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
@media (prefers-reduced-motion: reduce) {
  .spinner { animation: none; }
}
</style>
