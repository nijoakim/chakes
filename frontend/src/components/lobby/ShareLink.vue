<script setup lang="ts">
import { onUnmounted, ref } from 'vue'

const props = defineProps<{ url: string }>()

const COPIED_FEEDBACK_MS = 1500
const copied = ref(false)
let copiedTimer: ReturnType<typeof setTimeout> | undefined

async function copy() {
  try {
    await navigator.clipboard.writeText(props.url)
  } catch {
    return // clipboard unavailable (e.g. insecure context or permission denied)
  }
  copied.value = true
  clearTimeout(copiedTimer)
  copiedTimer = setTimeout(() => { copied.value = false }, COPIED_FEEDBACK_MS)
}

function selectAll(e: Event) {
  (e.target as HTMLInputElement).select()
}

onUnmounted(() => clearTimeout(copiedTimer))
</script>

<template>
  <div class="share-link">
    <input
      class="share-url"
      type="text"
      readonly
      :value="url"
      aria-label="Lobby link"
      @focus="selectAll"
    >
    <button
      type="button"
      :class="{ copied }"
      @click="copy"
    >
      {{ copied ? 'Copied' : 'Copy' }}
    </button>
    <span
      class="visually-hidden"
      aria-live="polite"
    >{{ copied ? 'Lobby link copied' : '' }}</span>
  </div>
</template>

<style scoped>
.share-link {
  display: flex;
  gap: 6px;
  width: 100%;
}
.share-url {
  flex: 1;
  min-width: 0;
  font-family: var(--mono);
  font-size: 13px;
  color: var(--text);
}
.share-link button {
  min-width: 5.5em;
}
.share-link button.copied {
  border-color: var(--accent);
  color: var(--accent);
}
.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}
</style>
