<script setup lang="ts">
import { ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useCatalogStore } from '../../stores/catalog'

type Settings = { gameType: string; cooldowns: Record<string, number>; upsideDown: boolean }

const props = defineProps<{ initialSettings?: Settings }>()

const emit = defineEmits<{ (e: 'start', payload: Settings): void }>()

const catalog = useCatalogStore()
const { pieceDefs, gameTypes } = storeToRefs(catalog)

const selectedGameType = ref(props.initialSettings?.gameType ?? 'orthodox')
const upsideDown = ref(props.initialSettings?.upsideDown ?? false)
const cooldownSettings = ref<Record<string, number>>(props.initialSettings?.cooldowns ?? {})

watch(pieceDefs, (defs) => {
  if (props.initialSettings) return
  cooldownSettings.value = Object.fromEntries(
    defs.map((p) => [p.name, p.default_cooldown])
  )
}, { immediate: true })

function adjustAll(delta: number) {
  for (const name in cooldownSettings.value) {
    cooldownSettings.value[name] = Math.max(0, cooldownSettings.value[name] + delta)
  }
}

function onStart() {
  emit('start', {
    gameType: selectedGameType.value,
    cooldowns: cooldownSettings.value,
    upsideDown: upsideDown.value,
  })
}
</script>

<template>
  <div class="game-setup">
    <div class="game-type-picker">
      <label
        v-for="gt in gameTypes"
        :key="gt.id"
        :class="{ active: selectedGameType === gt.id }"
      >
        <input
          v-model="selectedGameType"
          type="radio"
          :value="gt.id"
        >
        {{ gt.name }}
      </label>
    </div>
    <div class="cooldown-all">
      <button @click="adjustAll(-1)">
        −
      </button>
      <span>All cooldowns</span>
      <button @click="adjustAll(1)">
        +
      </button>
    </div>
    <table class="cooldown-table">
      <thead>
        <tr>
          <th>Piece</th>
          <th>Cooldown (s)</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="p in pieceDefs"
          :key="p.name"
        >
          <td>{{ p.name }}</td>
          <td>
            <input
              v-model.number="cooldownSettings[p.name]"
              type="number"
              min="0"
              step="1"
            >
          </td>
        </tr>
      </tbody>
    </table>
    <label class="checkbox-label">
      <input
        v-model="upsideDown"
        type="checkbox"
      >
      Upside-down chess
    </label>
    <button @click="onStart">
      Start game
    </button>
  </div>
</template>

<style scoped>
.game-setup {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: center;
  padding: 24px;
}
.game-type-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: center;
}
.game-type-picker label {
  padding: 4px 10px;
  border: 1px solid #aaa;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}
.game-type-picker label.active {
  border-color: #333;
  font-weight: bold;
  background: #f0f0f0;
}
.game-type-picker input[type=radio] {
  display: none;
}
.cooldown-all {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
}
.cooldown-table {
  border-collapse: collapse;
  font-size: 14px;
}
.cooldown-table th,
.cooldown-table td {
  padding: 4px 10px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}
.cooldown-table input[type=number] {
  width: 60px;
}
.checkbox-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  cursor: pointer;
}
</style>
