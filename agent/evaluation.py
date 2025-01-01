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

    # Add new constants for exchange evaluation
    EXCHANGE_VALUES = {
        # 'P': [100, 100, 100, 100, 100, 100, 120, 140],  # Pawn value by rank
        'P': 100,
        'N': 325,
        'B': 335,
        'R': 500,
        'Q': 975,
        'K': 20000
    }

    # Constants for exchange evaluation
    CAPTURE_MARGIN_BASE = 200  # Base margin for considering captures
    EXCHANGE_THRESHOLD = 20    # Minimum advantage to consider an exchange
    MINOR_EXCHANGE_BONUS = 30  # Bonus for winning minor piece exchanges
    ATTACK_WEIGHTS = {
        'P': 1,
        'N': 2,
        'B': 2,
        'R': 3,
        'Q': 4
    }

    # Attack pattern masks
    KNIGHT_ATTACKS = [
        0x0000000000020400, 0x0000000000050800,
        0x00000000000A1100, 0x0000000000142200,
        0x0000000000284400, 0x0000000000508800,
        0x0000000000A01000, 0x0000000000402000
    ]
    
    KING_ATTACKS = [
        0x0000000000000302, 0x0000000000000705,
        0x0000000000000E0A, 0x0000000000001C14,
        0x0000000000003828, 0x0000000000007050,
        0x000000000000E0A0, 0x000000000000C040
    ]

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

    # Optimized bitboard masks
    FILE_MASKS = [0x0101010101010101 << i for i in range(8)]
    RANK_MASKS = [0xFF << (8 * i) for i in range(8)]
    DIAGONAL_MASKS = [
        0x8040201008040201, 0x4020100804020100,
        0x2010080402010000, 0x1008040201000000,
        0x0804020100000000, 0x0402010000000000,
        0x0201000000000000, 0x0100000000000000
    ]
    ANTI_DIAGONAL_MASKS = [
        0x0102040810204080, 0x0001020408102040,
        0x0000010204081020, 0x0000000102040810,
        0x0000000001020408, 0x0000000000010204,
        0x0000000000000102, 0x0000000000000001
    ]

    # Enhanced evaluation parameters
    DOUBLED_PAWN_PENALTY = -15
    ISOLATED_PAWN_PENALTY = -25
    BACKWARD_PAWN_PENALTY = -20
    PASSED_PAWN_BONUS = [0, 10, 20, 40, 60, 90, 130, 180]  # Based on rank
    CONNECTED_PAWNS_BONUS = 8
    ROOK_OPEN_FILE_BONUS = 25
    ROOK_SEMI_OPEN_FILE_BONUS = 15
    BISHOP_PAIR_BONUS = 40
    BISHOP_MOBILITY_MULT = 4
    KNIGHT_OUTPOST_BONUS = 20
    KING_SHIELD_BONUS = [15, 10, 5]  # Distance-based bonus

    def __init__(self, board: Board):
        self.board = board
        self.score = 0

       # Optimized bitboard caches
        self.white_pieces = (self.board.white_pawns | self.board.white_knights | 
                           self.board.white_bishops | self.board.white_rooks | 
                           self.board.white_queens | self.board.white_king)
        self.black_pieces = (self.board.black_pawns | self.board.black_knights | 
                           self.board.black_bishops | self.board.black_rooks | 
                           self.board.black_queens | self.board.black_king)
        self.all_pieces = self.white_pieces | self.black_pieces
        self.empty_squares = ~self.all_pieces & 0xFFFFFFFFFFFFFFFF

        # Pre-calculate piece counts and positions
        self._init_piece_data()

        # Game phase calculation
        self.game_phase = self._calculate_game_phase()

        # Add attack maps cache
        self.white_attacks = 0
        self.black_attacks = 0
        self.white_piece_attacks = {}
        self.black_piece_attacks = {}
        self._init_attack_maps()

    @staticmethod
    def _popcount(bitboard: int) -> int:
        """Fast population count using built-in function"""
        return bin(bitboard).count('1')

    def _init_attack_maps(self):
        """Initialize attack maps for all pieces using bitwise operations"""
        # White pieces attack maps
        self.white_piece_attacks['P'] = self._get_pawn_attacks(self.board.white_pawns, True)
        self.white_piece_attacks['N'] = self._get_knight_attacks(self.board.white_knights)
        self.white_piece_attacks['B'] = self._get_bishop_attacks(self.board.white_bishops)
        self.white_piece_attacks['R'] = self._get_rook_attacks(self.board.white_rooks)
        self.white_piece_attacks['Q'] = self._get_queen_attacks(self.board.white_queens)
        self.white_piece_attacks['K'] = self._get_king_attacks(self.board.white_king)

        # Black pieces attack maps
        self.black_piece_attacks['P'] = self._get_pawn_attacks(self.board.black_pawns, False)
        self.black_piece_attacks['N'] = self._get_knight_attacks(self.board.black_knights)
        self.black_piece_attacks['B'] = self._get_bishop_attacks(self.board.black_bishops)
        self.black_piece_attacks['R'] = self._get_rook_attacks(self.board.black_rooks)
        self.black_piece_attacks['Q'] = self._get_queen_attacks(self.board.black_queens)
        self.black_piece_attacks['K'] = self._get_king_attacks(self.board.black_king)
        
        # Combine all attacks
        self.white_attacks = sum(self.white_piece_attacks.values())
        self.black_attacks = sum(self.black_piece_attacks.values())

    def _init_piece_data(self):
        """Initialize piece counts and positions using fast bitwise operations"""
        self.piece_counts = {
            'white_pawns': self._popcount(self.board.white_pawns),
            'white_knights': self._popcount(self.board.white_knights),
            'white_bishops': self._popcount(self.board.white_bishops),
            'white_rooks': self._popcount(self.board.white_rooks),
            'white_queens': self._popcount(self.board.white_queens),
            'black_pawns': self._popcount(self.board.black_pawns),
            'black_knights': self._popcount(self.board.black_knights),
            'black_bishops': self._popcount(self.board.black_bishops),
            'black_rooks': self._popcount(self.board.black_rooks),
            'black_queens': self._popcount(self.board.black_queens)
        }

    def _get_pawn_attacks(self, pawns: int, is_white: bool) -> int:
        """Get all squares attacked by pawns"""
        if is_white:
            # White pawns attack up-left and up-right
            return ((pawns & ~self.FILE_MASKS[0]) << 7) | ((pawns & ~self.FILE_MASKS[7]) << 9)
        else:
            # Black pawns attack down-left and down-right
            return ((pawns & ~self.FILE_MASKS[0]) >> 9) | ((pawns & ~self.FILE_MASKS[7]) >> 7)

    def _get_knight_attacks(self, knights: int) -> int:
        """Get all squares attacked by knights using pre-computed attack patterns"""
        attacks = 0
        while knights:
            knight_square = self._get_lsb(knights)
            if knight_square >= 0:
                # Shift the appropriate attack pattern to the knight's position
                pattern = self.KNIGHT_ATTACKS[knight_square & 7]  # Use file for pattern selection
                attacks |= (pattern << (8 * (knight_square >> 3))) & 0xFFFFFFFFFFFFFFFF
            knights &= knights - 1  # Clear LSB
        return attacks

    def _get_bishop_attacks(self, bishops: int) -> int:
        """Get all squares attacked by bishops using sliding attacks on diagonals"""
        attacks = 0
        while bishops:
            bishop_square = self._get_lsb(bishops)
            if bishop_square >= 0:
                attacks |= self._get_diagonal_attacks(bishop_square)
            bishops &= bishops - 1
        return attacks

    def _get_rook_attacks(self, rooks: int) -> int:
        """Get all squares attacked by rooks using sliding attacks on ranks and files"""
        attacks = 0
        while rooks:
            rook_square = self._get_lsb(rooks)
            if rook_square >= 0:
                attacks |= self._get_orthogonal_attacks(rook_square)
            rooks &= rooks - 1
        return attacks

    def _get_queen_attacks(self, queens: int) -> int:
        """Get all squares attacked by queens (combination of rook and bishop attacks)"""
        attacks = 0
        while queens:
            queen_square = self._get_lsb(queens)
            if queen_square >= 0:
                attacks |= self._get_diagonal_attacks(queen_square) | self._get_orthogonal_attacks(queen_square)
            queens &= queens - 1
        return attacks

    def _get_king_attacks(self, king: int) -> int:
        """Get all squares attacked by king using pre-computed attack patterns"""
        if not king:
            return 0
        king_square = self._get_lsb(king)
        if king_square < 0:
            return 0
        # Use pre-computed king attack pattern
        pattern = self.KING_ATTACKS[king_square & 7]  # Use file for pattern selection
        return (pattern << (8 * (king_square >> 3))) & 0xFFFFFFFFFFFFFFFF

    def _get_diagonal_attacks(self, square: int) -> int:
        """Get diagonal and anti-diagonal attacks from a square"""
        attacks = 0
        rank, file = square >> 3, square & 7

        # Get relevant diagonal masks
        diag_index = 7 + file - rank
        anti_diag_index = file + rank
        if 0 <= diag_index < len(self.DIAGONAL_MASKS):
            diag_mask = self.DIAGONAL_MASKS[diag_index]
            # Calculate blockers and attacks
            blockers = self.all_pieces & diag_mask
            attacks |= self._get_sliding_attacks(square, diag_mask, blockers)

        if 0 <= anti_diag_index < len(self.ANTI_DIAGONAL_MASKS):
            anti_diag_mask = self.ANTI_DIAGONAL_MASKS[anti_diag_index]
            # Calculate blockers and attacks
            blockers = self.all_pieces & anti_diag_mask
            attacks |= self._get_sliding_attacks(square, anti_diag_mask, blockers)

        return attacks

    def _get_orthogonal_attacks(self, square: int) -> int:
        """Get rank and file attacks from a square"""
        attacks = 0
        rank, file = square >> 3, square & 7

        # Rank attacks
        rank_mask = self.RANK_MASKS[rank]
        rank_blockers = self.all_pieces & rank_mask
        attacks |= self._get_sliding_attacks(square, rank_mask, rank_blockers)

        # File attacks
        file_mask = self.FILE_MASKS[file]
        file_blockers = self.all_pieces & file_mask
        attacks |= self._get_sliding_attacks(square, file_mask, file_blockers)

        return attacks

    def _calculate_game_phase(self) -> int:
        """Calculate game phase (0-256) based on remaining material"""
        total_phase = 256
        current_phase = total_phase

        # Subtract from total phase based on missing pieces
        current_phase -= (16 - (self.piece_counts['white_pawns'] + 
                              self.piece_counts['black_pawns'])) * 4
        current_phase -= (4 - (self.piece_counts['white_knights'] + 
                             self.piece_counts['black_knights'])) * 8
        current_phase -= (4 - (self.piece_counts['white_bishops'] + 
                             self.piece_counts['black_bishops'])) * 8
        current_phase -= (4 - (self.piece_counts['white_rooks'] + 
                             self.piece_counts['black_rooks'])) * 16
        current_phase -= (2 - (self.piece_counts['white_queens'] + 
                             self.piece_counts['black_queens'])) * 32

        return max(current_phase, 0)

    def _get_sliding_attacks(self, square: int, mask: int, blockers: int) -> int:
        """Get sliding piece attacks considering blockers"""
        square_bb = 1 << square

        # Get attacks towards both directions
        forward_ray = mask & ((0xFFFFFFFFFFFFFFFF << square) if square < 63 else 0)
        backward_ray = mask & ((0xFFFFFFFFFFFFFFFF >> (64 - square)) if square > 0 else 0)

        # Find first blockers in each direction
        forward_blocker = forward_ray & blockers
        backward_blocker = backward_ray & blockers

        # Adjust rays to stop at first blockers
        if forward_blocker:
            first_blocker = 1 << self._get_lsb(forward_blocker)
            forward_ray &= (first_blocker - 1)
        if backward_blocker:
            first_blocker = 1 << (63 - self._get_msb(backward_blocker))
            backward_ray &= ~(first_blocker - 1)

        return forward_ray | backward_ray

    def _is_endgame(self) -> bool:
        """Simplified and faster endgame detection"""
        return (self.piece_counts['white_queens'] + self.piece_counts['black_queens'] == 0 or
                (self.piece_counts['white_queens'] + self.piece_counts['black_queens'] == 1 and
                 self.piece_counts['white_rooks'] + self.piece_counts['black_rooks'] <= 1))

    def evaluate(self) -> int:
        """Enhanced position evaluation using bitwise operations"""
        # Quick terminal position detection
        if self.board.is_checkmate():
            return -20000 if self.board.white_to_move else 20000
        if self.board.is_stalemate():
            return 0

        # Base material and positional evaluation
        self.score = self._evaluate_material()

        # Only do detailed evaluation if position isn't clearly decided
        if -2000 <= self.score <= 2000:
            self.score += self._evaluate_position()
            self.score += self._evaluate_exchanges()  # Add exchange evaluation

            # Phase-based evaluation adjustments
            phase_factor = self.game_phase / 256
            self.score = int(self.score * phase_factor)

            # Tempo bonus
            self.score += 15 if self.board.white_to_move else -15

        return self.score

    def _evaluate_exchanges(self) -> int:
        """Evaluate potential captures and exchanges"""
        score = 0

        # Evaluate hanging pieces (pieces attacked but not defended)
        white_hanging = self.black_attacks & self.white_pieces & ~(self.white_attacks)
        black_hanging = self.white_attacks & self.black_pieces & ~(self.black_attacks)

        # Process hanging pieces
        while white_hanging:
            piece_square = self._get_lsb(white_hanging)
            piece_type = self._get_piece_type_at_square(piece_square, True)
            score -= self.EXCHANGE_VALUES.get(piece_type, 0)
            white_hanging &= white_hanging - 1

        while black_hanging:
            piece_square = self._get_lsb(black_hanging)
            piece_type = self._get_piece_type_at_square(piece_square, False)
            score += self.EXCHANGE_VALUES.get(piece_type, 0)
            black_hanging &= black_hanging - 1

        # Evaluate favorable exchanges
        score += self._evaluate_piece_exchanges(True)   # White exchanges
        score += self._evaluate_piece_exchanges(False)  # Black exchanges

        return score

    def _evaluate_piece_exchanges(self, is_white: bool) -> int:
        """Evaluate potential exchanges for one side"""
        score = 0
        attacker_pieces = self.white_pieces if is_white else self.black_pieces
        defender_pieces = self.black_pieces if is_white else self.white_pieces

        # Get attacked pieces
        attacked_pieces = (self.white_attacks if is_white else self.black_attacks) & defender_pieces

        while attacked_pieces:
            target_square = self._get_lsb(attacked_pieces)
            exchange_value = self._evaluate_single_exchange(target_square, is_white)
            score += exchange_value if is_white else -exchange_value
            attacked_pieces &= attacked_pieces - 1

        return score

    def _evaluate_single_exchange(self, target_square: int, is_white: bool) -> int:
        """Evaluate a single exchange sequence using Static Exchange Evaluation (SEE)"""
        target_type = self._get_piece_type_at_square(target_square, not is_white)
        target_value = self.EXCHANGE_VALUES.get(target_type, 0)

        # Get attackers and defenders
        attackers = self._get_attackers_to_square(target_square, is_white)
        defenders = self._get_attackers_to_square(target_square, not is_white)

        if not attackers:
            return 0

        # Sort attackers by value (ascending)
        attacker_list = self._sort_pieces_by_value(attackers)
        defender_list = self._sort_pieces_by_value(defenders)

        # Simulate the exchange sequence
        gain = target_value
        current_value = gain

        for i in range(min(len(attacker_list), len(defender_list))):
            # Attacker captures
            current_value = -current_value + self.EXCHANGE_VALUES.get(attacker_list[i], 0)
            if current_value < -self.EXCHANGE_THRESHOLD:
                break

            # Defender recaptures
            if i < len(defender_list):
                current_value = -current_value + self.EXCHANGE_VALUES.get(defender_list[i], 0)
                if current_value < -self.EXCHANGE_THRESHOLD:
                    break

        return -current_value if current_value < 0 else 0

    def _get_attackers_to_square(self, square: int, is_white: bool) -> list:
        """Get all pieces attacking a square"""
        attackers = []
        piece_attacks = self.white_piece_attacks if is_white else self.black_piece_attacks

        for piece_type, attacks in piece_attacks.items():
            if attacks & (1 << square):
                attackers.append(piece_type)

        return attackers

    def _sort_pieces_by_value(self, pieces: list) -> list:
        """Sort pieces by their exchange value"""
        return sorted(pieces, key=lambda x: self.EXCHANGE_VALUES.get(x, 0))

    def _get_piece_type_at_square(self, square: int, is_white: bool) -> str:
        """Get piece type at a given square"""
        bit = 1 << square
        pieces = {
            'P': self.board.white_pawns if is_white else self.board.black_pawns,
            'N': self.board.white_knights if is_white else self.board.black_knights,
            'B': self.board.white_bishops if is_white else self.board.black_bishops,
            'R': self.board.white_rooks if is_white else self.board.black_rooks,
            'Q': self.board.white_queens if is_white else self.board.black_queens,
            'K': self.board.white_king if is_white else self.board.black_king
        }

        for piece_type, bitboard in pieces.items():
            if bitboard & bit:
                return piece_type
        return ''

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
        """Enhanced positional evaluation using bitwise operations"""
        score = 0

        # Pawn structure evaluation
        score += self._evaluate_pawn_structure()

        # Piece mobility and positioning
        score += self._evaluate_piece_activity()

        # King safety evaluation
        score += self._evaluate_king_safety()

        return score

    def _evaluate_pawn_structure(self) -> int:
        """Evaluate pawn structure using bitwise operations"""
        score = 0
        white_pawns = self.board.white_pawns
        black_pawns = self.board.black_pawns

        # Doubled pawns
        for file_mask in self.FILE_MASKS:
            wp_count = self._popcount(white_pawns & file_mask)
            bp_count = self._popcount(black_pawns & file_mask)
            score += self.DOUBLED_PAWN_PENALTY * (wp_count - 1 if wp_count > 1 else 0)
            score -= self.DOUBLED_PAWN_PENALTY * (bp_count - 1 if bp_count > 1 else 0)

        # Passed pawns and isolated pawns
        for i, file_mask in enumerate(self.FILE_MASKS):
            adjacent_files = 0
            if i > 0:
                adjacent_files |= self.FILE_MASKS[i - 1]
            if i < 7:
                adjacent_files |= self.FILE_MASKS[i + 1]

            # White pawns
            wp_file = white_pawns & file_mask
            if wp_file:
                if not (white_pawns & adjacent_files):
                    score += self.ISOLATED_PAWN_PENALTY
                if not ((black_pawns & file_mask) | 
                       (black_pawns & adjacent_files & 
                        ((wp_file - 1) & 0xFFFFFFFFFFFFFFFF))):
                    score += self.PASSED_PAWN_BONUS[7 - (wp_file.bit_length() - 1) // 8]

            # Black pawns
            bp_file = black_pawns & file_mask
            if bp_file:
                if not (black_pawns & adjacent_files):
                    score -= self.ISOLATED_PAWN_PENALTY
                if not ((white_pawns & file_mask) | 
                       (white_pawns & adjacent_files & 
                        ((bp_file << 1) - 1))):
                    score -= self.PASSED_PAWN_BONUS[bp_file.bit_length() // 8]

        return score

    def _evaluate_piece_activity(self) -> int:
        """Evaluate piece mobility and positioning"""
        score = 0

        # Rook positioning
        white_rooks = self.board.white_rooks
        black_rooks = self.board.black_rooks

        # Open and semi-open files for rooks
        for file_mask in self.FILE_MASKS:
            file_pawns = (self.board.white_pawns | self.board.black_pawns) & file_mask
            if not file_pawns:
                score += self.ROOK_OPEN_FILE_BONUS * self._popcount(white_rooks & file_mask)
                score -= self.ROOK_OPEN_FILE_BONUS * self._popcount(black_rooks & file_mask)
            else:
                white_file_pawns = self.board.white_pawns & file_mask
                black_file_pawns = self.board.black_pawns & file_mask
                if not white_file_pawns:
                    score += self.ROOK_SEMI_OPEN_FILE_BONUS * self._popcount(white_rooks & file_mask)
                if not black_file_pawns:
                    score -= self.ROOK_SEMI_OPEN_FILE_BONUS * self._popcount(black_rooks & file_mask)

        # Knight outposts
        white_knights = self.board.white_knights
        black_knights = self.board.black_knights

        # Calculate pawn attack masks
        white_pawn_attacks = ((self.board.white_pawns & ~self.FILE_MASKS[0]) >> 7) | \
                           ((self.board.white_pawns & ~self.FILE_MASKS[7]) >> 9)
        black_pawn_attacks = ((self.board.black_pawns & ~self.FILE_MASKS[0]) << 9) | \
                           ((self.board.black_pawns & ~self.FILE_MASKS[7]) << 7)

        # Knight outpost bonus (knights defended by pawns and cannot be attacked by enemy pawns)
        white_outposts = white_knights & white_pawn_attacks & ~black_pawn_attacks & \
                        (self.RANK_MASKS[3] | self.RANK_MASKS[4] | self.RANK_MASKS[5])
        black_outposts = black_knights & black_pawn_attacks & ~white_pawn_attacks & \
                        (self.RANK_MASKS[2] | self.RANK_MASKS[3] | self.RANK_MASKS[4])

        score += self.KNIGHT_OUTPOST_BONUS * self._popcount(white_outposts)
        score -= self.KNIGHT_OUTPOST_BONUS * self._popcount(black_outposts)

        # Bishop mobility using diagonal masks
        white_bishops = self.board.white_bishops
        black_bishops = self.board.black_bishops

        # Calculate bishop mobility using diagonal and anti-diagonal masks
        for diag_mask in self.DIAGONAL_MASKS + self.ANTI_DIAGONAL_MASKS:
            white_bishop_diag = white_bishops & diag_mask
            black_bishop_diag = black_bishops & diag_mask
            if white_bishop_diag:
                mobility = self._popcount(diag_mask & ~self.white_pieces)
                score += mobility * self.BISHOP_MOBILITY_MULT
            if black_bishop_diag:
                mobility = self._popcount(diag_mask & ~self.black_pieces)
                score -= mobility * self.BISHOP_MOBILITY_MULT

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

    def _evaluate_king_safety(self) -> int:
        """Evaluate king safety using bitwise operations"""
        score = 0

        # Only evaluate king safety in non-endgame positions
        if self.game_phase > 128:  # Middle game
            white_king_square = self._get_lsb(self.board.white_king)
            black_king_square = self._get_lsb(self.board.black_king)

            # Get king files
            white_king_file = white_king_square & 7
            black_king_file = black_king_square & 7

            # Evaluate pawn shield for white king
            white_king_zone = self._get_king_zone(white_king_square)
            white_pawn_shield = self.board.white_pawns & white_king_zone

            # Count pawns in the shield based on distance from king
            for i, distance in enumerate(self.KING_SHIELD_BONUS):
                rank_mask = self.RANK_MASKS[7 - i] if white_king_square >= 48 else self.RANK_MASKS[i]
                shield_pawns = self._popcount(white_pawn_shield & rank_mask)
                score += shield_pawns * distance

            # Evaluate pawn shield for black king
            black_king_zone = self._get_king_zone(black_king_square)
            black_pawn_shield = self.board.black_pawns & black_king_zone

            for i, distance in enumerate(self.KING_SHIELD_BONUS):
                rank_mask = self.RANK_MASKS[i] if black_king_square < 16 else self.RANK_MASKS[7 - i]
                shield_pawns = self._popcount(black_pawn_shield & rank_mask)
                score -= shield_pawns * distance

            # Evaluate king exposure (open files near king)
            white_king_files = self._get_adjacent_files(white_king_file)
            black_king_files = self._get_adjacent_files(black_king_file)

            for file_mask in white_king_files:
                if not (self.board.white_pawns & file_mask):
                    score -= 15  # Penalty for each open file near king

            for file_mask in black_king_files:
                if not (self.board.black_pawns & file_mask):
                    score += 15  # Penalty for each open file near king

            # Additional penalty for attacks near king
            white_king_attacks = self._count_attacks_near_king(white_king_square, True)
            black_king_attacks = self._count_attacks_near_king(black_king_square, False)

            score -= white_king_attacks * 10
            score += black_king_attacks * 10

        return score

    def _get_king_zone(self, king_square: int) -> int:
        """Get a bitboard of the 8 squares surrounding the king plus 3 squares in front"""
        zone = 0
        rank = king_square >> 3
        file = king_square & 7

        # Generate zone masks based on king position
        for r in range(max(0, rank - 1), min(8, rank + 2)):
            for f in range(max(0, file - 1), min(8, file + 2)):
                zone |= 1 << (r * 8 + f)

        # Add three squares in front for castled king
        if rank == 0 or rank == 7:
            front_rank = 1 if rank == 0 else 6
            for f in range(max(0, file - 1), min(8, file + 2)):
                zone |= 1 << (front_rank * 8 + f)

        return zone

    def _get_adjacent_files(self, file: int) -> list:
        """Get masks for files adjacent to the given file"""
        files = []
        if file > 0:
            files.append(self.FILE_MASKS[file - 1])
        files.append(self.FILE_MASKS[file])
        if file < 7:
            files.append(self.FILE_MASKS[file + 1])
        return files

    def _count_attacks_near_king(self, king_square: int, is_white_king: bool) -> int:
        """Count number of enemy attacks near the king"""
        king_zone = self._get_king_zone(king_square)
        enemy_pieces = self.black_pieces if is_white_king else self.white_pieces
        return self._popcount(king_zone & enemy_pieces)

    @staticmethod
    def _get_lsb(bitboard: int) -> int:
        """Get the position of the least significant bit"""
        return (bitboard & -bitboard).bit_length() - 1 if bitboard else -1

    @staticmethod
    def _get_msb(bitboard: int) -> int:
        """Get the position of the most significant bit"""
        return bitboard.bit_length() - 1 if bitboard else -1
