<script setup lang="ts">
import { computed } from 'vue'
import { pieceImages } from '../../assets/pieceImages'
import type { Color } from '../../services/api'

const props = defineProps<{
  name: string
  color: Color
}>()

const src = computed(() => pieceImages[props.name]?.[props.color])
</script>

<template>
  <img
    v-if="src"
    :src="src"
    class="piece-img"
    :alt="name"
  >
  <span
    v-else
    class="piece-text"
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
</style>
