class Piece:
    def __init__(self, color, piece_type):
        self.color = color
        self.type = piece_type

    def promote(self):
        from game.constants import DAME
        self.type = DAME