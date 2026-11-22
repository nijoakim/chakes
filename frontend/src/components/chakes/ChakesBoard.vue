<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, shallowRef, watch } from 'vue'
import BoardGrid from '@/components/board/BoardGrid.vue'
import ChakesSquare, { type CaptureGhost, type MoveMark } from './ChakesSquare.vue'
import type { Color, Cooldowns } from '@/services/types'
import type { DisplayBoard, DisplayPiece, SideFlags } from '@/chakes/types'
import { isLightSquare, sameSquare, squareKey, type Square } from '@/chakes/square'
import { orientedSquares } from '@/chakes/orientation'
import { responsiveSquareSize } from '@/chakes/boardSize'
import { diffBoards, type BoardMove } from '@/chakes/moveDiff'
import type { RecentMove } from '@/composables/useRecentMoves'

// Coordinate label alphabet: a-z, A-Z, then Greek α-ω (76 total, covers up to 64 columns)
const FILE_LABELS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZαβγδεζηθικλμνξοπρστυφχψω'

/** Piece slide duration: quick enough never to feel like input lag. */
const SLIDE_MS = 130
/** Matches the `capture-out` animation in ChakesSquare. */
const GHOST_MS = 200

const props = defineProps<{
  board: DisplayBoard
  cooldowns: Cooldowns
  maxCooldowns: Record<string, number>
  /** Side the board is viewed from (spectators pass 'white'). */
  viewer: Color
  selected: Square | null
  /** null: the selection's legal moves are not known yet (nothing highlighted). */
  legalMoves: ReadonlySet<string> | null
  rejectedSquares: Set<string>
  /** Moves to highlight (see useRecentMoves); later entries win on a shared square. */
  recentMoves?: readonly RecentMove[]
  inCheck?: SideFlags
  inAntiCheck?: SideFlags
  /** A change of game id means a new game: its board is not animated as moves. */
  gameId?: string | null
}>()

const emit = defineEmits<{
  (e: 'squareClick', square: Square): void
  (e: 'squareRightClick', square: Square, event: MouseEvent): void
}>()

const rows = computed(() => props.board.length)
const cols = computed(() => props.board[0]?.length ?? 0)

// Display-ordered grid of board-space squares; every lookup below is in board space.
const squares = computed(() => orientedSquares(rows.value, cols.value, props.viewer))

const fileLabels = computed(() => (squares.value[0] ?? []).map(([, c]) => FILE_LABELS[c] ?? '?'))
const rankLabels = computed(() => squares.value.map(([[r]]) => String(r + 1)))
// Files sit on the edge nearest rank 1, which is the bottom unless viewing as black.
const fileLabelsOnBottom = computed(() => props.viewer !== 'black')

function pieceAt([r, c]: Square) {
  return props.board[r]?.[c] ?? null
}

// --- Last-move highlights ---

const moveMarks = computed(() => {
  const marks = new Map<string, MoveMark>()
  for (const m of props.recentMoves ?? []) {
    marks.set(squareKey(m.from), { id: m.id, own: m.own, to: false })
    marks.set(squareKey(m.to), { id: m.id, own: m.own, to: true })
  }
  return marks
})

// --- Check indication ---

// The engine's check is about the 'King'; its anti-check is about the
// 'Anti-King' (which must stay attacked) — see engine.is_in_anti_check.
function alertAt(sq: Square): 'check' | 'anti-check' | null {
  const p = pieceAt(sq)
  if (!p) return null
  if (p.name === 'King' && props.inCheck?.[p.owner]) return 'check'
  if (p.name === 'Anti-King' && props.inAntiCheck?.[p.owner]) return 'anti-check'
  return null
}

// --- Piece motion ---

// Pieces are rendered inside their squares, and the grid simply re-renders
// when a new board arrives, so a move would teleport. Instead the displayed
// board (authoritative + optimistic overlay) is diffed on every change and
// each moved piece is FLIP-animated: it is already in its destination square
// in the DOM (so state, hit-testing and clicks are exact from the first
// frame) and a short compositor-only transform makes it appear to slide in
// from its source. Because the diff is of the *displayed* board:
//  - an optimistic move slides when it is made; the server's confirmation
//    leaves the displayed board unchanged, so nothing replays;
//  - a rejected optimistic move changes the displayed board back, so the piece
//    slides home.
// Captured pieces get a brief ghost that fades out under the arriving piece.

const rootRef = ref<HTMLElement | null>(null)
const ghosts = shallowRef(new Map<string, CaptureGhost>())
let ghostId = 1
const ghostTimers = new Set<ReturnType<typeof setTimeout>>()

function reducedMotion(): boolean {
  return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false
}

function squareEl(sq: Square): HTMLElement | null {
  return rootRef.value?.querySelector<HTMLElement>(`[data-sq="${squareKey(sq)}"]`) ?? null
}

