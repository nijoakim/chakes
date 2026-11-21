const MAX_SQUARE_PX = 64
const PAGE_GUTTER_PX = 44
/** Extra square-widths reserved for the rank-label columns on both sides of the board. */
const LABEL_COLUMNS = 2

/**
 * Responsive square size (a CSS length) for a board `cols` squares wide.
 * Single source for the game board and anything that must line up with it.
 */
export function responsiveSquareSize(cols: number): string {
  return `min(${MAX_SQUARE_PX}px, calc((100vw - ${PAGE_GUTTER_PX}px) / ${cols + LABEL_COLUMNS}))`
}
