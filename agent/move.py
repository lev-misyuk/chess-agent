from enum import IntEnum, auto
from dataclasses import dataclass
from agent.square import Square

class MoveFlag(IntEnum):
    """Flags for special move types"""
    QUIET = auto()                  # Regular move
    DOUBLE_PAWN_PUSH = auto()       # Double pawn push
    KING_CASTLE = auto()            # Kingside castling
    QUEEN_CASTLE = auto()           # Queenside castling
    CAPTURE = auto()                # Regular capture
    EN_PASSANT = auto()             # En passant capture
    PROMOTION_N = auto()            # Promotion to knight
    PROMOTION_B = auto()            # Promotion to bishop
    PROMOTION_R = auto()            # Promotion to rook
    PROMOTION_Q = auto()            # Promotion to queen
    PROMOTION_CAPTURE_N = auto()    # Capture and promote to knight
    PROMOTION_CAPTURE_B = auto()    # Capture and promote to bishop
    PROMOTION_CAPTURE_R = auto()    # Capture and promote to rook
    PROMOTION_CAPTURE_Q = auto()    # Capture and promote to queen

@dataclass
class Move:
    """Represents a chess move"""
    from_square: Square
    to_square: Square
    flag: MoveFlag = MoveFlag.QUIET

    @property
    def is_capture(self) -> bool:
        """Check if the move is a capture"""
        return self.flag in (
            MoveFlag.CAPTURE,
            MoveFlag.EN_PASSANT,
            MoveFlag.PROMOTION_CAPTURE_B,
            MoveFlag.PROMOTION_CAPTURE_N,
            MoveFlag.PROMOTION_CAPTURE_Q,
            MoveFlag.PROMOTION_CAPTURE_R
        )

    @property
    def is_promotion(self) -> bool:
        """Check if the move is a promotion"""
        return self.flag in (
            MoveFlag.PROMOTION_N,
            MoveFlag.PROMOTION_B,
            MoveFlag.PROMOTION_R,
            MoveFlag.PROMOTION_Q,
            MoveFlag.PROMOTION_CAPTURE_N,
            MoveFlag.PROMOTION_CAPTURE_B,
            MoveFlag.PROMOTION_CAPTURE_R,
            MoveFlag.PROMOTION_CAPTURE_Q
        )

    @property
    def is_castling(self) -> bool:
        """Check if the move is a castling move"""
        return self.flag in (MoveFlag.KING_CASTLE, MoveFlag.QUEEN_CASTLE)

    def get_promotion_piece(self) -> str:
        """Get the promotion piece type"""
        promotion_pieces = {
            MoveFlag.PROMOTION_N: 'N',
            MoveFlag.PROMOTION_B: 'B',
            MoveFlag.PROMOTION_R: 'R',
            MoveFlag.PROMOTION_Q: 'Q',
            MoveFlag.PROMOTION_CAPTURE_N: 'N',
            MoveFlag.PROMOTION_CAPTURE_B: 'B',
            MoveFlag.PROMOTION_CAPTURE_R: 'R',
            MoveFlag.PROMOTION_CAPTURE_Q: 'Q'
        }
        return promotion_pieces.get(self.flag, '')

    def __str__(self) -> str:
        """Convert move to UCI notation"""
        move_str = f"{self.from_square.notation}{self.to_square.notation}"
        if self.is_promotion:
            move_str += self.get_promotion_piece().lower()
        return move_str

    @classmethod
    def from_uci(cls, uci: str) -> 'Move':
        """Create a Move from UCI notation"""
        if not (len(uci) in {4, 5} and 
                'a' <= uci[0] <= 'h' and 
                '1' <= uci[1] <= '8' and
                'a' <= uci[2] <= 'h' and 
                '1' <= uci[3] <= '8'):
            raise ValueError(f"Invalid UCI notation: {uci}")

        from_square = Square.from_notation(uci[:2])
        to_square = Square.from_notation(uci[2:4])

        flag = MoveFlag.QUIET
        if len(uci) == 5:
            promotion_flags = {
                'n': MoveFlag.PROMOTION_N,
                'b': MoveFlag.PROMOTION_B,
                'r': MoveFlag.PROMOTION_R,
                'q': MoveFlag.PROMOTION_Q
            }
            flag = promotion_flags.get(uci[4].lower())
            if flag is None:
                raise ValueError(f"Invalid promotion piece: {uci[4]}")

        return cls(from_square, to_square, flag)
