import type { WirePos } from '@/services/types'

/**
 * A board coordinate as [row, col] in board space: row 0 is white's back rank
 * (rank 1), col 0 is the a-file. This is the only coordinate form used inside
 * the client; wire {x, y} positions are converted at the socket/API boundary.
 */
export type Square = readonly [row: number, col: number]

/** Stable string key for a square, for use in Sets and Records. */
export function squareKey([r, c]: Square): string {
  return `${r},${c}`
}

export function sameSquare(a: Square | null, b: Square | null): boolean {
  return a !== null && b !== null && a[0] === b[0] && a[1] === b[1]
}

export function toWire([r, c]: Square): WirePos {
  return { x: c, y: r }
}

export function fromWire({ x, y }: WirePos): Square {
  return [y, x]
}

/** Parse the backend's "x,y" legal-move key. */
export function fromWireKey(key: string): Square {
  const [x, y] = key.split(',').map(Number)
  return fromWire({ x, y })
}

/** Backend legal-move destinations arrive as [x, y] tuples. */
export function fromWireTuple([x, y]: readonly number[]): Square {
  return fromWire({ x, y })
}

/** Chess convention: a1 (row 0, col 0) is dark. */
export function isLightSquare([r, c]: Square): boolean {
  return (r + c) % 2 === 1
}
