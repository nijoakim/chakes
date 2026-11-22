const MAX_SQUARE_PX = 64
const PAGE_GUTTER_PX = 44
/**
 * Extra square-widths reserved for the slim rank-label gutter on the left of
 * the board (`--gutter` in ChakesBoard.vue).
 */
const LABEL_COLUMNS = 0.4

/**
 * Responsive square size (a CSS length) for a board `cols` squares wide.
 * Single source for the game board and anything that must line up with it.
 */
export function responsiveSquareSize(cols: number): string {
  return `min(${MAX_SQUARE_PX}px, calc((100vw - ${PAGE_GUTTER_PX}px) / ${cols + LABEL_COLUMNS}))`
}
