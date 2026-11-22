<script setup lang="ts">
import { ref, watch, computed, nextTick } from 'vue'
import { storeToRefs } from 'pinia'
import { useCatalogStore } from '@/stores/catalog'
import { getPieceDefs } from '@/services/api'
import { getSetupPreview } from '@/services/catalogApi'
import type { PieceDef, InitialBoardResponse } from '@/services/types'
import type { GameSettings } from '@/chakes/types'
import { isLightSquare } from '@/chakes/square'
import { orientedSquares } from '@/chakes/orientation'
import BoardGrid from '@/components/board/BoardGrid.vue'
import BoardSquare from '@/components/board/BoardSquare.vue'
import PieceSprite from '@/components/chakes/PieceSprite.vue'
import PieceMoveDiagram from './PieceMoveDiagram.vue'

const props = defineProps<{ initialSettings?: GameSettings }>()

const emit = defineEmits<{ (e: 'start', payload: GameSettings): void }>()

const catalog = useCatalogStore()
const { gameTypes, optionDescriptions, pieceGuides } = storeToRefs(catalog)

const ORTHODOX_PIECES = new Set(['Pawn', 'Rook', 'Knight', 'Bishop', 'Queen', 'King'])
const DEFAULT_BASE_COOLDOWN = 3
const MAX_COOLDOWN = 99

const selectedGameType = ref(props.initialSettings?.gameType ?? 'orthodox')
const upsideDown = ref(props.initialSettings?.upsideDown ?? false)
const currentPieceDefs = ref<PieceDef[]>([])
const initialBoard = ref<InitialBoardResponse | null>(null)

const initialAbsolute = props.initialSettings?.cooldowns ?? {}
const initialValues = Object.values(initialAbsolute)
const globalCooldown = ref(
  initialValues.length > 0
    ? Math.round(initialValues.reduce((a, b) => a + b, 0) / initialValues.length)
    : DEFAULT_BASE_COOLDOWN
)
const cooldownOffsets = ref<Record<string, number>>(
  Object.fromEntries(
    Object.entries(initialAbsolute).map(([name, v]) => [name, v - globalCooldown.value])
  )
)

function clampCooldown(v: number): number {
  return Math.min(MAX_COOLDOWN, Math.max(0, Math.round(v)))
}

function concreteCooldown(name: string): number {
  return Math.max(0, globalCooldown.value + (cooldownOffsets.value[name] ?? 0))
}

function setPieceCooldown(name: string, concrete: number) {
  cooldownOffsets.value[name] = concrete - globalCooldown.value
}

function onCooldownInput(name: string, event: Event) {
  const input = event.target as HTMLInputElement
  const parsed = input.value.trim() === '' ? NaN : Number(input.value)
  if (Number.isFinite(parsed)) setPieceCooldown(name, clampCooldown(parsed))
  // Always show the value actually in effect (reverts empty / invalid input).
  input.value = String(concreteCooldown(name))
}

function isOverride(name: string): boolean {
  return (cooldownOffsets.value[name] ?? 0) !== 0
}

function resetPiece(name: string) {
  cooldownOffsets.value[name] = 0
}

function formatOffset(name: string): string {
  const d = concreteCooldown(name) - globalCooldown.value
  return d > 0 ? `+${d}` : `−${-d}`
}

let fetchSeq = 0
watch([selectedGameType, upsideDown], async ([gameType, flipped]) => {
  const seq = ++fetchSeq
  const [defs, board] = await Promise.all([getPieceDefs(gameType), getSetupPreview(gameType, flipped)])
  if (seq !== fetchSeq) return // a newer selection superseded this one
  currentPieceDefs.value = [...defs].sort((a, b) => a.name.localeCompare(b.name))
  const prev = cooldownOffsets.value
  cooldownOffsets.value = Object.fromEntries(
    currentPieceDefs.value.map((p) => [p.name, prev[p.name] ?? 0])
  )
  initialBoard.value = board
}, { immediate: true })

