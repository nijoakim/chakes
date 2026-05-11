<script setup lang="ts">
import { computed } from 'vue'
import { pieceImages } from '../../assets/pieceImages'
import type { Color } from '../../services/api'

const props = defineProps<{
  name: string
  color: Color
  pending?: boolean
}>()

const src = computed(() => pieceImages[props.name]?.[props.color])
</script>

<template>
  <img
    v-if="src"
    :src="src"
    class="piece-img"
    :class="{ pending }"
    :alt="name"
  >
  <span
    v-else
    class="piece-text"
    :class="{ pending }"
  >{{ name }}</span>
</template>

<style scoped>
.piece-img {
  width: 90%;
  height: 90%;
  pointer-events: none;
  user-select: none;
  display: block;
}
.piece-text {
  font-size: 0.75rem;
  text-align: center;
  font-weight: bold;
  pointer-events: none;
  user-select: none;
}
.pending {
  opacity: 0.6;
  animation: pending-pulse 1s ease-in-out infinite alternate;
}
@keyframes pending-pulse {
  from { opacity: 0.55; }
  to   { opacity: 0.75; }
}
</style>
