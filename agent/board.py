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

    def is_square_attacked(self, square: Square, by_white: str):
        """Checks if a square is attacked by any piece of the given color"""
        for i in range(64):
            piece = self.get_piece_at(i)
            if piece == '.':
                continue

            is_white_piece = piece.isupper()
            if is_white_piece != by_white:
                continue

            if self.get_attacks(i) & (1 << int(square)):
                return True

        return False

    def is_in_check(self, white: str):
        """Determines if the given side is in check"""
        king_square = None
        king_bb = self.white_king if white else self.black_king

        # Find king's square
        for i in range(64):
            if king_bb & (1 << i):
                king_square = i
                break

        return self.is_square_attacked(king_square, not white)

    def generate_pseudo_legal_moves(self) -> list[Move]:
        """Generates all pseudo-legal moves in the current position"""
        moves = []
        side_pieces = self.white_pieces if self.white_to_move else self.black_pieces

        for bb_square in range(64):
            if not (side_pieces & (1 << bb_square)):
                continue

            from_square = Square.from_bitboard_square(bb_square)
            piece = self.get_piece_at(from_square)

            # Get attacked squares
            attacks = self.get_attacks(from_square)

            # Filter out attacks on own pieces
            if self.white_to_move:
                attacks &= ~self.white_pieces
            else:
                attacks &= ~self.black_pieces

            # Generate moves from attacks
            for to_bb_square in range(64):
                if attacks & (1 << to_bb_square):
                    to_square = Square.from_bitboard_square(to_bb_square)
                    target_piece = self.get_piece_at(to_square)

                    # Determine move flag
                    flag = MoveFlag.QUIET
                    if target_piece != '.':
                        flag = MoveFlag.CAPTURE

                    # Handle pawn moves
                    if piece.upper() == 'P':
                        # Promotions
                        if (self.white_to_move and to_square.rank == 8) or \
                           (not self.white_to_move and to_square.rank == 1):
                            promotion_flags = (
                                MoveFlag.PROMOTION_Q,
                                MoveFlag.PROMOTION_R,
                                MoveFlag.PROMOTION_B,
                                MoveFlag.PROMOTION_N
                            ) if flag == MoveFlag.QUIET else (
                                MoveFlag.PROMOTION_CAPTURE_Q,
                                MoveFlag.PROMOTION_CAPTURE_R,
                                MoveFlag.PROMOTION_CAPTURE_B,
                                MoveFlag.PROMOTION_CAPTURE_N
                            )
                            for promotion_flag in promotion_flags:
                                moves.append(Move(from_square, to_square, promotion_flag))
                            continue

                        # En passant
                        if self.en_passant_target == to_square:
                            flag = MoveFlag.EN_PASSANT

                    # Handle castling
                    elif piece.upper() == 'K':
                        if self.white_to_move:
                            if (from_square == Square.E1 and to_square == Square.G1 and
                                self.castling_rights['K']):
                                flag = MoveFlag.KING_CASTLE
                            elif (from_square == Square.E1 and to_square == Square.C1 and
                                  self.castling_rights['Q']):
                                flag = MoveFlag.QUEEN_CASTLE
                        else:
                            if (from_square == Square.E8 and to_square == Square.G8 and
                                self.castling_rights['k']):
                                flag = MoveFlag.KING_CASTLE
                            elif (from_square == Square.E8 and to_square == Square.C8 and
                                  self.castling_rights['q']):
                                flag = MoveFlag.QUEEN_CASTLE

                    moves.append(Move(from_square, to_square, flag))

            # Add pawn double pushes
            if piece.upper() == 'P':
                if (self.white_to_move and from_square.rank == 2) or \
                   (not self.white_to_move and from_square.rank == 7):
                    double_push_square = Square.from_coords(
                        from_square.rank + (2 if self.white_to_move else -2),
                        from_square.file
                    )
                    if self.get_piece_at(double_push_square) == '.':
                        moves.append(Move(from_square, double_push_square, MoveFlag.DOUBLE_PAWN_PUSH))

        return moves

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

            # Add promoted piece
            promotion_piece = move.get_promotion_piece()
            target_bb = f"{'white' if self.white_to_move else 'black'}_{promotion_piece.lower()}s"
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

    def is_checkmate(self):
        """Determines if the current position is checkmate"""
        if not self.is_in_check(self.white_to_move):
            return False

        # Try all possible moves
        for move in self.generate_pseudo_legal_moves():
            old_state = self.__dict__.copy()
            if self.make_move(*move):
                self.__dict__ = old_state
                return False
            self.__dict__ = old_state

        return True

    def is_stalemate(self):
        """Determines if the current position is stalemate"""
        if self.is_in_check(self.white_to_move):
            return False

        # Try all possible moves
        for move in self.generate_pseudo_legal_moves():
            old_state = self.__dict__.copy()
            if self.make_move(move):
                self.__dict__ = old_state
                return False
            self.__dict__ = old_state

        return True