function adjustBase(delta: number) {
  globalCooldown.value = Math.min(MAX_COOLDOWN, Math.max(0, globalCooldown.value + delta))
}

/** Engine defaults: base = their average, each piece offset to its own default. */
function resetCooldowns() {
  const defs = currentPieceDefs.value
  const base = defs.length
    ? Math.round(defs.reduce((a, p) => a + p.default_cooldown, 0) / defs.length)
    : DEFAULT_BASE_COOLDOWN
  globalCooldown.value = base
  cooldownOffsets.value = Object.fromEntries(defs.map((p) => [p.name, p.default_cooldown - base]))
}

const cooldownsAreDefault = computed(() => {
  const defs = currentPieceDefs.value
  return defs.every((p) => concreteCooldown(p.name) === p.default_cooldown)
    && Object.values(cooldownOffsets.value).every((o) => o === 0)
})

const overrideCount = computed(() => currentPieceDefs.value.filter((p) => isOverride(p.name)).length)

function onStart() {
  emit('start', {
    gameType: selectedGameType.value,
    cooldowns: Object.fromEntries(
      currentPieceDefs.value.map((p) => [p.name, concreteCooldown(p.name)])
    ),
    upsideDown: upsideDown.value,
  })
}

// --- Descriptions ---------------------------------------------------------

const selectedGameTypeInfo = computed(() => gameTypes.value.find((gt) => gt.id === selectedGameType.value))

// --- Preview --------------------------------------------------------------

// Preview is shown from white's side.
const previewSquares = computed(() => {
  const b = initialBoard.value?.board
  return b ? orientedSquares(b.length, b[0]?.length ?? 0, 'white') : null
})
const previewCols = computed(() => initialBoard.value?.size_x ?? 8)
const previewSquareSize = computed(() => {
  const max = previewCols.value > 8 ? 30 : 32
  return `min(${max}px, calc((100vw - 56px) / ${previewCols.value}))`
})

// --- Piece guide ----------------------------------------------------------

const guidePiece = ref<string | null>(null)
const guideCard = ref<HTMLElement | null>(null)

const currentGuides = computed(() => pieceGuides.value[selectedGameType.value] ?? [])
const selectedGuide = computed(() => currentGuides.value.find((g) => g.name === guidePiece.value) ?? null)
const guideError = ref(false)

watch(selectedGameType, async (gameType) => {
  guideError.value = false
  try {
    await catalog.loadPieceGuide(gameType)
  } catch {
    guideError.value = true
  }
}, { immediate: true })

// Keep a valid selection: default to the variant's signature (non-orthodox) piece.
watch(currentPieceDefs, (defs) => {
  if (guidePiece.value && defs.some((p) => p.name === guidePiece.value)) return
  guidePiece.value = defs.find((p) => !ORTHODOX_PIECES.has(p.name))?.name
    ?? defs.find((p) => p.name === 'Knight')?.name
    ?? defs[0]?.name
    ?? null
})

function showGuide(name: string) {
  guidePiece.value = name
  // In the single-column layout the guide may be off screen.
  if (window.matchMedia('(max-width: 860px)').matches) {
    void nextTick(() => guideCard.value?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }))
  }
}

function isFairy(name: string): boolean {
  return !ORTHODOX_PIECES.has(name)
}

const summary = computed(() => {
  const parts = [selectedGameTypeInfo.value?.name ?? selectedGameType.value, `${globalCooldown.value}s base cooldown`]
  if (overrideCount.value) parts.push(`${overrideCount.value} custom`)
  if (upsideDown.value) parts.push('upside-down')
  return parts.join(' · ')
})
</script>

