<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  (e: 'create', desiredName: string | undefined): void
  (e: 'join', name: string): void
}>()

const input = ref('')

function onCreate() {
  emit('create', input.value.trim() || undefined)
}

function onJoin() {
  const trimmed = input.value.trim()
  if (trimmed) emit('join', trimmed)
}
</script>

<template>
  <div class="lobby">
    <button @click="onCreate">
      Create lobby
    </button>
    <div class="join">
      <input
        v-model="input"
        placeholder="Lobby name"
        @keyup.enter="onJoin"
      >
      <button @click="onJoin">
        Join lobby
      </button>
    </div>
  </div>
</template>

<style scoped>
.lobby {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: center;
}
.join {
  display: flex;
  gap: 8px;
}
</style>
