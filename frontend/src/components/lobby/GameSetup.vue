<script setup lang="ts">
import { ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useCatalogStore } from '../../stores/catalog'
import { getPieceDefs, getInitialBoard } from '../../services/api'
import type { PieceDef, InitialBoardResponse, PieceInstance } from '../../services/api'
import PieceSprite from '../chess/PieceSprite.vue'

type Settings = { gameType: string; cooldowns: Record<string, number>; upsideDown: boolean; latencyHiding: boolean }

const props = defineProps<{ initialSettings?: Settings }>()

const emit = defineEmits<{ (e: 'start', payload: Settings): void }>()

const catalog = useCatalogStore()
const { gameTypes } = storeToRefs(catalog)

const selectedGameType = ref(props.initialSettings?.gameType ?? 'orthodox')
const upsideDown = ref(props.initialSettings?.upsideDown ?? false)
const latencyHiding = ref(false)
const currentPieceDefs = ref<PieceDef[]>([])
const initialBoard = ref<InitialBoardResponse | null>(null)

const initialAbsolute = props.initialSettings?.cooldowns ?? {}
const initialValues = Object.values(initialAbsolute)
const globalCooldown = ref(
  initialValues.length > 0
    ? Math.round(initialValues.reduce((a, b) => a + b, 0) / initialValues.length)
    : 3
)
const cooldownOffsets = ref<Record<string, number>>(
  Object.fromEntries(
    Object.entries(initialAbsolute).map(([name, v]) => [name, v - globalCooldown.value])
  )
)

function concreteCooldown(name: string): number {
  return Math.max(0, globalCooldown.value + (cooldownOffsets.value[name] ?? 0))
}

function setPieceCooldown(name: string, concrete: number) {
  cooldownOffsets.value[name] = concrete - globalCooldown.value
}

watch(selectedGameType, async (gameType) => {
  const [defs, board] = await Promise.all([getPieceDefs(gameType), getInitialBoard(gameType)])
  currentPieceDefs.value = [...defs].sort((a, b) => a.name.localeCompare(b.name))
  const prev = cooldownOffsets.value
  cooldownOffsets.value = Object.fromEntries(
    currentPieceDefs.value.map((p) => [p.name, prev[p.name] ?? 0])
  )
  initialBoard.value = board
}, { immediate: true })

function adjustBase(delta: number) {
  globalCooldown.value = Math.max(0, globalCooldown.value + delta)
}

function onStart() {
  emit('start', {
    gameType: selectedGameType.value,
    cooldowns: Object.fromEntries(
      currentPieceDefs.value.map((p) => [p.name, concreteCooldown(p.name)])
    ),
    upsideDown: upsideDown.value,
    latencyHiding: latencyHiding.value,
  })
}

function isLight(r: number, c: number): boolean {
  return (r + c) % 2 === 0
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
      <button @click="adjustBase(-1)">
        −
      </button>
      <span>Base cooldown: {{ globalCooldown }}s</span>
      <button @click="adjustBase(1)">
        +
      </button>
    </div>
    <table class="cooldown-table">
      <thead>
        <tr>
          <th />
          <th>Piece</th>
          <th>Cooldown (s)</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="p in currentPieceDefs"
          :key="p.name"
        >
          <td>
            <div class="piece-preview-pair">
              <div class="piece-preview light">
                <PieceSprite
                  :name="p.name"
                  color="white"
                />
              </div>
              <div class="piece-preview dark">
                <PieceSprite
                  :name="p.name"
                  color="black"
                />
              </div>
            </div>
          </td>
          <td>{{ p.name }}</td>
          <td>
            <input
              type="number"
              min="0"
              step="1"
              :value="concreteCooldown(p.name)"
              @change="setPieceCooldown(p.name, Number(($event.target as HTMLInputElement).value))"
            >
          </td>
        </tr>
      </tbody>
    </table>

    <div
      v-if="initialBoard"
      class="board-preview"
      :style="{ '--cols': initialBoard.size_x }"
    >
      <template
        v-for="(row, r) in initialBoard.board"
        :key="r"
      >
        <div
          v-for="(piece, c) in row"
          :key="c"
          class="mini-square"
          :class="isLight(r, c) ? 'light' : 'dark'"
        >
          <PieceSprite
            v-if="piece"
            :name="(piece as PieceInstance).name"
            :color="(piece as PieceInstance).owner"
          />
        </div>
      </template>
    </div>

    <label class="checkbox-label">
      <input
        v-model="upsideDown"
        type="checkbox"
      >
      Upside-down chess
    </label>
    <label class="checkbox-label">
      <input
        v-model="latencyHiding"
        type="checkbox"
      >
      Show moves immediately (latency hiding)
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
.piece-preview-pair {
  display: flex;
  gap: 2px;
  align-items: center;
}
.piece-preview {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 2px;
}
.piece-preview.light { background: #f0d9b5; }
.piece-preview.dark  { background: #b58863; }
.board-preview {
  display: grid;
  grid-template-columns: repeat(var(--cols), 1fr);
  gap: 0;
  border: 1px solid #888;
}
.mini-square {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.mini-square.light { background: #f0d9b5; }
.mini-square.dark  { background: #b58863; }
.checkbox-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  cursor: pointer;
}
</style>