<template>
  <div class="game-setup">
    <div class="setup-columns">
      <div class="col col-settings">
        <section
          class="card variant-card"
          aria-labelledby="setup-variant-heading"
        >
          <h2 id="setup-variant-heading">
            Variant
          </h2>
          <div
            class="game-type-picker"
            role="radiogroup"
            aria-labelledby="setup-variant-heading"
          >
            <label
              v-for="gt in gameTypes"
              :key="gt.id"
              :class="{ active: selectedGameType === gt.id }"
            >
              <input
                v-model="selectedGameType"
                type="radio"
                name="setup-game-type"
                :value="gt.id"
              >
              {{ gt.name }}
            </label>
          </div>
          <p
            v-if="selectedGameTypeInfo?.description"
            class="description"
            aria-live="polite"
          >
            {{ selectedGameTypeInfo.description }}
          </p>

          <div class="option">
            <label class="checkbox-label">
              <input
                v-model="upsideDown"
                type="checkbox"
                aria-describedby="setup-upside-down-desc"
              >
              Upside-down chess
            </label>
            <p
              v-if="optionDescriptions.upside_down"
              id="setup-upside-down-desc"
              class="description small"
            >
              {{ optionDescriptions.upside_down }}
            </p>
          </div>
        </section>

        <section
          class="card cooldown-card"
          aria-labelledby="setup-cooldown-heading"
        >
          <div class="card-head">
            <h2 id="setup-cooldown-heading">
              Cooldowns
            </h2>
            <button
              class="reset-btn"
              :disabled="cooldownsAreDefault"
              @click="resetCooldowns"
            >
              Reset cooldowns
            </button>
          </div>
          <p
            v-if="optionDescriptions.cooldown"
            class="description small"
          >
            {{ optionDescriptions.cooldown }}
          </p>
          <div class="base-row">
            <div class="cooldown-all">
              <button
                class="step-btn"
                aria-label="Decrease base cooldown"
                :disabled="globalCooldown <= 0"
                @click="adjustBase(-1)"
              >
                −
              </button>
              <span class="cooldown-value">Base cooldown: <strong>{{ globalCooldown }}s</strong></span>
              <button
                class="step-btn"
                aria-label="Increase base cooldown"
                :disabled="globalCooldown >= MAX_COOLDOWN"
                @click="adjustBase(1)"
              >
                +
              </button>
            </div>
            <p class="hint">
              Pieces follow the base unless you set their own value below.
            </p>
          </div>
          <table class="cooldown-table">
            <thead>
              <tr>
                <th scope="col">
                  Piece <span class="th-hint">· select to see moves</span>
                </th>
                <th scope="col">
                  Cooldown
                </th>
                <th scope="col">
                  <span class="visually-hidden">Override</span>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="p in currentPieceDefs"
                :key="p.name"
                :class="{ override: isOverride(p.name), selected: guidePiece === p.name }"
              >
                <td>
                  <button
                    class="piece-btn"
                    :aria-pressed="guidePiece === p.name"
                    :title="`Show how the ${p.name} moves`"
                    @click="showGuide(p.name)"
                  >
                    <span
                      class="piece-preview-pair"
                      aria-hidden="true"
                    >
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
                    </span>
                    <span class="piece-name">{{ p.name }}</span>
                    <span
                      v-if="isFairy(p.name)"
                      class="fairy-tag"
                    >fairy</span>
                  </button>
                </td>
                <td>
                  <span class="cooldown-input">
                    <input
                      type="number"
                      min="0"
                      :max="MAX_COOLDOWN"
                      step="1"
                      inputmode="numeric"
                      :aria-label="`${p.name} cooldown in seconds`"
                      :value="concreteCooldown(p.name)"
                      @change="onCooldownInput(p.name, $event)"
                    >
                    <span aria-hidden="true">s</span>
                  </span>
                </td>
                <td class="override-cell">
                  <template v-if="isOverride(p.name)">
                    <span
                      class="offset-badge"
                      :title="`${formatOffset(p.name)}s compared to the base cooldown`"
                    >{{ formatOffset(p.name) }}</span>
                    <button
                      class="icon-btn"
                      :aria-label="`Reset ${p.name} to the base cooldown`"
                      :title="`Reset ${p.name} to the base cooldown`"
                      @click="resetPiece(p.name)"
                    >
                      ↺
                    </button>
                  </template>
                  <span
                    v-else
                    class="base-tag"
                  >base</span>
                </td>
              </tr>
            </tbody>
          </table>
        </section>
      </div>

      <div class="col col-board">
        <section
          class="card preview-card"
          aria-labelledby="setup-preview-heading"
        >
          <div class="card-head">
            <h2 id="setup-preview-heading">
              Starting position
            </h2>
            <span class="hint">Tap a piece to see how it moves</span>
          </div>
          <BoardGrid
            v-if="previewSquares && initialBoard"
            v-slot="{ cell: [r, c] }"
            class="board-preview"
            :cells="previewSquares"
            :square-size="previewSquareSize"
          >
            <BoardSquare
              :light="isLightSquare([r, c])"
              :selected="!!guidePiece && initialBoard.board[r]?.[c]?.name === guidePiece"
            >
              <button
                v-if="initialBoard.board[r]?.[c]"
                class="preview-piece"
                tabindex="-1"
                :aria-label="`${initialBoard.board[r][c]!.owner} ${initialBoard.board[r][c]!.name}: show how it moves`"
                @click="showGuide(initialBoard.board[r][c]!.name)"
              >
                <PieceSprite
                  :name="initialBoard.board[r][c]!.name"
                  :color="initialBoard.board[r][c]!.owner"
                />
              </button>
            </BoardSquare>
          </BoardGrid>
        </section>

        <section
          ref="guideCard"
          class="card guide-card"
          aria-labelledby="setup-guide-heading"
          aria-live="polite"
        >
          <h2 id="setup-guide-heading">
            <template v-if="selectedGuide">
              How the {{ selectedGuide.name }} moves
            </template>
            <template v-else>
              Piece guide
            </template>
          </h2>
          <template v-if="selectedGuide">
            <PieceMoveDiagram
              :guide="selectedGuide"
              :board-size="168"
            />
            <p
              v-if="selectedGuide.notes"
              class="description small notes"
            >
              {{ selectedGuide.notes }}
            </p>
          </template>
          <p
            v-else
            class="description small"
          >
            {{ guideError ? 'The piece guide could not be loaded.' : 'Loading…' }}
          </p>
        </section>
      </div>
    </div>

    <div class="start-bar">
      <span class="summary">{{ summary }}</span>
      <button
        class="primary start-btn"
        @click="onStart"
      >
        Start game
      </button>
    </div>
  </div>
