from agent.board import Board

class Evaluation:
    """Class for evaluating chess positions using various heuristics"""

    # Material values in centipawns
    PIECE_VALUES = {
        'P': 100,   # Pawn
        'N': 320,   # Knight
        'B': 330,   # Bishop
        'R': 500,   # Rook
        'Q': 900,   # Queen
        'K': 20000  # King
    }

    # Combine all piece-square tables into a single dictionary for faster lookup
    PIECE_SQUARE_TABLES = {
        'P': [
            0,   0,   0,   0,   0,   0,   0,   0,
            50,  50,  50,  50,  50,  50,  50,  50,
            10,  10,  20,  30,  30,  20,  10,  10,
            5,   5,   10,  25,  25,  10,  5,   5,
            0,   0,   0,   20,  20,  0,   0,   0,
            5,  -5,  -10,  0,   0,  -10,  -5,  5,
            5,   10,  10,  -20, -20, 10,  10,  5,
            0,   0,   0,   0,   0,   0,   0,   0
        ],
        'N': [
            -50, -40, -30, -30, -30, -30, -40, -50,
            -40, -20,  0,   0,   0,   0,  -20, -40,
            -30,  0,   10,  15,  15,  10,  0,  -30,
            -30,  5,   15,  20,  20,  15,  5,  -30,
            -30,  0,   15,  20,  20,  15,  0,  -30,
            -30,  5,   10,  15,  15,  10,  5,  -30,
            -40, -20,  0,   5,   5,   0,  -20, -40,
            -50, -40, -30, -30, -30, -30, -40, -50
        ],
        'B': [
        -20, -10, -10, -10, -10, -10, -10, -20,
        -10,  0,   0,   0,   0,   0,   0,  -10,
        -10,  0,   5,   10,  10,  5,   0,  -10,
        -10,  5,   5,   10,  10,  5,   5,  -10,
        -10,  0,   10,  10,  10,  10,  0,  -10,
        -10,  10,  10,  10,  10,  10,  10, -10,
        -10,  5,   0,   0,   0,   0,   5,  -10,
        -20, -10, -10, -10, -10, -10, -10, -20
        ],
        'R': [
        0,   0,   0,   0,   0,   0,   0,   0,
        5,   10,  10,  10,  10,  10,  10,  5,
        -5,  0,   0,   0,   0,   0,   0,  -5,
        -5,  0,   0,   0,   0,   0,   0,  -5,
        -5,  0,   0,   0,   0,   0,   0,  -5,
        -5,  0,   0,   0,   0,   0,   0,  -5,
        -5,  0,   0,   0,   0,   0,   0,  -5,
        0,   0,   0,   5,   5,   0,   0,   0
        ],
        'Q': [
        -20, -10, -10, -5,  -5,  -10, -10, -20,
        -10,  0,   0,   0,   0,   0,   0,  -10,
        -10,  0,   5,   5,   5,   5,   0,  -10,
        -5,   0,   5,   5,   5,   5,   0,   -5,
        0,    0,   5,   5,   5,   5,   0,   -5,
        -10,  5,   5,   5,   5,   5,   0,  -10,
        -10,  0,   5,   0,   0,   0,   0,  -10,
        -20, -10, -10, -5,  -5,  -10, -10, -20
        ],
        'K': [
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -20, -30, -30, -40, -40, -30, -30, -20,
        -10, -20, -20, -20, -20, -20, -20, -10,
        20,   20,  0,   0,   0,   0,   20,  20,
        20,   30,  10,  0,   0,   10,  30,  20
        ]
    }

    # Precomputed bitboard masks for common operations
    FILE_MASKS = [0x0101010101010101 << i for i in range(8)]
    RANK_MASKS = [0xFF << (8 * i) for i in range(8)]

    KING_ENDGAME_TABLE = [
        -50, -40, -30, -20, -20, -30, -40, -50,
        -30, -20, -10,  0,   0,  -10, -20, -30,
        -30, -10,  20,  30,  30,  20, -10, -30,
        -30, -10,  30,  40,  40,  30, -10, -30,
        -30, -10,  30,  40,  40,  30, -10, -30,
        -30, -10,  20,  30,  30,  20, -10, -30,
        -30, -30,  0,   0,   0,   0,  -30, -30,
        -50, -30, -30, -30, -30, -30, -30, -50
    ]

    # Penalties and bonuses in centipawns
    DOUBLED_PAWN_PENALTY = -10
    ISOLATED_PAWN_PENALTY = -20
    BACKWARD_PAWN_PENALTY = -15
    PASSED_PAWN_BONUS = 20
    ROOK_OPEN_FILE_BONUS = 15
    ROOK_SEMI_OPEN_FILE_BONUS = 10
    BISHOP_PAIR_BONUS = 30
    KNIGHT_OUTPOST_BONUS = 15
    KING_SHIELD_BONUS = 10

    # Additional tactical evaluation constants
    PINNED_PIECE_PENALTY = -30
    DISCOVERED_ATTACK_BONUS = 25
    HANGING_PIECE_PENALTY = -35
    EXCHANGE_BONUS = 15
    PROTECTED_PIECE_BONUS = 10

    # Mobility bonuses (per legal move)
    MOBILITY_BONUS = {
        'N': 4,   # Knight
        'B': 5,   # Bishop
        'R': 3,   # Rook
        'Q': 2    # Queen
    }

    def __init__(self, board: Board):
        self.board = board
        self.score = 0

        # Bitboard caches
        self.white_pieces = (self.board.white_pawns | self.board.white_knights | 
                           self.board.white_bishops | self.board.white_rooks | 
                           self.board.white_queens | self.board.white_king)
        self.black_pieces = (self.board.black_pawns | self.board.black_knights | 
                           self.board.black_bishops | self.board.black_rooks | 
                           self.board.black_queens | self.board.black_king)
        self.all_pieces = self.white_pieces | self.black_pieces

        # Cache piece counts for faster material counting
        self.piece_counts = {
            'white_pawns': bin(self.board.white_pawns).count('1'),
            'white_knights': bin(self.board.white_knights).count('1'),
            'white_bishops': bin(self.board.white_bishops).count('1'),
            'white_rooks': bin(self.board.white_rooks).count('1'),
            'white_queens': bin(self.board.white_queens).count('1'),
            'black_pawns': bin(self.board.black_pawns).count('1'),
            'black_knights': bin(self.board.black_knights).count('1'),
            'black_bishops': bin(self.board.black_bishops).count('1'),
            'black_rooks': bin(self.board.black_rooks).count('1'),
            'black_queens': bin(self.board.black_queens).count('1')
        }

        # Pre-calculate game phase
        self.is_endgame = self._is_endgame()

    def _is_endgame(self) -> bool:
        """Simplified and faster endgame detection"""
        return (self.piece_counts['white_queens'] + self.piece_counts['black_queens'] == 0 or
                (self.piece_counts['white_queens'] + self.piece_counts['black_queens'] == 1 and
                 self.piece_counts['white_rooks'] + self.piece_counts['black_rooks'] <= 1))

    def evaluate(self) -> int:
        """Ultra-fast position evaluation"""
        # Quick checkmate/stalemate detection
        if self.board.is_checkmate():
            return -20000 if self.board.white_to_move else 20000
        if self.board.is_stalemate():
            return 0
        
        self.score = self._evaluate_material()

        # Only do detailed evaluation if not in a clearly won/lost position
        if -2000 <= self.score <= 2000:
            self.score += self._evaluate_position()

            # Mobility evaluation only in complex positions
            if not self.is_endgame:
                mob_score = self._evaluate_mobility()
                self.score += mob_score

            # Add tempo bonus
            self.score += 10 if self.board.white_to_move else -10

        return self.score

    def _evaluate_material(self) -> int:
        """Fast material evaluation using cached piece counts"""
        score = 0
        score += self.piece_counts['white_pawns'] * self.PIECE_VALUES['P']
        score += self.piece_counts['white_knights'] * self.PIECE_VALUES['N']
        score += self.piece_counts['white_bishops'] * self.PIECE_VALUES['B']
        score += self.piece_counts['white_rooks'] * self.PIECE_VALUES['R']
        score += self.piece_counts['white_queens'] * self.PIECE_VALUES['Q']

        score -= self.piece_counts['black_pawns'] * self.PIECE_VALUES['P']
        score -= self.piece_counts['black_knights'] * self.PIECE_VALUES['N']
        score -= self.piece_counts['black_bishops'] * self.PIECE_VALUES['B']
        score -= self.piece_counts['black_rooks'] * self.PIECE_VALUES['R']
        score -= self.piece_counts['black_queens'] * self.PIECE_VALUES['Q']

        # Bishop pair bonus
        if self.piece_counts['white_bishops'] >= 2:
            score += 30
        if self.piece_counts['black_bishops'] >= 2:
            score -= 30

        return score

    def _evaluate_position(self) -> int:
        """Fast positional evaluation using bitboards"""
        score = 0

        # Evaluate pawn structure using bitboards
        white_pawns = self.board.white_pawns
        black_pawns = self.board.black_pawns

        # Count doubled pawns using file masks
        for file_mask in self.FILE_MASKS:
            white_pawns_on_file = bin(white_pawns & file_mask).count('1')
            black_pawns_on_file = bin(black_pawns & file_mask).count('1')
            if white_pawns_on_file > 1:
                score -= 10 * (white_pawns_on_file - 1)
            if black_pawns_on_file > 1:
                score += 10 * (black_pawns_on_file - 1)

        # Basic king safety evaluation
        if not self.is_endgame:
            white_king_square = bin(self.board.white_king).count('1') - 1
            black_king_square = bin(self.board.black_king).count('1') - 1

            if white_king_square >= 0:
                white_king_file = white_king_square % 8
                pawn_shield = 0
                for file in range(max(0, white_king_file - 1), min(8, white_king_file + 2)):
                    if white_pawns & self.FILE_MASKS[file]:
                        pawn_shield += 1
                score += pawn_shield * 10

            if black_king_square >= 0:
                black_king_file = black_king_square % 8
                pawn_shield = 0
                for file in range(max(0, black_king_file - 1), min(8, black_king_file + 2)):
                    if black_pawns & self.FILE_MASKS[file]:
                        pawn_shield += 1
                score -= pawn_shield * 10

        return score

    def _evaluate_mobility(self) -> int:
        """Simplified mobility evaluation"""
        score = 0
        move_count = len(self.board.get_legal_moves())

        # Only consider mobility if there are enough pieces
        if self.all_pieces:
            mobility_factor = 2
            score += move_count * mobility_factor if self.board.white_to_move else -move_count * mobility_factor

        return score

    @staticmethod
    def _lsb(bitboard: int) -> int:
        """Get least significant bit position"""
        return (bitboard & -bitboard).bit_length() - 1 if bitboard else -1

    @staticmethod
    def _pop_lsb(bitboard: int) -> tuple[int, int]:
        """Pop least significant bit and return both the bit position and remaining bitboard"""
        if not bitboard:
            return -1, 0
        lsb = bitboard & -bitboard
        return (lsb.bit_length() - 1), (bitboard ^ lsb)
