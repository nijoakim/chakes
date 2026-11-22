<!--
  PieceMoveDiagram — a small board with a white piece in the centre and every
  square it can reach marked, as measured by the backend from the engine's
  piece definition (/api/piece-guide). White moves up the board.

  Marker shape says what the piece may do on a square (move and capture /
  move only / capture only); a tinted square means the move is a slide that a
  piece in the way can block, an untinted one a step or leap.
-->

<script setup lang="ts">
import { computed } from 'vue'
import type { GuideSquare, PieceGuide } from '@/services/catalogTypes'
import { isLightSquare, type Square } from '@/chakes/square'
import BoardGrid from '@/components/board/BoardGrid.vue'
import BoardSquare from '@/components/board/BoardSquare.vue'
import PieceSprite from '@/components/chakes/PieceSprite.vue'
import MoveMarker, { type MarkerKind } from './MoveMarker.vue'

const props = withDefaults(defineProps<{
  guide: PieceGuide
  /** Width of the diagram board in px; squares scale to fit. */
  boardSize?: number
}>(), { boardSize: 189 })

const movement = computed(() => props.guide.movement)

// Crop to the squares the piece can reach (plus a one-square margin), so
// short-range pieces are drawn larger. Never smaller than 5x5.
const radius = computed(() => {
  const { origin, size, squares, hurdles } = movement.value
  let r = 1
  for (const s of [...squares, ...hurdles]) {
    r = Math.max(r, Math.abs(s.x - origin.x), Math.abs(s.y - origin.y))
  }
  const maxR = Math.min(origin.x, origin.y, size - 1 - origin.x, size - 1 - origin.y)
  return Math.min(maxR, r + 1)
})
// Display order: white's forward direction (+y) points up.
const cells = computed<Square[][]>(() => {
  const { x: ox, y: oy } = movement.value.origin
  const R = radius.value
  return Array.from({ length: 2 * R + 1 }, (_, i) =>
    Array.from({ length: 2 * R + 1 }, (_, j): Square => [oy + R - i, ox - R + j]),
  )
})
const squareSize = computed(() => `${Math.floor(props.boardSize / (2 * radius.value + 1))}px`)

const byKey = computed(() => {
  const map = new Map<string, GuideSquare>()
  for (const s of movement.value.squares) map.set(`${s.x},${s.y}`, s)
  return map
})
const hurdleKeys = computed(() => new Set(movement.value.hurdles.map((h) => `${h.x},${h.y}`)))

function squareAt(r: number, c: number): GuideSquare | undefined {
  return byKey.value.get(`${c},${r}`)
}
function isOrigin(r: number, c: number): boolean {
  return movement.value.origin.x === c && movement.value.origin.y === r
}

function markerKind(s: GuideSquare): MarkerKind {
  if (s.move && s.capture) return 'both'
  if (s.move) return 'move'
  return 'capture'
}

const squares = computed(() => movement.value.squares)
const has = computed(() => ({
  both: squares.value.some((s) => s.move && s.capture),
  move: squares.value.some((s) => s.move && !s.capture),
  capture: squares.value.some((s) => s.capture && !s.move),
  initial: squares.value.some((s) => s.initial),
  friend: squares.value.some((s) => s.friend),
  ride: squares.value.some((s) => s.ride),
  leap: squares.value.some((s) => !s.ride && !s.hop),
  hop: movement.value.hurdles.length > 0,
}))

/** Plain-language summary for screen readers (the diagram itself is visual). */
const summary = computed(() => {
  const s = squares.value
  const parts: string[] = [`${s.length} reachable squares from the centre of an empty board`]
  const rides = s.filter((q) => q.ride).length
  const leaps = s.filter((q) => !q.ride && !q.hop).length
  if (rides) parts.push(`${rides} along slides that can be blocked`)
  if (leaps) parts.push(`${leaps} by steps or leaps that cannot be blocked`)
  const moveOnly = s.filter((q) => q.move && !q.capture).length
  const captureOnly = s.filter((q) => q.capture && !q.move).length
  if (moveOnly) parts.push(`${moveOnly} for moving only`)
  if (captureOnly) parts.push(`${captureOnly} for capturing only`)
  if (has.value.initial) parts.push('some only on its first move')
  if (has.value.friend) parts.push('it can capture its own pieces')
  if (has.value.hop) parts.push('it must jump over a piece to move')
  return `How the ${props.guide.name} moves: ${parts.join('; ')}.`
})
</script>

<template>
  <div class="piece-move-diagram">
    <BoardGrid
      v-slot="{ cell: [r, c] }"
      class="diagram-board"
      :cells="cells"
      :square-size="squareSize"
      role="img"
      :aria-label="summary"
    >
      <BoardSquare :light="isLightSquare([r, c])">
        <PieceSprite
          v-if="isOrigin(r, c)"
          :name="guide.name"
          color="white"
        />
        <span
          v-else-if="hurdleKeys.has(`${c},${r}`)"
          class="hurdle"
        />
        <template v-else-if="squareAt(r, c)">
          <span
            v-if="squareAt(r, c)!.ride"
            class="ride-tint"
          />
          <MoveMarker
            :kind="markerKind(squareAt(r, c)!)"
            :initial="squareAt(r, c)!.initial"
            :friend="squareAt(r, c)!.friend"
          />
        </template>
      </BoardSquare>
    </BoardGrid>

    <div class="side">
      <ul
        class="legend"
        aria-hidden="true"
      >
        <li v-if="has.both">
          <span class="swatch"><MoveMarker kind="both" /></span>Moves or captures
        </li>
        <li v-if="has.move">
          <span class="swatch"><MoveMarker kind="move" /></span>Moves only, no capture
        </li>
        <li v-if="has.capture">
          <span class="swatch"><MoveMarker kind="capture" /></span>Captures only
        </li>
        <li v-if="has.initial">
          <span class="swatch"><MoveMarker
            kind="move"
            initial
          /></span>Only on its first move
        </li>
        <li v-if="has.friend">
          <span class="swatch"><MoveMarker
            kind="move"
            friend
          /></span>May capture your own piece
        </li>
        <li v-if="has.ride">
          <span class="swatch"><span class="ride-tint" /></span>Slides: blocked by pieces in the way
        </li>
        <li v-if="has.leap">
          <span class="swatch" />Steps or leaps: can't be blocked
        </li>
        <li v-if="has.hop">
          <span class="swatch"><span class="hurdle" /></span>Example piece to jump over
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.piece-move-diagram {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 16px;
  align-items: flex-start;
}
.diagram-board {
  flex: none;
  border-width: 1px;
}
.ride-tint {
  position: absolute;
  inset: 0;
  background: rgba(15, 118, 110, 0.42);
  pointer-events: none;
}
.hurdle {
  width: 56%;
  height: 56%;
  border-radius: 3px;
  background: #6b7378;
  box-shadow: inset 0 0 0 2px rgba(0, 0, 0, 0.25);
}
.side {
  flex: 1;
  min-width: 140px;
  font-size: 13px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.legend {
  list-style: none;
  margin: 0;
  padding: 0;
  font-size: 13px;
  line-height: 1.3;
  color: var(--text);
  display: grid;
  gap: 5px;
}
.legend li {
  display: flex;
  align-items: center;
  gap: 8px;
}
.swatch {
  position: relative;
  flex: none;
  width: 18px;
  height: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--board-light);
  border-radius: 2px;
  box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.12);
}
</style>
