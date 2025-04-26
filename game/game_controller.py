from game.board import Board
from game.constants import *
from data_management.game_recorder import GameRecorder

class GameController:
    def __init__(self, create_recorder=True):
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

        if create_recorder:
            self.game_recorder = GameRecorder(auto_save=True, save_interval=3)
        else:
            self.game_recorder = None

    def reset(self):
        if hasattr(self, 'game_recorder') and self.game_recorder:
            if self.game_over:
                self.game_recorder.end_game(self.winner)
            else:
                self.game_recorder.end_game(None)

        self.board.reset()
        self.current_player = WHITE
        self.selected_piece = None
        self.valid_moves = {}
        self.captures_available = False
        self.game_over = False
        self.winner = None
        self.piece_count = {WHITE: 20, BLACK: 20}

        self.game_recorder = GameRecorder(auto_save=True, save_interval=3)

    def check_captures_available(self):
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board.get_piece(row, col)
                if piece and piece.color == self.current_player:
                    captures = self.board._get_captures(row, col)
                    if captures:
                        return True
        return False

    def can_piece_capture(self, row, col):
        captures = self.board._get_captures(row, col)
        return bool(captures)

    def select(self, row, col):
        if self.selected_piece == (row, col):
            self.selected_piece = None
            self.valid_moves = {}
            return False

        self.captures_available = self.check_captures_available()

        piece = self.board.get_piece(row, col)
        if piece and piece.color == self.current_player:
            if self.captures_available and not self.can_piece_capture(row, col):
                return False

            self.selected_piece = (row, col)
            self.valid_moves = self.board.get_valid_moves(row, col, self.current_player)
            return True

        return False

    def _classify_move(self, from_pos, to_pos, piece_type, captures, promotion):
        move_count = self.game_recorder.move_count if hasattr(self, 'game_recorder') and self.game_recorder else 0
        total_pieces = self.piece_count[WHITE] + self.piece_count[BLACK]

        if move_count < 8:
            classification = "opening"
        elif total_pieces < 15:
            classification = "end_game"
        else:
            classification = "middle_game"

        if captures:
            if len(captures) > 1:
                classification = "multiple_capture"
            else:
                classification = "capture"

        if promotion:
            if captures:
                classification = "capture_promotion"
            else:
                classification = "promotion"

        if piece_type == DAME:
            if "capture" in classification:
                classification = "king_" + classification

        return classification

    def _calculate_move_score(self, piece_type, captures, promotion, to_pos):
        score = 0

        base_score = 5 if piece_type == PION else 7

        if captures:
            capture_score = len(captures) * 10
            score += capture_score

        if promotion:
            score += 15

        to_row, to_col = to_pos
        center_distance = abs(to_row - BOARD_SIZE//2) + abs(to_col - BOARD_SIZE//2)
        center_score = max(0, (BOARD_SIZE - center_distance) * 0.5)
        score += center_score

        if piece_type == DAME:
            if to_row == 0 or to_row == BOARD_SIZE-1 or to_col == 0 or to_col == BOARD_SIZE-1:
                score += 5

        return base_score + score

    def move(self, row, col):
        if self.selected_piece and (row, col) in self.valid_moves:
            from_row, from_col = self.selected_piece
            from_pos = (from_row, from_col)
            to_pos = (row, col)

            piece = self.board.get_piece(from_row, from_col)
            piece_type = piece.type if piece else None

            captured = self.valid_moves[(row, col)]
            was_promoted = False

            if captured:
                for capt_row, capt_col in captured:
                    self.board.remove_piece(capt_row, capt_col)
                    self.piece_count[BLACK if self.current_player == WHITE else WHITE] -= 1

            self.board.move_piece(from_row, from_col, row, col)

            piece = self.board.get_piece(row, col)
            if piece and piece.type == PION:
                if (piece.color == WHITE and row == 0) or (piece.color == BLACK and row == BOARD_SIZE-1):
                    piece.type = DAME
                    was_promoted = True

            if hasattr(self, 'game_recorder') and self.game_recorder:
                move_classification = self._classify_move(from_pos, to_pos, piece_type, captured, was_promoted)

                move_score = self._calculate_move_score(piece_type, captured, was_promoted, to_pos)

                self.game_recorder.record_move(
                    player=self.current_player,
                    from_pos=from_pos,
                    to_pos=to_pos,
                    piece_type=piece_type,
                    captures=captured,
                    promotion=was_promoted,
                    classification=move_classification,
                    move_score=move_score
                )

                self.game_recorder.save_moves()

            self.selected_piece = None
            self.valid_moves = {}

            if self.piece_count[BLACK] == 0:
                self.game_over = True
                self.winner = WHITE
                if hasattr(self, 'game_recorder') and self.game_recorder:
                    self.game_recorder.end_game(self.winner)
            elif self.piece_count[WHITE] == 0:
                self.game_over = True
                self.winner = BLACK
                if hasattr(self, 'game_recorder') and self.game_recorder:
                    self.game_recorder.end_game(self.winner)

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