</template>

<style scoped>
.game-setup {
  width: 100%;
  max-width: 1180px;
  box-sizing: border-box;
  padding: 0 20px;
  text-align: left;
}
.setup-columns {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}
.col {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}
.col-settings {
  flex: 1 1 0;
}
.col-board {
  flex: none;
  width: 400px;
}
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: calc(var(--radius) + 4px);
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.card h2 {
  font-size: 15px;
  margin: 0;
  letter-spacing: 0;
}
.card-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
}
.game-setup p {
  line-height: 1.45;
}
.description {
  font-size: 14px;
  line-height: 1.45;
  color: var(--text);
}
.description.small,
.hint {
  font-size: 13px;
}
.hint {
  color: var(--text);
}
.base-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 12px;
}
.base-row .hint {
  flex: 1 1 14em;
}
.notes {
  border-top: 1px solid var(--border);
  padding-top: 8px;
}
.cooldown-table tr.selected td:first-child {
  box-shadow: inset 3px 0 0 var(--accent);
}

/* Variant pills */
.game-type-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
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
.option {
  border-top: 1px solid var(--border);
  padding-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-h);
  cursor: pointer;
}

/* Cooldowns */
.reset-btn {
  font-size: 13px;
  padding: 4px 10px;
}
.cooldown-all {
  display: flex;
  flex: none;
  align-items: center;
  gap: 4px;
  padding: 4px;
  font-size: 14px;
  border: 1px solid var(--border);
  border-radius: calc(var(--radius) + 4px);
  background: var(--code-bg);
}
.cooldown-value {
  min-width: 9.5em;
  text-align: center;
  color: var(--text);
}
.cooldown-value strong {
  color: var(--text-h);
  font-variant-numeric: tabular-nums;
}
.step-btn {
  width: 30px;
  height: 30px;
  padding: 0;
  font-size: 18px;
  line-height: 1;
}
.cooldown-table {
  border-collapse: collapse;
  font-size: 14px;
  width: 100%;
}
.cooldown-table th {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text);
  text-align: left;
}
.th-hint {
  text-transform: none;
  letter-spacing: 0;
  font-weight: 400;
}
.cooldown-table th,
.cooldown-table td {
  padding: 2px 6px;
  border-bottom: 1px solid var(--border);
}
.cooldown-table td {
  color: var(--text-h);
}
.cooldown-table tr.selected td {
  background: var(--accent-bg);
}
.piece-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 1px 4px;
  border: none;
  background: transparent;
  font-weight: 500;
  text-align: left;
}
.piece-btn:hover {
  background: transparent;
}
.piece-btn[aria-pressed='true'] {
  color: var(--accent);
  font-weight: 600;
}
.piece-preview-pair {
  display: flex;
  gap: 2px;
  align-items: center;
}
.piece-preview {
  --sq: 24px;
  border-radius: 2px;
}
.fairy-tag,
.base-tag,
.offset-badge {
  font-size: 11px;
  line-height: 1.5;
  padding: 0 6px;
  border-radius: 999px;
  white-space: nowrap;
}
.fairy-tag {
  border: 1px solid var(--accent-border);
  color: var(--accent);
  font-weight: 600;
}
.base-tag {
  color: var(--text);
  opacity: 0.7;
}
.cooldown-input {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--text);
}
.cooldown-table input[type=number] {
  width: 60px;
  padding: 2px 8px;
  line-height: 1.3;
  font-size: 14px;
  font-variant-numeric: tabular-nums;
}
tr.override input[type=number] {
  border-color: var(--accent);
  background: var(--accent-bg);
  font-weight: 700;
}
.override-cell {
  white-space: nowrap;
  width: 74px;
  text-align: right;
}
.offset-badge {
  background: var(--accent);
  color: var(--accent-fg);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.icon-btn {
  margin-left: 4px;
  width: 26px;
  height: 26px;
  padding: 0;
  font-size: 15px;
  line-height: 1;
}

/* Preview */
.board-preview {
  align-self: center;
  border-width: 1px;
}
.preview-piece {
  all: unset;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

/* Start bar: always reachable, sticks to the bottom of the viewport when the
   setup is taller than the screen. */
.start-bar {
  position: sticky;
  bottom: 0;
  z-index: 2;
  margin-top: 16px;
  padding: 10px 0;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 16px;
  background: var(--bg);
  border-top: 1px solid var(--border);
}
.summary {
  font-size: 14px;
  color: var(--text);
  min-width: 0;
}
.start-btn {
  padding: 10px 32px;
  font-size: 17px;
  flex: none;
}
.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}

/* Single column on narrow screens: variant, board, guide, then cooldowns. */
@media (max-width: 860px) {
  .game-setup {
    padding: 0;
  }
  .setup-columns {
    flex-direction: column;
    align-items: stretch;
  }
  .col {
    display: contents;
  }
  .variant-card { order: 1; }
  .preview-card { order: 2; }
  .guide-card { order: 3; }
  .cooldown-card { order: 4; }
  .start-bar {
    padding: 10px 0 calc(10px + env(safe-area-inset-bottom));
  }
  .summary {
    font-size: 13px;
  }
  .start-btn {
    padding: 10px 22px;
  }
  .th-hint {
    display: none;
  }
}
</style>
