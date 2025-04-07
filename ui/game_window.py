import pygame
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.board_view import BoardView

class GameWindow:
    BOARD_SIZE_PX = 800
    INFO_PANEL_WIDTH = 300
    WINDOW_WIDTH = BOARD_SIZE_PX + INFO_PANEL_WIDTH
    WINDOW_HEIGHT = BOARD_SIZE_PX

    def __init__(self):
        pygame.init()

        self.window = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        pygame.display.set_caption("Jeu de Dames")

        self.running = True
        self.needs_redraw = True

        self.board_view = BoardView(self.window, self.BOARD_SIZE_PX, self.INFO_PANEL_WIDTH)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Gérer le clic gauche de la souris
                self.board_view.handle_click(event.pos)
                self.needs_redraw = True

            # Touche "r" pour réinitialiser le jeu
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.board_view.game_controller.reset()
                self.needs_redraw = True

    def run(self):
        while self.running:
            self.handle_events()

            if self.needs_redraw:
                self.window.fill((50, 50, 50))

                self.board_view.draw()

                pygame.display.flip()
                self.needs_redraw = False

            pygame.time.wait(100)

        pygame.quit()
        sys.exit()