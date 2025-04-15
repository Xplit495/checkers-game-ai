import numpy as np

from game.constants import *
from game.piece import Piece


class Board:
    def __init__(self):
        self.reset()

    def reset(self):
        self.board = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=object)

        for row in range(0, 4):
            for col in range(BOARD_SIZE):
                if (row + col) % 2 == 1:
                    self.board[row, col] = Piece(BLACK, PION)

        for row in range(6, BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if (row + col) % 2 == 1:
                    self.board[row, col] = Piece(WHITE, PION)

    def is_valid_position(self, row, col):
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

    def get_piece(self, row, col):
        if self.is_valid_position(row, col):
            return self.board[row, col]
        return None

    def set_piece(self, row, col, piece):
        if self.is_valid_position(row, col):
            self.board[row, col] = piece

    def remove_piece(self, row, col):
        if self.is_valid_position(row, col):
            self.board[row, col] = 0

    def move_piece(self, from_row, from_col, to_row, to_col):
        piece = self.get_piece(from_row, from_col)
        if piece:
            self.set_piece(to_row, to_col, piece)
            self.remove_piece(from_row, from_col)
            return True
        return False

    def get_valid_moves(self, row, col, color):
        piece = self.get_piece(row, col)
        valid_moves = {}

        if piece and piece.color == color:
            captures = self._get_captures(row, col)
            if captures:
                return captures

            if piece.type == PION:
                directions = [(-1, -1), (-1, 1)] if color == WHITE else [(1, -1), (1, 1)]

                for dir_row, dir_col in directions:
                    new_row, new_col = row + dir_row, col + dir_col
                    if self.is_valid_position(new_row, new_col) and self.get_piece(new_row, new_col) == 0:
                        valid_moves[(new_row, new_col)] = []
            else:
                directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

                for dir_row, dir_col in directions:
                    new_row, new_col = row + dir_row, col + dir_col

                    while (self.is_valid_position(new_row, new_col) and
                           self.get_piece(new_row, new_col) == 0):
                        valid_moves[(new_row, new_col)] = []
                        new_row += dir_row
                        new_col += dir_col

        return valid_moves

    def _get_captures(self, row, col):
        piece = self.get_piece(row, col)
        captures = {}

        if not piece:
            return captures

        if piece.type == PION:
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

                        temp_board = self.copy()
                        temp_board.move_piece(row, col, jump_row, jump_col)
                        temp_board.remove_piece(new_row, new_col)
                        next_captures = temp_board._get_captures(jump_row, jump_col)

                        for next_pos, next_captured in next_captures.items():
                            captures[next_pos] = [(new_row, new_col)] + next_captured
        else:
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

            for dir_row, dir_col in directions:
                r, c = row + dir_row, col + dir_col
                opponent_found = False
                opponent_pos = None

                while self.is_valid_position(r, c):
                    current_piece = self.get_piece(r, c)

                    if current_piece == 0:
                        r += dir_row
                        c += dir_col
                        continue

                    if current_piece.color == piece.color:
                        break

                    opponent_found = True
                    opponent_pos = (r, c)
                    r += dir_row
                    c += dir_col
                    break

                if opponent_found:
                    while self.is_valid_position(r, c):
                        if self.get_piece(r, c) == 0:
                            captures[(r, c)] = [opponent_pos]

                            temp_board = self.copy()
                            temp_board.move_piece(row, col, r, c)
                            temp_board.remove_piece(opponent_pos[0], opponent_pos[1])
                            next_captures = temp_board._get_captures(r, c)

                            for next_pos, next_captured in next_captures.items():
                                captures[next_pos] = [opponent_pos] + next_captured
                        else:
                            break

                        r += dir_row
                        c += dir_col

        return captures

    def copy(self):
        new_board = Board()
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                new_board.board[row, col] = self.board[row, col]
        return new_board

    def to_dict(self):
        board_dict = {}
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.get_piece(row, col)
                if piece:
                    board_dict[(row, col)] = {"color": piece.color, "type": piece.type}
        return board_dict