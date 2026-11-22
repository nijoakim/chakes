<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useCatalogStore } from '@/stores/catalog'
import { getPieceDefs, getInitialBoard } from '@/services/api'
import type { PieceDef, InitialBoardResponse } from '@/services/types'
import type { GameSettings } from '@/chakes/types'
import { isLightSquare } from '@/chakes/square'
import { orientedSquares } from '@/chakes/orientation'
import BoardGrid from '@/components/board/BoardGrid.vue'
import BoardSquare from '@/components/board/BoardSquare.vue'
import PieceSprite from '@/components/chakes/PieceSprite.vue'

const props = defineProps<{ initialSettings?: GameSettings }>()

const emit = defineEmits<{ (e: 'start', payload: GameSettings): void }>()

const catalog = useCatalogStore()
const { gameTypes } = storeToRefs(catalog)

const selectedGameType = ref(props.initialSettings?.gameType ?? 'orthodox')
const upsideDown = ref(props.initialSettings?.upsideDown ?? false)
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

watch([selectedGameType, upsideDown], async ([gameType, flipped]) => {
  const [defs, board] = await Promise.all([getPieceDefs(gameType), getInitialBoard(gameType, flipped)])
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
  })
}

// Preview is shown from white's side.
const previewSquares = computed(() => {
  const b = initialBoard.value?.board
  return b ? orientedSquares(b.length, b[0]?.length ?? 0, 'white') : null
})
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
      <button
        class="step-btn"
        aria-label="Decrease base cooldown"
        @click="adjustBase(-1)"
      >
        −
      </button>
      <span class="cooldown-value">Base cooldown: <strong>{{ globalCooldown }}s</strong></span>
      <button
        class="step-btn"
        aria-label="Increase base cooldown"
        @click="adjustBase(1)"
      >
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
              <BoardSquare
                class="piece-preview"
                light
              >
                <PieceSprite
                  :name="p.name"
                  color="white"
                />
              </BoardSquare>
              <BoardSquare
                class="piece-preview"
                :light="false"
              >
                <PieceSprite
                  :name="p.name"
                  color="black"
                />
              </BoardSquare>
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

    <BoardGrid
      v-if="previewSquares && initialBoard"
      v-slot="{ cell: [r, c] }"
      class="board-preview"
      :cells="previewSquares"
      square-size="32px"
    >
      <BoardSquare :light="isLightSquare([r, c])">
        <PieceSprite
          v-if="initialBoard.board[r]?.[c]"
          :name="initialBoard.board[r][c]!.name"
          :color="initialBoard.board[r][c]!.owner"
        />
      </BoardSquare>
    </BoardGrid>

    <label class="checkbox-label">
      <input
        v-model="upsideDown"
        type="checkbox"
      >
      Upside-down chess
    </label>
    <button
      class="primary start-btn"
      @click="onStart"
    >
      Start game
    </button>
  </div>
</template>

<style scoped>
.game-setup {
  display: flex;
  flex-direction: column;
  gap: 14px;
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
  padding: 5px 12px;
  border: 1px solid var(--border-strong);
  border-radius: 999px;
  background: var(--surface);
  cursor: pointer;
  font-size: 14px;
  color: var(--text-h);
  transition: background-color 0.12s, border-color 0.12s;
}
.game-type-picker label:hover {
  border-color: var(--accent-border);
}
.game-type-picker label.active {
  border-color: var(--accent);
  font-weight: 600;
  color: var(--accent);
  background: var(--accent-bg);
}
.game-type-picker label:has(input:focus-visible) {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
.game-type-picker input[type=radio] {
  /* Visually hidden but still keyboard-focusable. */
  position: absolute;
  opacity: 0;
  width: 1px;
  height: 1px;
  pointer-events: none;
}
.cooldown-all {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px;
  font-size: 14px;
  border: 1px solid var(--border);
  border-radius: calc(var(--radius) + 4px);
  background: var(--code-bg);
}
.cooldown-value {
  min-width: 11em;
  color: var(--text);
}
.cooldown-value strong {
  color: var(--text-h);
  font-variant-numeric: tabular-nums;
}
.step-btn {
  width: 32px;
  height: 32px;
  padding: 0;
  font-size: 18px;
  line-height: 1;
}
.cooldown-table {
  border-collapse: collapse;
  font-size: 14px;
}
.cooldown-table th {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text);
}
.cooldown-table th,
.cooldown-table td {
  padding: 4px 10px;
  text-align: left;
  border-bottom: 1px solid var(--border);
}
.cooldown-table td {
  color: var(--text-h);
}
.cooldown-table input[type=number] {
  width: 64px;
  padding: 4px 8px;
  font-size: 14px;
  font-variant-numeric: tabular-nums;
}
.piece-preview-pair {
  display: flex;
  gap: 2px;
  align-items: center;
}
.piece-preview {
  --sq: 28px;
  border-radius: 2px;
}
.board-preview {
  border-width: 1px;
}
.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--text-h);
  cursor: pointer;
}
.start-btn {
  margin-top: 4px;
  padding: 10px 32px;
  font-size: 17px;
}
</style>
