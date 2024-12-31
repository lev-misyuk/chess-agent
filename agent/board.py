from typing import Optional
from agent.square import Square
from agent.move import Move, MoveFlag

STARTING_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

class Board:
    """Class representing a chess board and game state"""
    # Predefined directional shifts for sliding pieces
    NORTH = 8
    SOUTH = -8
    EAST = 1
    WEST = -1
    NORTH_EAST = 9
    NORTH_WEST = 7
    SOUTH_EAST = -7
    SOUTH_WEST = -9

    def __init__(self, fen: str = STARTING_FEN):
        """Initialize the board from a FEN string"""
        # Initialize all bitboards to 0
        self.white_pawns = 0
        self.white_knights = 0
        self.white_bishops = 0
        self.white_rooks = 0
        self.white_queens = 0
        self.white_king = 0

        self.black_pawns = 0
        self.black_knights = 0
        self.black_bishops = 0
        self.black_rooks = 0
        self.black_queens = 0
        self.black_king = 0

        # Initialize game state
        self.white_to_move = True
        self.castling_rights = {'K': True, 'Q': True, 'k': True, 'q': True}
        self.en_passant_target: Optional[Square] = None
        self.halfmove_clock = 0
        self.fullmove_number = 1

        self._parse_fen(fen)
        self.update_position_masks()

    def _parse_fen(self, fen: str) -> None:
        """Parse a FEN string and set up the board accordingly"""
        parts = fen.split()
        ranks = parts[0].split('/')

        # 1. Parse piece placement
        for rank_idx, rank in enumerate(ranks):
            file_idx = 0
            for char in rank:
                if char.isdigit():
                    file_idx += int(char)
                else:
                    square = Square.from_coords(7 - rank_idx, file_idx)
                    mask = 1 << int(square)

                    if char == 'P': self.white_pawns |= mask
                    elif char == 'N': self.white_knights |= mask
                    elif char == 'B': self.white_bishops |= mask
                    elif char == 'R': self.white_rooks |= mask
                    elif char == 'Q': self.white_queens |= mask
                    elif char == 'K': self.white_king |= mask
                    elif char == 'p': self.black_pawns |= mask
                    elif char == 'n': self.black_knights |= mask
                    elif char == 'b': self.black_bishops |= mask
                    elif char == 'r': self.black_rooks |= mask
                    elif char == 'q': self.black_queens |= mask
                    elif char == 'k': self.black_king |= mask

                    file_idx += 1

        # 2. Active color
        self.white_to_move = parts[1] == 'w'

        # 3. Castling availability
        self.castling_rights = {
            'K': 'K' in parts[2],
            'Q': 'Q' in parts[2],
            'k': 'k' in parts[2],
            'q': 'q' in parts[2]
        }

        # 4. En passant target square
        self.en_passant_target = None if parts[3] == '-' else Square.from_notation(parts[3])

        # 5. Halfmove clock
        self.halfmove_clock = int(parts[4])

        # 6. Fullmove number
        self.fullmove_number = int(parts[5])

    def __str__(self):
        """Returns a string representation of the current board position"""
        # Unicode chess pieces
        pieces = {
            'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
            'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
        }

        # Create the board string with a border
        board_str = "\n  ┌───┬───┬───┬───┬───┬───┬───┬───┐\n"

        for rank in range(7, -1, -1):
            board_str += f"{rank + 1} │"
            for file in range(8):
                square = rank * 8 + file
                piece = self.get_piece_at(square)
                # Convert piece to Unicode symbol if it's a piece, or use dot for empty square
                symbol = pieces.get(piece, '·')
                board_str += f" {symbol} │"

            # Add rank separator unless it's the last rank
            if rank > 0:
                board_str += "\n  ├───┼───┼───┼───┼───┼───┼───┼───┤\n"
            else:
                board_str += "\n  └───┴───┴───┴───┴───┴───┴───┴───┘\n"

        # Add file labels
        board_str += "    a   b   c   d   e   f   g   h\n"

        # Add additional game state information
        board_str += f"\nTurn: {'White' if self.white_to_move else 'Black'}\n"

        # Add castling rights
        castling = "".join([k for k, v in self.castling_rights.items() if v])
        board_str += f"Castling: {castling if castling else '-'}\n"

        # Add check/checkmate/stalemate status
        if self.is_checkmate():
            board_str += "CHECKMATE\n"
        elif self.is_stalemate():
            board_str += "STALEMATE\n"
        elif self.is_in_check(self.white_to_move):
            board_str += "CHECK\n"

        return board_str

    def generate_fen(self) -> str:
        """Generates a FEN string representing the current position"""
        # 1. Piece placement
        empty_count = 0
        position = []
        for rank in range(7, -1, -1):
            rank_str = ""
            for file in range(8):
                square = Square.from_coords(rank, file)
                piece = self.get_piece_at(square)

                if piece == '.':
                    empty_count += 1
                else:
                    if empty_count > 0:
                        rank_str += str(empty_count)
                        empty_count = 0
                    rank_str += piece

            if empty_count > 0:
                rank_str += str(empty_count)
                empty_count = 0

            position.append(rank_str)

        fen = '/'.join(position)

        # 2. Active color
        fen += ' w ' if self.white_to_move else ' b '

        # 3. Castling availability
        castling = ''
        if self.castling_rights['K']: castling += 'K'
        if self.castling_rights['Q']: castling += 'Q'
        if self.castling_rights['k']: castling += 'k'
        if self.castling_rights['q']: castling += 'q'
        fen += castling if castling else '-'

        # 4. En passant target square
        fen += ' ' + (self.en_passant_target.notation if self.en_passant_target else '-')

        # 5. Halfmove clock
        fen += f' {self.halfmove_clock}'

        # 6. Fullmove number
        fen += f' {self.fullmove_number}'

        return fen

    def update_position_masks(self):
        """Updates the combined position masks for all pieces"""
        self.white_pieces = (
            self.white_pawns | self.white_knights | self.white_bishops |
            self.white_rooks | self.white_queens | self.white_king
        )
        self.black_pieces = (
            self.black_pawns | self.black_knights | self.black_bishops |
            self.black_rooks | self.black_queens | self.black_king
        )
        self.all_pieces = self.white_pieces | self.black_pieces

    def get_piece_at(self, square: Square) -> str:
        """Returns the piece at the given square"""
        mask = 1 << int(square)

        if self.white_pawns & mask: return 'P'
        if self.white_knights & mask: return 'N'
        if self.white_bishops & mask: return 'B'
        if self.white_rooks & mask: return 'R'
        if self.white_queens & mask: return 'Q'
        if self.white_king & mask: return 'K'

        if self.black_pawns & mask: return 'p'
        if self.black_knights & mask: return 'n'
        if self.black_bishops & mask: return 'b'
        if self.black_rooks & mask: return 'r'
        if self.black_queens & mask: return 'q'
        if self.black_king & mask: return 'k'

        return '.'

    def get_sliding_attacks(self, square: Square, directions: int):
        """Gets attacks for sliding pieces (bishop, rook, queen)"""
        attacks = 0
        square_index = int(square)
        rank, file = square_index // 8, square_index % 8

        for direction in directions:
            current_square = square_index
            while True:
                current_square += direction
                current_rank, current_file = current_square // 8, current_square % 8

                # Check if we've moved off the board or wrapped around
                if (current_square < 0 or current_square > 63 or
                    abs(current_file - file) > 7):
                    break

                attacks |= 1 << current_square

                # Stop if we hit a piece
                if self.all_pieces & (1 << current_square):
                    break

                file = current_file

        return attacks

    def get_attacks(self, square: Square):
        """Returns a bitboard of all squares attacked from the given square"""
        piece = self.get_piece_at(square)
        if piece == '.':
            return 0

        is_white = piece.isupper()
        piece = piece.upper()
        attacks = 0

        square_index = int(square)

        if piece == 'P':
            # Pawn attacks
            if is_white:
                if square_index % 8 > 0:  # Can attack left
                    attacks |= 1 << (square_index + 7)
                if square_index % 8 < 7:  # Can attack right
                    attacks |= 1 << (square_index + 9)
            else:
                if square_index % 8 > 0:  # Can attack left
                    attacks |= 1 << (square_index - 9)
                if square_index % 8 < 7:  # Can attack right
                    attacks |= 1 << (square_index - 7)

        elif piece == 'N':
            # Knight attacks
            knight_moves = [
                (2, 1), (2, -1), (-2, 1), (-2, -1),
                (1, 2), (1, -2), (-1, 2), (-1, -2)
            ]
            rank, file = square_index // 8, square_index % 8
            for rank_move, file_move in knight_moves:
                new_rank = rank + rank_move
                new_file = file + file_move
                if 0 <= new_rank < 8 and 0 <= new_file < 8:
                    attacks |= 1 << (new_rank * 8 + new_file)

        elif piece == 'B':
            # Bishop attacks
            attacks = self.get_sliding_attacks(square,
                [self.NORTH_EAST, self.NORTH_WEST, self.SOUTH_EAST, self.SOUTH_WEST])

        elif piece == 'R':
            # Rook attacks
            attacks = self.get_sliding_attacks(square,
                [self.NORTH, self.SOUTH, self.EAST, self.WEST])

        elif piece == 'Q':
            # Queen attacks (combination of bishop and rook)
            attacks = self.get_sliding_attacks(square,
                [self.NORTH, self.SOUTH, self.EAST, self.WEST,
                 self.NORTH_EAST, self.NORTH_WEST, self.SOUTH_EAST, self.SOUTH_WEST])

        elif piece == 'K':
            # King attacks (one square in all directions)
            king_directions = [
                self.NORTH, self.SOUTH, self.EAST, self.WEST,
                self.NORTH_EAST, self.NORTH_WEST, self.SOUTH_EAST, self.SOUTH_WEST
            ]
            rank, file = square_index // 8, square_index % 8
            for direction in king_directions:
                new_square = square_index + direction
                new_rank, new_file = new_square // 8, new_square % 8
                if (0 <= new_square < 64 and 
                    abs(new_file - file) <= 1 and
                    abs(new_rank - rank) <= 1):
                    attacks |= 1 << new_square

        return attacks

    def is_square_attacked(self, square: Square, by_white: bool) -> bool:
        """Checks if a square is attacked by any piece of the given color"""
        square_idx = int(square)

        # Check pawn attacks
        rank, file = square_idx // 8, square_idx % 8
        if by_white:
            # Check white pawn attacks
            for attack_file in [file - 1, file + 1]:
                if 0 <= attack_file < 8 and rank > 0:
                    attack_square = Square.from_coords(rank - 1, attack_file)
                    if self.get_piece_at(attack_square) == 'P':
                        return True
        else:
            # Check black pawn attacks
            for attack_file in [file - 1, file + 1]:
                if 0 <= attack_file < 8 and rank < 7:
                    attack_square = Square.from_coords(rank + 1, attack_file)
                    if self.get_piece_at(attack_square) == 'p':
                        return True

        # Check knight attacks
        knight_moves = [
            (2, 1), (2, -1), (-2, 1), (-2, -1),
            (1, 2), (1, -2), (-1, 2), (-1, -2)
        ]
        for rank_offset, file_offset in knight_moves:
            new_rank = rank + rank_offset
            new_file = file + file_offset
            if 0 <= new_rank < 8 and 0 <= new_file < 8:
                attack_square = Square.from_coords(new_rank, new_file)
                piece = self.get_piece_at(attack_square)
                if piece == ('N' if by_white else 'n'):
                    return True

        # Check sliding piece attacks (bishop, rook, queen)
        # Diagonal directions for bishop/queen
        diagonal_directions = [
            self.NORTH_EAST, self.NORTH_WEST,
            self.SOUTH_EAST, self.SOUTH_WEST
        ]

        # Straight directions for rook/queen
        straight_directions = [
            self.NORTH, self.SOUTH,
            self.EAST, self.WEST
        ]

        # Check diagonal attacks
        for direction in diagonal_directions:
            current_square = square_idx
            current_rank, current_file = rank, file

            while True:
                current_square += direction
                new_rank = current_square // 8
                new_file = current_square % 8

                if (current_square < 0 or current_square > 63 or
                    abs(new_rank - current_rank) != abs(new_file - current_file)):
                    break

                piece = self.get_piece_at(Square.from_bitboard_square(current_square))
                if piece != '.':
                    if by_white:
                        if piece in 'BQ':  # White bishop or queen
                            return True
                    else:
                        if piece in 'bq':  # Black bishop or queen
                            return True
                    break

                current_rank, current_file = new_rank, new_file

        # Check straight attacks
        for direction in straight_directions:
            current_square = square_idx
            current_rank, current_file = rank, file

            while True:
                current_square += direction
                new_rank = current_square // 8
                new_file = current_square % 8

                if (current_square < 0 or current_square > 63 or
                    (direction in [self.EAST, self.WEST] and new_rank != current_rank) or
                    (direction in [self.NORTH, self.SOUTH] and new_file != current_file)):
                    break

                piece = self.get_piece_at(Square.from_bitboard_square(current_square))
                if piece != '.':
                    if by_white:
                        if piece in 'RQ':  # White rook or queen
                            return True
                    else:
                        if piece in 'rq':  # Black rook or queen
                            return True
                    break

                current_rank, current_file = new_rank, new_file

        # Check king attacks
        king_moves = [(1, 0), (1, 1), (0, 1), (-1, 1),
                    (-1, 0), (-1, -1), (0, -1), (1, -1)]
        for rank_offset, file_offset in king_moves:
            new_rank = rank + rank_offset
            new_file = file + file_offset
            if 0 <= new_rank < 8 and 0 <= new_file < 8:
                attack_square = Square.from_coords(new_rank, new_file)
                piece = self.get_piece_at(attack_square)
                if piece == ('K' if by_white else 'k'):
                    return True

        return False

    def is_in_check(self, white: bool) -> bool:
        """Determines if the given side is in check"""
        # Find king position
        king_bb = self.white_king if white else self.black_king
        king_square = None

        for i in range(64):
            if king_bb & (1 << i):
                king_square = Square.from_bitboard_square(i)
                break

        if king_square is None:
            return False

        # Check if any enemy piece attacks the king
        return self.is_square_attacked(king_square, not white)

    def make_move(self, move: Move) -> bool:
        """Makes a move on the board if it's legal"""
        # Store current state
        old_state = self.__dict__.copy()

        from_bb = int(move.from_square)
        to_bb = int(move.to_square)
        from_mask = 1 << from_bb
        to_mask = 1 << to_bb

        piece = self.get_piece_at(move.from_square)
        if piece == '.' or piece.isupper() != self.white_to_move:
            return False

        # Handle special moves
        if move.is_castling:
            if move.flag == MoveFlag.KING_CASTLE:
                rook_from = Square.H1 if self.white_to_move else Square.H8
                rook_to = Square.F1 if self.white_to_move else Square.F8
            else:  # Queen-side castle
                rook_from = Square.A1 if self.white_to_move else Square.A8
                rook_to = Square.D1 if self.white_to_move else Square.D8

            # Move rook
            rook_from_bb = int(rook_from)
            rook_to_bb = int(rook_to)
            if self.white_to_move:
                self.white_rooks &= ~(1 << rook_from_bb)
                self.white_rooks |= (1 << rook_to_bb)
            else:
                self.black_rooks &= ~(1 << rook_from_bb)
                self.black_rooks |= (1 << rook_to_bb)

        # Handle captures and piece movement
        captured_piece = False
        for piece_bb in (
            'white_pawns', 'white_knights', 'white_bishops', 'white_rooks', 
            'white_queens', 'white_king', 'black_pawns', 'black_knights', 
            'black_bishops', 'black_rooks', 'black_queens', 'black_king'
        ):
            current_bb = getattr(self, piece_bb)

            # Handle capturing
            if current_bb & to_mask:
                captured_piece = True
                setattr(self, piece_bb, current_bb & ~to_mask)

            # Move piece
            if current_bb & from_mask:
                new_bb = (current_bb & ~from_mask) | to_mask
                setattr(self, piece_bb, new_bb)

        # Handle promotions
        if move.is_promotion:
            # Remove pawn
            if self.white_to_move:
                self.white_pawns &= ~to_mask
            else:
                self.black_pawns &= ~to_mask

            # Add promoted piece based on the promotion type
            promotion_piece = move.get_promotion_piece()
            if promotion_piece == 'Q':
                target_bb = 'white_queens' if self.white_to_move else 'black_queens'
            elif promotion_piece == 'R':
                target_bb = 'white_rooks' if self.white_to_move else 'black_rooks'
            elif promotion_piece == 'B':
                target_bb = 'white_bishops' if self.white_to_move else 'black_bishops'
            elif promotion_piece == 'N':
                target_bb = 'white_knights' if self.white_to_move else 'black_knights'

            current_bb = getattr(self, target_bb)
            setattr(self, target_bb, current_bb | to_mask)

        # Update position masks
        self.update_position_masks()

        # Check if move is legal (doesn't leave king in check)
        if self.is_in_check(self.white_to_move):
            self.__dict__ = old_state
            return False

        # Update game state
        self.white_to_move = not self.white_to_move
        if not self.white_to_move:
            self.fullmove_number += 1

        # Update castling rights
        if piece.upper() == 'K':
            if self.white_to_move:
                self.castling_rights['K'] = False
                self.castling_rights['Q'] = False
            else:
                self.castling_rights['k'] = False
                self.castling_rights['q'] = False
        elif piece.upper() == 'R':
            if move.from_square == Square.A1:
                self.castling_rights['Q'] = False
            elif move.from_square == Square.H1:
                self.castling_rights['K'] = False
            elif move.from_square == Square.A8:
                self.castling_rights['q'] = False
            elif move.from_square == Square.H8:
                self.castling_rights['k'] = False

        return True

    def is_checkmate(self) -> bool:
        """Determines if the current position is checkmate"""
        # If not in check, it's not checkmate
        if not self.is_in_check(self.white_to_move):
            return False

        # If there are any legal moves, it's not checkmate
        return len(self.get_legal_moves()) == 0

    def is_stalemate(self) -> bool:
        """Determines if the current position is stalemate"""
        # If in check, it's not stalemate
        if self.is_in_check(self.white_to_move):
            return False

        # If there are any legal moves, it's not stalemate
        return len(self.get_legal_moves()) == 0

    def get_legal_pawn_moves(self, square: Square) -> list[Move]:
        """Get all legal pawn moves from given square"""
        moves = []
        square_idx = int(square)
        rank, file = square_idx // 8, square_idx % 8

        if self.white_to_move:
            # Forward moves
            if rank < 7:  # Not on last rank
                # Single push
                target = Square.from_coords(rank + 1, file)
                if self.get_piece_at(target) == '.':
                    if rank == 6:  # Promotion
                        for flag in [MoveFlag.PROMOTION_Q, MoveFlag.PROMOTION_R, 
                                MoveFlag.PROMOTION_B, MoveFlag.PROMOTION_N]:
                            moves.append(Move(square, target, flag))
                    else:
                        moves.append(Move(square, target, MoveFlag.QUIET))

                    # Double push from starting rank
                    if rank == 1:
                        target = Square.from_coords(rank + 2, file)
                        if self.get_piece_at(target) == '.':
                            moves.append(Move(square, target, MoveFlag.DOUBLE_PAWN_PUSH))

            # Captures
            for capture_file in [file - 1, file + 1]:
                if 0 <= capture_file < 8 and rank < 7:
                    target = Square.from_coords(rank + 1, capture_file)
                    piece_at_target = self.get_piece_at(target)

                    if piece_at_target != '.' and piece_at_target.islower():  # Enemy piece
                        if rank == 6:  # Promotion capture
                            for flag in [MoveFlag.PROMOTION_CAPTURE_Q, MoveFlag.PROMOTION_CAPTURE_R,
                                    MoveFlag.PROMOTION_CAPTURE_B, MoveFlag.PROMOTION_CAPTURE_N]:
                                moves.append(Move(square, target, flag))
                        else:
                            moves.append(Move(square, target, MoveFlag.CAPTURE))

                    # En passant
                    if self.en_passant_target and target == self.en_passant_target:
                        moves.append(Move(square, target, MoveFlag.EN_PASSANT))

        else:  # Black pawns
            # Forward moves
            if rank > 0:  # Not on last rank
                # Single push
                target = Square.from_coords(rank - 1, file)
                if self.get_piece_at(target) == '.':
                    if rank == 1:  # Promotion
                        for flag in [MoveFlag.PROMOTION_Q, MoveFlag.PROMOTION_R,
                                MoveFlag.PROMOTION_B, MoveFlag.PROMOTION_N]:
                            moves.append(Move(square, target, flag))
                    else:
                        moves.append(Move(square, target, MoveFlag.QUIET))

                    # Double push from starting rank
                    if rank == 6:
                        target = Square.from_coords(rank - 2, file)
                        if self.get_piece_at(target) == '.':
                            moves.append(Move(square, target, MoveFlag.DOUBLE_PAWN_PUSH))

            # Captures
            for capture_file in [file - 1, file + 1]:
                if 0 <= capture_file < 8 and rank > 0:
                    target = Square.from_coords(rank - 1, capture_file)
                    piece_at_target = self.get_piece_at(target)

                    if piece_at_target != '.' and piece_at_target.isupper():  # Enemy piece
                        if rank == 1:  # Promotion capture
                            for flag in [MoveFlag.PROMOTION_CAPTURE_Q, MoveFlag.PROMOTION_CAPTURE_R,
                                    MoveFlag.PROMOTION_CAPTURE_B, MoveFlag.PROMOTION_CAPTURE_N]:
                                moves.append(Move(square, target, flag))
                        else:
                            moves.append(Move(square, target, MoveFlag.CAPTURE))

                    # En passant
                    if self.en_passant_target and target == self.en_passant_target:
                        moves.append(Move(square, target, MoveFlag.EN_PASSANT))

        return moves

    def get_legal_knight_moves(self, square: Square) -> list[Move]:
        """Get all legal knight moves from given square"""
        moves = []
        square_idx = int(square)
        rank, file = square_idx // 8, square_idx % 8

        # All possible knight moves
        knight_moves = [
            (2, 1), (2, -1), (-2, 1), (-2, -1),
            (1, 2), (1, -2), (-1, 2), (-1, -2)
        ]

        for rank_offset, file_offset in knight_moves:
            new_rank = rank + rank_offset
            new_file = file + file_offset

            if 0 <= new_rank < 8 and 0 <= new_file < 8:
                target = Square.from_coords(new_rank, new_file)
                target_piece = self.get_piece_at(target)

                # Square is empty or contains enemy piece
                if target_piece == '.' or \
                (self.white_to_move and target_piece.islower()) or \
                (not self.white_to_move and target_piece.isupper()):
                    flag = MoveFlag.CAPTURE if target_piece != '.' else MoveFlag.QUIET
                    moves.append(Move(square, target, flag))

        return moves

    def get_legal_sliding_moves(self, square: Square, directions: list) -> list[Move]:
        """Get all legal moves for sliding pieces (bishop, rook, queen)"""
        moves = []
        square_idx = int(square)
        rank, file = square_idx // 8, square_idx % 8

        for direction in directions:
            current_square = square_idx
            current_rank, current_file = rank, file

            while True:
                current_square += direction
                new_rank = current_square // 8
                new_file = current_square % 8

                # Check if we've moved off the board
                if (current_square < 0 or current_square > 63):
                    break

                # Check if we've wrapped around the board
                rank_diff = abs(new_rank - current_rank)
                file_diff = abs(new_file - current_file)
                if (direction in [self.EAST, self.WEST] and rank_diff != 0) or \
                (direction in [self.NORTH, self.SOUTH] and file_diff != 0) or \
                (direction in [self.NORTH_EAST, self.NORTH_WEST, self.SOUTH_EAST, self.SOUTH_WEST] 
                    and abs(rank_diff - file_diff) != 0):
                    break

                target = Square.from_bitboard_square(current_square)
                target_piece = self.get_piece_at(target)

                # Empty square
                if target_piece == '.':
                    moves.append(Move(square, target, MoveFlag.QUIET))
                # Enemy piece
                elif (self.white_to_move and target_piece.islower()) or \
                    (not self.white_to_move and target_piece.isupper()):
                    moves.append(Move(square, target, MoveFlag.CAPTURE))
                    break
                # Own piece
                else:
                    break

                current_rank = new_rank
                current_file = new_file

        return moves

    def get_legal_king_moves(self, square: Square) -> list[Move]:
        """Get all legal king moves from given square"""
        moves = []
        square_idx = int(square)
        rank, file = square_idx // 8, square_idx % 8

        # Normal king moves
        king_moves = [
            (1, 0), (1, 1), (0, 1), (-1, 1),
            (-1, 0), (-1, -1), (0, -1), (1, -1)
        ]

        for rank_offset, file_offset in king_moves:
            new_rank = rank + rank_offset
            new_file = file + file_offset

            if 0 <= new_rank < 8 and 0 <= new_file < 8:
                target = Square.from_coords(new_rank, new_file)
                target_piece = self.get_piece_at(target)

                # Square is empty or contains enemy piece
                if target_piece == '.' or \
                (self.white_to_move and target_piece.islower()) or \
                (not self.white_to_move and target_piece.isupper()):
                    flag = MoveFlag.CAPTURE if target_piece != '.' else MoveFlag.QUIET
                    moves.append(Move(square, target, flag))

        # Castling
        if self.white_to_move:
            if self.castling_rights['K'] and square == Square.E1:
                if (self.get_piece_at(Square.F1) == '.' and 
                    self.get_piece_at(Square.G1) == '.' and
                    not self.is_square_attacked(Square.E1, False) and
                    not self.is_square_attacked(Square.F1, False) and
                    not self.is_square_attacked(Square.G1, False)):
                    moves.append(Move(Square.E1, Square.G1, MoveFlag.KING_CASTLE))

            if self.castling_rights['Q'] and square == Square.E1:
                if (self.get_piece_at(Square.D1) == '.' and 
                    self.get_piece_at(Square.C1) == '.' and
                    self.get_piece_at(Square.B1) == '.' and
                    not self.is_square_attacked(Square.E1, False) and
                    not self.is_square_attacked(Square.D1, False) and
                    not self.is_square_attacked(Square.C1, False)):
                    moves.append(Move(Square.E1, Square.C1, MoveFlag.QUEEN_CASTLE))
        else:
            if self.castling_rights['k'] and square == Square.E8:
                if (self.get_piece_at(Square.F8) == '.' and 
                    self.get_piece_at(Square.G8) == '.' and
                    not self.is_square_attacked(Square.E8, True) and
                    not self.is_square_attacked(Square.F8, True) and
                    not self.is_square_attacked(Square.G8, True)):
                    moves.append(Move(Square.E8, Square.G8, MoveFlag.KING_CASTLE))

            if self.castling_rights['q'] and square == Square.E8:
                if (self.get_piece_at(Square.D8) == '.' and 
                    self.get_piece_at(Square.C8) == '.' and
                    self.get_piece_at(Square.B8) == '.' and
                    not self.is_square_attacked(Square.E8, True) and
                    not self.is_square_attacked(Square.D8, True) and
                    not self.is_square_attacked(Square.C8, True)):
                    moves.append(Move(Square.E8, Square.C8, MoveFlag.QUEEN_CASTLE))

        return moves

    def get_legal_moves(self) -> list[Move]:
        """Get all legal moves in the current position"""
        moves = []

        # Iterate through all squares
        for square_idx in range(64):
            square = Square.from_bitboard_square(square_idx)
            piece = self.get_piece_at(square)

            # Skip empty squares and opponent's pieces
            if piece == '.' or \
            (self.white_to_move and piece.islower()) or \
            (not self.white_to_move and piece.isupper()):
                continue

            # Generate moves based on piece type
            piece_type = piece.upper()
            if piece_type == 'P':
                moves.extend(self.get_legal_pawn_moves(square))
            elif piece_type == 'N':
                moves.extend(self.get_legal_knight_moves(square))
            elif piece_type == 'B':
                moves.extend(self.get_legal_sliding_moves(square, 
                    [self.NORTH_EAST, self.NORTH_WEST, self.SOUTH_EAST, self.SOUTH_WEST]))
            elif piece_type == 'R':
                moves.extend(self.get_legal_sliding_moves(square,
                    [self.NORTH, self.SOUTH, self.EAST, self.WEST]))
            elif piece_type == 'Q':
                moves.extend(self.get_legal_sliding_moves(square,
                    [self.NORTH, self.SOUTH, self.EAST, self.WEST,
                    self.NORTH_EAST, self.NORTH_WEST, self.SOUTH_EAST, self.SOUTH_WEST]))
            elif piece_type == 'K':
                moves.extend(self.get_legal_king_moves(square))

        # Filter out moves that would leave king in check
        legal_moves = []
        for move in moves:
            # Store board state
            old_state = self.__dict__.copy()

            # Try to make the move
            if self.make_move(move):
                legal_moves.append(move)

            # Restore board state
            self.__dict__ = old_state

        return legal_moves
