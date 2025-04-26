class Player:
    def __init__(self, color, name=None):
        self.color = color
        self.name = name or f"Joueur {color}"

    def select_move(self, game_controller):
        raise NotImplementedError("Cette méthode doit être implémentée par une sous-classe")