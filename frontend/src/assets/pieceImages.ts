// Orthodox — white
import wKing   from './white/king.svg'
import wQueen  from './white/queen.svg'
import wRook   from './white/rook.svg'
import wBishop from './white/bishop.svg'
import wKnight from './white/knight.svg'
import wPawn   from './white/pawn.svg'
// Fairy — white
import wAntiKing    from './white/anti-king.svg'
import wAntiPawn    from './white/anti-pawn.svg'
import wAntiQueen   from './white/anti-queen.svg'
import wAmazon      from './white/amazon.svg'
import wChancellor  from './white/chancellor.svg'
import wCommoner    from './white/commoner.svg'
import wDragon      from './white/dragon.svg'
import wFool        from './white/fool.svg'
import wShip        from './white/ship.svg'
import wZebra       from './white/zebra.svg'
// Orthodox — black
import bKing   from './black/king.svg'
import bQueen  from './black/queen.svg'
import bRook   from './black/rook.svg'
import bBishop from './black/bishop.svg'
import bKnight from './black/knight.svg'
import bPawn   from './black/pawn.svg'
// Fairy — black
import bAntiKing    from './black/anti-king.svg'
import bAntiPawn    from './black/anti-pawn.svg'
import bAntiQueen   from './black/anti-queen.svg'
import bAmazon      from './black/amazon.svg'
import bChancellor  from './black/chancellor.svg'
import bCommoner    from './black/commoner.svg'
import bDragon      from './black/dragon.svg'
import bFool        from './black/fool.svg'
import bShip        from './black/ship.svg'
import bZebra       from './black/zebra.svg'

export type PieceImages = { white: string; black: string }

// Maps piece name to { white: svgUrl, black: svgUrl }.
// Pieces without an entry fall back to displaying their name as text.
export const pieceImages: Partial<Record<string, PieceImages>> = {
  // Orthodox
  King:            { white: wKing,   black: bKing   },
  Queen:           { white: wQueen,  black: bQueen  },
  Rook:            { white: wRook,   black: bRook   },
  Bishop:          { white: wBishop, black: bBishop },
  Knight:          { white: wKnight, black: bKnight },
  Pawn:            { white: wPawn,   black: bPawn   },
  // Fairy
  Amazon:          { white: wAmazon,     black: bAmazon     }, // A = Amazon = Q+N
  'Anti-King':     { white: wFool,       black: bFool       }, // Fool = seeks check
  'Berolina Pawn': { white: wAntiPawn,   black: bAntiPawn   }, // h = pawn variant
  Camel:           { white: wZebra,      black: bZebra      }, // Z = extended leaper family
  Chameleon:       { white: wDragon,     black: bDragon     }, // D = multi-mode piece
  Ferz:            { white: wAntiKing,   black: bAntiKing   }, // f = Ferz in Wikimedia
  Grasshopper:     { white: wAntiQueen,  black: bAntiQueen  }, // g = Grasshopper
  Man:             { white: wCommoner,   black: bCommoner   }, // x = Commoner = non-royal king
  Nightrider:      { white: wChancellor, black: bChancellor }, // c = Chancellor, knight-based
  Wazir:           { white: wShip,       black: bShip       }, // s = Ship, orthogonal mover
}
