from players.player import Player

class HumanPlayer(Player):
    def __init__(self, color, name=None):
        super().__init__(color, name)

    def select_move(self, game_controller):
        return None