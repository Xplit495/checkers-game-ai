import pygame

class PieceView:
    def __init__(self, square_size):
        self.square_size = square_size
        self.radius = int(square_size * 0.4)

        self.white_outer = (255, 255, 255)
        self.white_inner = (220, 220, 220)
        self.black_outer = (0, 0, 0)
        self.black_inner = (50, 50, 50)
        self.king_marker = (212, 175, 55)

    def draw_piece(self, window, row, col, color, piece_type):
        x = col * self.square_size + self.square_size // 2
        y = row * self.square_size + self.square_size // 2

        outer_color = self.white_outer if color == "white" else self.black_outer
        inner_color = self.white_inner if color == "white" else self.black_inner

        pygame.draw.circle(window, outer_color, (x, y), self.radius)

        pygame.draw.circle(window, inner_color, (x, y), int(self.radius * 0.8))

        if piece_type == "dame":
            pygame.draw.circle(window, self.king_marker, (x, y), int(self.radius * 0.4))

    def draw_pieces(self, window, board_state):
        for position, piece in board_state.items():
            row, col = position
            self.draw_piece(window, row, col, piece["color"], piece["type"])

    def highlight_piece(self, window, row, col):
        x = col * self.square_size + self.square_size // 2
        y = row * self.square_size + self.square_size // 2

        highlight_color = (255, 255, 0)
        pygame.draw.circle(window, highlight_color, (x, y), self.radius + 5, 3)