function slide({ from, to }: BoardMove): void {
  const fromEl = squareEl(from)
  const toEl = squareEl(to)
  const piece = toEl?.querySelector<HTMLElement>('.square-piece')
  if (!fromEl || !toEl || !piece) return
  const a = fromEl.getBoundingClientRect()
  const b = toEl.getBoundingClientRect()
  const dx = a.left - b.left
  const dy = a.top - b.top
  if (dx === 0 && dy === 0) return
  piece.getAnimations().forEach((anim) => { if (anim.id === 'slide') anim.cancel() })
  // Lift above neighbouring squares' pieces and cooldown bars while moving.
  // Vue never binds `style` on the sprite, so this inline write is ours alone.
  piece.style.zIndex = '5'
  const anim = piece.animate(
    [{ transform: `translate(${dx}px, ${dy}px)` }, { transform: 'translate(0, 0)' }],
    { duration: SLIDE_MS, easing: 'cubic-bezier(0.25, 0.8, 0.35, 1)', id: 'slide' },
  )
  const done = () => { piece.style.zIndex = '' }
  anim.onfinish = done
  anim.oncancel = done
}

function addGhosts(removed: { square: Square; piece: DisplayPiece }[]): void {
  if (removed.length === 0) return
  const next = new Map(ghosts.value)
  const added: Array<[string, number]> = []
  for (const { square, piece } of removed) {
    const key = squareKey(square)
    const id = ghostId++
    next.set(key, { id, piece })
    added.push([key, id])
  }
  ghosts.value = next
  const timer = setTimeout(() => {
    ghostTimers.delete(timer)
    const m = new Map(ghosts.value)
    for (const [key, id] of added) if (m.get(key)?.id === id) m.delete(key)
    ghosts.value = m
  }, GHOST_MS)
  ghostTimers.add(timer)
}

watch(
  () => [props.board, props.gameId] as const,
  ([next, game], [prev, prevGame]) => {
    if (game !== prevGame || reducedMotion()) return
    const diff = diffBoards(prev, next)
    if (!diff) return
    addGhosts(diff.removed)
    if (diff.moves.length === 0) return
    // Once this flush has rendered the new board (and the ghosts).
    void nextTick(() => diff.moves.forEach(slide))
  },
)

onBeforeUnmount(() => {
  ghostTimers.forEach(clearTimeout)
  ghostTimers.clear()
})
</script>

<template>
  <!-- Rank labels in a slim gutter on the left, file labels in a slim gutter
       on the edge nearest rank 1. No mirror spacers on the other sides. -->
  <div
    ref="rootRef"
    class="board-with-labels"
    :class="{ 'files-top': !fileLabelsOnBottom }"
    :style="{ '--sq': responsiveSquareSize(cols || 8) }"
  >
    <div class="rank-labels">
      <div
        v-for="(label, r) in rankLabels"
        :key="r"
        class="rank-label"
      >
        {{ label }}
      </div>
    </div>
    <BoardGrid
      v-slot="{ cell: sq }"
      class="grid"
      :cells="squares"
    >
      <ChakesSquare
        :data-sq="squareKey(sq)"
        :piece="pieceAt(sq)"
        :is-light="isLightSquare(sq)"
        :is-selected="sameSquare(selected, sq)"
        :is-legal-move="legalMoves?.has(squareKey(sq)) ?? false"
        :is-rejected="rejectedSquares.has(squareKey(sq))"
        :cooldown="cooldowns[sq[0]]?.[sq[1]] ?? 0"
        :max-cooldown="maxCooldowns[pieceAt(sq)?.name ?? ''] ?? 1"
        :move-mark="moveMarks.get(squareKey(sq)) ?? null"
        :ghost="ghosts.get(squareKey(sq)) ?? null"
        :alert="alertAt(sq)"
        @click="emit('squareClick', sq)"
        @right-click="emit('squareRightClick', sq, $event)"
      />
    </BoardGrid>
    <div class="file-labels">
      <div
        v-for="(label, c) in fileLabels"
        :key="c"
        class="file-label"
      >
        {{ label }}
      </div>
    </div>
  </div>
</template>

<style scoped>
/* The 0.4 must match LABEL_COLUMNS in chakes/boardSize.ts. */
.board-with-labels {
  --gutter: calc(var(--sq) * 0.4);
  --border-w: 2px; /* BoardGrid's border, so labels line up with squares */
  display: inline-grid;
  grid-template-columns: var(--gutter) auto;
  grid-template-areas:
    'ranks board'
    '.     files';
}
.board-with-labels.files-top {
  grid-template-areas:
    '.     files'
    'ranks board';
}
.grid { grid-area: board; }
.rank-labels {
  grid-area: ranks;
  display: flex;
  flex-direction: column;
  padding-block: var(--border-w);
}
.file-labels {
  grid-area: files;
  display: flex;
  padding-inline: var(--border-w);
}
.rank-label,
.file-label {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: max(9px, calc(var(--sq) * 0.28));
  font-weight: 600;
  line-height: 1;
  color: var(--board-label);
  user-select: none;
}
.rank-label {
  width: var(--gutter);
  height: var(--sq);
}
.file-label {
  width: var(--sq);
  height: var(--gutter);
}
</style>
