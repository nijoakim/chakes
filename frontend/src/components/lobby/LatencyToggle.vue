<script setup lang="ts">
const enabled = defineModel<boolean>({ required: true })
</script>

<template>
  <label
    class="latency-toggle"
    title="Show your moves immediately, before the server confirms them"
  >
    <input
      v-model="enabled"
      type="checkbox"
    >
    latency hiding
  </label>
</template>

<style scoped>
.latency-toggle {
  font-size: 11px;
  font-family: monospace;
  opacity: 0.8;
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
}
</style>
