from game.board import Board
from game.constants import *

class GameController:
    def __init__(self):
        self.board = Board()
        self.current_player = WHITE
        self.selected_piece = None
        self.valid_moves = {}
        self.captures_available = False
        self.game_over = False
        self.winner = None

        self.piece_count = {
            WHITE: 20,
            BLACK: 20
        }

    def reset(self):
        self.board.reset()
        self.current_player = WHITE
        self.selected_piece = None
        self.valid_moves = {}
        self.captures_available = False
        self.game_over = False
        self.winner = None
        self.piece_count = {WHITE: 20, BLACK: 20}

    def select(self, row, col):
        if self.selected_piece == (row, col):
            self.selected_piece = None
            self.valid_moves = {}
            return False

        piece = self.board.get_piece(row, col)
        if piece and piece.color == self.current_player:
            self.selected_piece = (row, col)
            self.valid_moves = self.board.get_valid_moves(row, col, self.current_player)
            return True

        return False

    def move(self, row, col):
        if self.selected_piece and (row, col) in self.valid_moves:
            from_row, from_col = self.selected_piece
            piece = self.board.get_piece(from_row, from_col)
            piece_type = piece.type if piece else None

            captured = self.valid_moves[(row, col)]
            if captured:
                for capt_row, capt_col in captured:
                    self.board.remove_piece(capt_row, capt_col)
                    self.piece_count[BLACK if self.current_player == WHITE else WHITE] -= 1

            self.board.move_piece(from_row, from_col, row, col)

            piece = self.board.get_piece(row, col)
            if piece and piece.type == PION:
                if (piece.color == WHITE and row == 0) or (piece.color == BLACK and row == BOARD_SIZE-1):
                    piece.type = DAME

            self.selected_piece = None
            self.valid_moves = {}

            if self.piece_count[BLACK] == 0:
                self.game_over = True
                self.winner = WHITE
            elif self.piece_count[WHITE] == 0:
                self.game_over = True
                self.winner = BLACK

            self.current_player = BLACK if self.current_player == WHITE else WHITE

            return True

        return False

    def get_game_state(self):
        return {
            'current_player': self.current_player,
            'white_pieces': self.piece_count[WHITE],
            'black_pieces': self.piece_count[BLACK],
            'board': self.board.to_dict(),
            'selected': self.selected_piece,
            'valid_moves': list(self.valid_moves.keys()) if self.valid_moves else [],
            'game_over': self.game_over,
            'winner': self.winner
        }