<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ rtt: number | null }>()

const color = computed(() => {
  if (props.rtt === null) return 'var(--text)'
  if (props.rtt < 150) return '#4caf50'
  if (props.rtt < 500) return '#ffc107'
  return '#f44336'
})
const label = computed(() => (props.rtt === null ? '— ms' : `${Math.round(props.rtt)} ms`))
</script>

<template>
  <div
    class="rtt-badge"
    :style="{ color }"
  >
    {{ label }}
  </div>
</template>

<style scoped>
.rtt-badge {
  width: 5em;
  font-size: 11px;
  font-family: monospace;
  opacity: 0.8;
}
</style>
