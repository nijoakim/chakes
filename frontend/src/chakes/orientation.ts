import type { Color } from '@/services/types'
import type { Square } from './square'

// Board-space grids have row 0 = rank 1 (white's back rank). Display convention:
// white sees rank N at the top; black sees rank 1 at the top with mirrored files.

/** Reorder a board-space grid into display order for the given viewer. */
export function orientGrid<T>(grid: readonly (readonly T[])[], viewer: Color): T[][] {
  if (viewer === 'black') return grid.map((row) => [...row].reverse())
  return [...grid].reverse().map((row) => [...row])
}

/** Map a display coordinate back to board space. */
export function displayToBoard(
  displayR: number,
  displayC: number,
  rows: number,
  cols: number,
  viewer: Color,
): Square {
  if (viewer === 'black') return [displayR, cols - 1 - displayC]
  return [rows - 1 - displayR, displayC]
}

/** Display-ordered grid of the board-space square under each display cell. */
export function orientedSquares(rows: number, cols: number, viewer: Color): Square[][] {
  return Array.from({ length: rows }, (_, dr) =>
    Array.from({ length: cols }, (_, dc) => displayToBoard(dr, dc, rows, cols, viewer)),
  )
}
