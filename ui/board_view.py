import os
import sys

import pygame

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game.constants import *
from game.game_controller import GameController

class BoardView:
    LIGHT_SQUARE = (240, 217, 181)
    DARK_SQUARE = (181, 136, 99)
    HIGHLIGHT_COLOR = (255, 255, 0, 100)

    INFO_BG_COLOR = (30, 30, 30)
    TEXT_COLOR = (255, 255, 255)

    def __init__(self, window, board_size_px, info_panel_width):
        self.window = window
        self.board_size_px = board_size_px
        self.info_panel_width = info_panel_width
        self.square_size = board_size_px // BOARD_SIZE

        self.font = pygame.font.SysFont('Arial', 24)
        self.small_font = pygame.font.SysFont('Arial', 18)

        from ui.piece_view import PieceView
        self.piece_view = PieceView(self.square_size)

        self.game_controller = GameController()
        self.game_state = self.game_controller.get_game_state()

    def draw_board(self):
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
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

        for i in range(BOARD_SIZE):
            text = self.small_font.render(str(i), True, (0, 0, 0))
            self.window.blit(text, (5, i * self.square_size + self.square_size//2 - 8))

            text = self.small_font.render(chr(97 + i), True, (0, 0, 0))
            self.window.blit(text, (i * self.square_size + self.square_size//2 - 5, self.board_size_px - 20))

    def draw_info_panel(self):
        info_panel_rect = pygame.Rect(
            self.board_size_px, 0,
            self.info_panel_width, self.board_size_px
        )
        pygame.draw.rect(self.window, self.INFO_BG_COLOR, info_panel_rect)

        turn_text = f"Tour: {'Blanc' if self.game_state['current_player'] == WHITE else 'Noir'}"
        turn_surface = self.font.render(turn_text, True, self.TEXT_COLOR)
        self.window.blit(turn_surface, (self.board_size_px + 20, 50))

        white_text = f"Pièces blanches: {self.game_state['white_pieces']}"
        white_surface = self.font.render(white_text, True, self.TEXT_COLOR)
        self.window.blit(white_surface, (self.board_size_px + 20, 100))

        black_text = f"Pièces noires: {self.game_state['black_pieces']}"
        black_surface = self.font.render(black_text, True, self.TEXT_COLOR)
        self.window.blit(black_surface, (self.board_size_px + 20, 150))

        if hasattr(self.game_controller, 'captures_available') and self.game_controller.captures_available:
            captures_text = "Captures disponibles!"
            captures_surface = self.font.render(captures_text, True, (255, 150, 0))
            self.window.blit(captures_surface, (self.board_size_px + 20, 200))

        if self.game_state['game_over']:
            game_over_text = f"Partie terminée! Vainqueur: {'Blanc' if self.game_state['winner'] == WHITE else 'Noir'}"
            game_over_surface = self.font.render(game_over_text, True, self.TEXT_COLOR)
            self.window.blit(game_over_surface, (self.board_size_px + 20, 200))

    def highlight_valid_moves(self):
        if self.game_state['selected']:
            row, col = self.game_state['selected']
            self.piece_view.highlight_piece(self.window, row, col)

            for move in self.game_state['valid_moves']:
                move_row, move_col = move
                x = move_col * self.square_size + self.square_size // 2
                y = move_row * self.square_size + self.square_size // 2

                pygame.draw.circle(
                    self.window,
                    self.HIGHLIGHT_COLOR,
                    (x, y),
                    self.square_size // 4
                )

    def draw(self):
        self.game_state = self.game_controller.get_game_state()

        self.draw_board()

        self.piece_view.draw_pieces(self.window, self.game_state['board'])

        self.highlight_valid_moves()

        self.draw_info_panel()

    def handle_click(self, pos):
        x, y = pos

        if x >= self.board_size_px:
            return False

        col = x // self.square_size
        row = y // self.square_size

        move_made = False

        if self.game_state['selected']:
            if (row, col) in self.game_state['valid_moves']:
                self.game_controller.move(row, col)
                move_made = True
            else:
                self.game_controller.select(row, col)
        else:
            self.game_controller.select(row, col)

        return move_made