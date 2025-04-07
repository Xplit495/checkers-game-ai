import pygame

class BoardView:
    LIGHT_SQUARE = (240, 217, 181)
    DARK_SQUARE = (181, 136, 99)

    INFO_BG_COLOR = (30, 30, 30)
    TEXT_COLOR = (255, 255, 255)

    BOARD_SIZE = 10

    def __init__(self, window, board_size_px, info_panel_width):
        self.window = window
        self.board_size_px = board_size_px
        self.info_panel_width = info_panel_width
        self.square_size = board_size_px // self.BOARD_SIZE

        self.font = pygame.font.SysFont('Arial', 24)

        from ui.piece_view import PieceView
        self.piece_view = PieceView(self.square_size)

        self.test_game_state = {
            'current_player': 'white',
            'white_pieces': 20,
            'black_pieces': 20,
            'board': self.create_test_board()
        }

    def create_test_board(self):
        test_board = {}
        for row in range(0, 4):
            for col in range(10):
                if (row + col) % 2 == 1:
                    test_board[(row, col)] = {"color": "black", "type": "pion"}

        for row in range(6, 10):
            for col in range(10):
                if (row + col) % 2 == 1:
                    test_board[(row, col)] = {"color": "white", "type": "pion"}

        test_board[(4, 5)] = {"color": "white", "type": "dame"}
        test_board[(5, 2)] = {"color": "black", "type": "dame"}

        return test_board

    def draw_board(self):
        for row in range(self.BOARD_SIZE):
            for col in range(self.BOARD_SIZE):
                if (row + col) % 2 == 0:
                    color = self.LIGHT_SQUARE
                else:
                    color = self.DARK_SQUARE

                pygame.draw.rect(
                    self.window,
                    color,
                    (col * self.square_size, row * self.square_size,
                     self.square_size, self.square_size)
                )

    def draw_info_panel(self):
        info_panel_rect = pygame.Rect(
            self.board_size_px, 0,
            self.info_panel_width, self.board_size_px
        )
        pygame.draw.rect(self.window, self.INFO_BG_COLOR, info_panel_rect)

        turn_text = f"Tour: {'Blanc' if self.test_game_state['current_player'] == 'white' else 'Noir'}"
        turn_surface = self.font.render(turn_text, True, self.TEXT_COLOR)
        self.window.blit(turn_surface, (self.board_size_px + 20, 50))

        white_text = f"Pièces blanches: {self.test_game_state['white_pieces']}"
        white_surface = self.font.render(white_text, True, self.TEXT_COLOR)
        self.window.blit(white_surface, (self.board_size_px + 20, 100))

        black_text = f"Pièces noires: {self.test_game_state['black_pieces']}"
        black_surface = self.font.render(black_text, True, self.TEXT_COLOR)
        self.window.blit(black_surface, (self.board_size_px + 20, 150))

    def draw(self):
        self.draw_board()

        self.piece_view.draw_pieces(self.window, self.test_game_state['board'])

        self.draw_info_panel()