from enum import IntEnum

class Square(IntEnum):
    """Chess square coordinates using 0x88 representation"""
    A1, B1, C1, D1, E1, F1, G1, H1 = 0, 1, 2, 3, 4, 5, 6, 7
    A2, B2, C2, D2, E2, F2, G2, H2 = 16, 17, 18, 19, 20, 21, 22, 23
    A3, B3, C3, D3, E3, F3, G3, H3 = 32, 33, 34, 35, 36, 37, 38, 39
    A4, B4, C4, D4, E4, F4, G4, H4 = 48, 49, 50, 51, 52, 53, 54, 55
    A5, B5, C5, D5, E5, F5, G5, H5 = 64, 65, 66, 67, 68, 69, 70, 71
    A6, B6, C6, D6, E6, F6, G6, H6 = 80, 81, 82, 83, 84, 85, 86, 87
    A7, B7, C7, D7, E7, F7, G7, H7 = 96, 97, 98, 99, 100, 101, 102, 103
    A8, B8, C8, D8, E8, F8, G8, H8 = 112, 113, 114, 115, 116, 117, 118, 119

    @property
    def rank(self) -> int:
        """Get the rank (0-7) of the square for bitboard operations"""
        return self.value >> 4

    @property
    def file(self) -> int:
        """Get the file (0-7) of the square"""
        return self.value & 7

    @property
    def rank_1based(self) -> int:
        """Get the rank (1-8) of the square for chess notation"""
        return self.rank + 1

    @property
    def file_char(self) -> str:
        """Get the file letter (a-h) of the square"""
        return chr(ord('a') + self.file)

    @property
    def notation(self) -> str:
        """Get the algebraic notation of the square ('e4', 'e5', etc.)"""
        return f'{self.file_char}{self.rank_1based}'

    @classmethod
    def from_notation(cls, notation: str) -> 'Square':
        """Create a Square from algebraic notation"""
        if not (len(notation) == 2 and
                'a' <= notation[0] <= 'h' and 
                '1' <= notation[1] <= '8'):
            raise ValueError(f"Invalid square notation: {notation}")

        file = ord(notation[0]) - ord('a')
        rank = int(notation[1]) - 1
        return cls(rank * 16 + file)

    @classmethod
    def from_coords(cls, rank: int, file: int) -> 'Square':
        """Create a Square from rank and file coordinates"""
        if not (0 <= rank <= 7 and 0 <= file <= 7):
            raise ValueError(f"Invalid coordinates: rank={rank}, file={file}")
        return cls(rank * 16 + file)

    def __int__(self) -> int:
        """Convert to 0-63 square index for bitboard operations"""
        return self.rank * 8 + self.file

    @classmethod
    def from_bitboard_square(cls, square: int) -> 'Square':
        """Create a Square from a 0-63 square index"""
        if not 0 <= square <= 63:
            raise ValueError(f"Invalid bitboard square: {square}")
        rank = square // 8
        file = square % 8
        return cls.from_coords(rank, file)
