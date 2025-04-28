import os
import sys

import pygame

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.board_view import BoardView
from players.human_player import HumanPlayer
from players.ai_player import AIPlayer
from game.constants import *
from visualization.stats_generator import StatsGenerator


def generate_stats():
    stats_generator = StatsGenerator()
    stats_files = stats_generator.generate_all_stats()

    if stats_files:
        print(f"Statistiques générées dans {stats_files}")


class GameWindow:
    BOARD_SIZE_PX = 800
    INFO_PANEL_WIDTH = 300
    WINDOW_WIDTH = BOARD_SIZE_PX + INFO_PANEL_WIDTH
    WINDOW_HEIGHT = BOARD_SIZE_PX

    BUTTON_COLOR = (100, 100, 100)
    BUTTON_HOVER_COLOR = (150, 150, 150)
    BUTTON_TEXT_COLOR = (255, 255, 255)

    def __init__(self):
        pygame.init()

        self.window = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        pygame.display.set_caption("Jeu de Dames")

        self.running = True
        self.needs_redraw = True

        self.game_mode = "human_vs_ai"
        self.active_player = WHITE

        self.human_player = HumanPlayer(WHITE)
        self.ai_player = AIPlayer(BLACK, difficulty="normal")

        self.board_view = BoardView(self.window, self.BOARD_SIZE_PX, self.INFO_PANEL_WIDTH)

        self.font = pygame.font.SysFont('Arial', 20)

        button_width = 200
        button_height = 40

        button_x = self.BOARD_SIZE_PX + (self.INFO_PANEL_WIDTH - button_width) // 2

        self.buttons = [
            {
                'rect': pygame.Rect(button_x, self.WINDOW_HEIGHT - 200, button_width, button_height),
                'text': 'Nouvelle Partie',
                'action': self.new_game
            },
            {
                'rect': pygame.Rect(button_x, self.WINDOW_HEIGHT - 150, button_width, button_height),
                'text': 'Changer de Mode',
                'action': self.toggle_game_mode
            },
            {
                'rect': pygame.Rect(button_x, self.WINDOW_HEIGHT - 100, button_width, button_height),
                'text': 'Générer Statistiques',
                'action': generate_stats
            },
            {
                'rect': pygame.Rect(button_x, self.WINDOW_HEIGHT - 50, button_width, button_height),
                'text': 'Quitter',
                'action': self.quit_game
            }
        ]

        self.ai_timer = 0
        self.ai_move_delay = 500

    def new_game(self):
        if hasattr(self.board_view.game_controller, 'game_recorder') and self.board_view.game_controller.game_recorder:
            winner = self.board_view.game_controller.winner
            self.board_view.game_controller.game_recorder.end_game(winner)

        self.board_view.game_controller.reset()
        self.active_player = WHITE
        self.needs_redraw = True

    def toggle_game_mode(self):
        if self.game_mode == "human_vs_human":
            self.game_mode = "human_vs_ai"
        else:
            self.game_mode = "human_vs_human"

        self.new_game()

    def quit_game(self):
        if hasattr(self.board_view.game_controller, 'game_recorder') and self.board_view.game_controller.game_recorder:
            self.board_view.game_controller.game_recorder.end_game(None)

        self.running = False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos

                for button in self.buttons:
                    if button['rect'].collidepoint(mouse_pos):
                        button['action']()
                        break
                else:
                    if self.game_mode == "human_vs_human" or (self.game_mode == "human_vs_ai" and self.active_player == WHITE):
                        if self.board_view.handle_click(mouse_pos):
                            self.active_player = BLACK if self.active_player == WHITE else WHITE
                        self.needs_redraw = True

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.new_game()

    def draw_buttons(self):
        mouse_pos = pygame.mouse.get_pos()

        for button in self.buttons:
            if button['rect'].collidepoint(mouse_pos):
                color = self.BUTTON_HOVER_COLOR
            else:
                color = self.BUTTON_COLOR

            pygame.draw.rect(self.window, color, button['rect'])
            pygame.draw.rect(self.window, (200, 200, 200), button['rect'], 2)

            text_surface = self.font.render(button['text'], True, self.BUTTON_TEXT_COLOR)
            text_rect = text_surface.get_rect(center=button['rect'].center)
            self.window.blit(text_surface, text_rect)

    def draw_game_info(self):
        mode_text = "Mode: Humain vs IA" if self.game_mode == "human_vs_ai" else "Mode: Humain vs Humain"
        mode_surface = self.font.render(mode_text, True, (255, 255, 255))
        self.window.blit(mode_surface, (self.BOARD_SIZE_PX + 20, 250))

        player_text = f"Tour: {'IA' if self.game_mode == 'human_vs_ai' and self.active_player == BLACK else 'Joueur'}"
        player_surface = self.font.render(player_text, True, (255, 255, 255))
        self.window.blit(player_surface, (self.BOARD_SIZE_PX + 20, 280))

    def handle_ai_move(self):
        if (self.game_mode == "human_vs_ai" and
            self.active_player == BLACK and
            not self.board_view.game_controller.game_over):

            current_time = pygame.time.get_ticks()

            if self.ai_timer == 0:
                self.ai_timer = current_time

            if current_time - self.ai_timer >= self.ai_move_delay:
                move = self.ai_player.select_move(self.board_view.game_controller)

                if move:
                    from_pos, to_pos = move

                    self.board_view.game_controller.select(from_pos[0], from_pos[1])

                    if self.board_view.game_controller.move(to_pos[0], to_pos[1]):
                        self.active_player = WHITE

                self.ai_timer = 0

                self.needs_redraw = True

    def run(self):
        while self.running:
            self.handle_events()

            self.handle_ai_move()

            if self.needs_redraw:
                self.window.fill((50, 50, 50))

                self.board_view.draw()

                self.draw_buttons()
                self.draw_game_info()

                pygame.display.flip()
                self.needs_redraw = False

            pygame.time.wait(30)

        if hasattr(self.board_view.game_controller, 'game_recorder') and self.board_view.game_controller.game_recorder:
            self.board_view.game_controller.game_recorder.end_game(self.board_view.game_controller.winner)

        pygame.quit()
        sys.exit()