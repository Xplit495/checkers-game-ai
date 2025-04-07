import numpy as np
from game.constants import *
from game.piece import Piece

class Board:
    def __init__(self):
        self.reset()

    def reset(self):
        """Réinitialise le plateau avec la position de départ"""
        self.board = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=object)

        # Placement des pions noirs (rangées 0-3)
        for row in range(0, 4):
            for col in range(BOARD_SIZE):
                if (row + col) % 2 == 1:
                    self.board[row, col] = Piece(BLACK, PION)

        # Placement des pions blancs (rangées 6-9)
        for row in range(6, BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if (row + col) % 2 == 1:
                    self.board[row, col] = Piece(WHITE, PION)

    def is_valid_position(self, row, col):
        """Vérifie si une position est valide sur le plateau"""
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

    def get_piece(self, row, col):
        """Récupère la pièce à la position donnée"""
        if self.is_valid_position(row, col):
            return self.board[row, col]
        return None

    def set_piece(self, row, col, piece):
        """Place une pièce à la position donnée"""
        if self.is_valid_position(row, col):
            self.board[row, col] = piece

    def remove_piece(self, row, col):
        """Enlève une pièce de la position donnée"""
        if self.is_valid_position(row, col):
            self.board[row, col] = 0

    def move_piece(self, from_row, from_col, to_row, to_col):
        """Déplace une pièce d'une position à une autre"""
        piece = self.get_piece(from_row, from_col)
        if piece:
            self.set_piece(to_row, to_col, piece)
            self.remove_piece(from_row, from_col)

            # Vérifier si le pion atteint la ligne opposée pour devenir une dame
            if piece.color == WHITE and to_row == 0 and piece.type == PION:
                piece.type = DAME
            elif piece.color == BLACK and to_row == BOARD_SIZE-1 and piece.type == PION:
                piece.type = DAME

            return True
        return False

    def get_valid_moves(self, row, col, color):
        """Récupère tous les mouvements valides pour une pièce"""
        piece = self.get_piece(row, col)
        valid_moves = {}

        if piece and piece.color == color:
            # Vérifie les captures d'abord (obligatoires)
            captures = self._get_captures(row, col)
            if captures:
                return captures

            # Si pas de captures possibles, vérifie les mouvements simples
            if piece.type == PION:
                directions = [(-1, -1), (-1, 1)] if color == WHITE else [(1, -1), (1, 1)]
            else:  # Dame
                directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

            for dir_row, dir_col in directions:
                new_row, new_col = row + dir_row, col + dir_col
                if self.is_valid_position(new_row, new_col) and self.get_piece(new_row, new_col) == 0:
                    valid_moves[(new_row, new_col)] = []

        return valid_moves

    def _get_captures(self, row, col):
        """Récupère toutes les captures possibles pour une pièce"""
        piece = self.get_piece(row, col)
        captures = {}

        if not piece:
            return captures

        if piece.type == PION:
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        else:  # Dame
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

        for dir_row, dir_col in directions:
            new_row, new_col = row + dir_row, col + dir_col
            if (self.is_valid_position(new_row, new_col) and
                self.get_piece(new_row, new_col) and
                self.get_piece(new_row, new_col).color != piece.color):
                jump_row, jump_col = new_row + dir_row, new_col + dir_col
                if (self.is_valid_position(jump_row, jump_col) and
                    self.get_piece(jump_row, jump_col) == 0):
                    captures[(jump_row, jump_col)] = [(new_row, new_col)]

                    # Vérifier les captures multiples
                    temp_board = self.copy()
                    temp_board.move_piece(row, col, jump_row, jump_col)
                    temp_board.remove_piece(new_row, new_col)
                    next_captures = temp_board._get_captures(jump_row, jump_col)

                    for next_pos, next_captured in next_captures.items():
                        captures[next_pos] = [(new_row, new_col)] + next_captured

        return captures

    def copy(self):
        """Crée une copie du plateau actuel"""
        new_board = Board()
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                new_board.board[row, col] = self.board[row, col]
        return new_board

    def to_dict(self):
        """Convertit le plateau en dictionnaire pour l'affichage"""
        board_dict = {}
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.get_piece(row, col)
                if piece:
                    board_dict[(row, col)] = {"color": piece.color, "type": piece.type}
        return board_dict