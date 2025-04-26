import random
import numpy as np
import pandas as pd
from game.constants import *
from data_management.data_processor import DataProcessor
from players.player import Player

class AIPlayer(Player):
    def __init__(self, color, difficulty="normal"):
        super().__init__(color)
        self.difficulty = difficulty
        self.data_processor = DataProcessor()

        self.weights = {
            "easy": {
                "material": 0.5,
                "position": 0.3,
                "history": 0.1,
                "captures": 0.3,
                "king": 0.2,
                "classification": 0.2
            },
            "normal": {
                "material": 0.7,
                "position": 0.6,
                "history": 0.5,
                "captures": 0.6,
                "king": 0.5,
                "classification": 0.5
            },
            "hard": {
                "material": 1.0,
                "position": 0.8,
                "history": 0.8,
                "captures": 0.9,
                "king": 0.7,
                "classification": 0.8
            }
        }

        self.classification_weights = {
            "opening": 0.6,
            "middle_game": 0.5,
            "end_game": 0.7,
            "capture": 0.8,
            "multiple_capture": 1.0,
            "promotion": 0.7,
            "capture_promotion": 0.9,
            "king_capture": 0.85
        }

    def select_move(self, game_controller):
        possible_moves = self._get_possible_moves(game_controller)

        if not possible_moves:
            return None

        evaluated_moves = self._evaluate_moves(game_controller, possible_moves)

        if self.difficulty == "easy":
            random_factor = 0.3
        elif self.difficulty == "normal":
            random_factor = 0.1
        else:
            random_factor = 0.02

        for move in evaluated_moves:
            evaluated_moves[move] += random.uniform(0, random_factor * 10)

        best_move = max(evaluated_moves.items(), key=lambda x: x[1])
        from_pos, to_pos = best_move[0]

        return from_pos, to_pos

    def _get_possible_moves(self, game_controller):
        possible_moves = {}

        captures_available = game_controller.check_captures_available()

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = game_controller.board.get_piece(row, col)

                if piece and piece.color == self.color:
                    if captures_available and not game_controller.can_piece_capture(row, col):
                        continue

                    valid_moves = game_controller.board.get_valid_moves(row, col, self.color)

                    for to_pos, captures in valid_moves.items():
                        from_pos = (row, col)
                        possible_moves[(from_pos, to_pos)] = 0

        return possible_moves

    def _evaluate_moves(self, game_controller, possible_moves):
        evaluated_moves = possible_moves.copy()

        total_pieces = game_controller.piece_count[WHITE] + game_controller.piece_count[BLACK]
        move_count = game_controller.game_recorder.move_count if hasattr(game_controller, 'game_recorder') and game_controller.game_recorder else 0

        if move_count < 8:
            game_phase = "opening"
        elif total_pieces < 15:
            game_phase = "end_game"
        else:
            game_phase = "middle_game"

        for move, _ in evaluated_moves.items():
            (from_pos, to_pos) = move
            from_row, from_col = from_pos
            to_row, to_col = to_pos

            from game.game_controller import GameController
            test_controller = GameController(create_recorder=False)
            test_controller.board = game_controller.board.copy()
            test_controller.current_player = self.color
            test_controller.piece_count = game_controller.piece_count.copy()

            piece = test_controller.board.get_piece(from_row, from_col)
            test_controller.selected_piece = from_pos
            test_controller.valid_moves = test_controller.board.get_valid_moves(from_row, from_col, self.color)

            captures = game_controller.board.get_valid_moves(from_row, from_col, self.color).get(to_pos, [])
            could_promote = False
            if piece and piece.type == PION:
                if (self.color == WHITE and to_row == 0) or (self.color == BLACK and to_row == BOARD_SIZE-1):
                    could_promote = True

            move_classification = self._determine_move_classification(
                from_pos, to_pos, piece.type if piece else PION,
                captures, could_promote, game_phase
            )

            test_controller.move(to_row, to_col)

            score = 0

            material_score = self._evaluate_material(test_controller)
            score += material_score * self.weights[self.difficulty]["material"]

            position_score = self._evaluate_position(to_row, to_col, piece.type if piece else PION, game_phase)
            score += position_score * self.weights[self.difficulty]["position"]

            capture_score = len(captures) * 10
            if len(captures) > 1:
                capture_score *= 1.5
            score += capture_score * self.weights[self.difficulty]["captures"]

            promotion_score = 0
            if could_promote:
                promotion_score = 15
            score += promotion_score * self.weights[self.difficulty]["king"]

            classification_score = self.classification_weights.get(move_classification, 0.5) * 10
            score += classification_score * self.weights[self.difficulty]["classification"]

            history_score = self._evaluate_from_history(game_controller, from_pos, to_pos, move_classification)
            score += history_score * self.weights[self.difficulty]["history"]

            evaluated_moves[move] = score

        return evaluated_moves

    def _determine_move_classification(self, from_pos, to_pos, piece_type, captures, promotion, game_phase):
        classification = game_phase

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
                classification = "king_capture"

        return classification

    def _evaluate_material(self, game_controller):
        opponent_color = BLACK if self.color == WHITE else WHITE

        my_pieces = game_controller.piece_count[self.color]
        opponent_pieces = game_controller.piece_count[opponent_color]

        my_kings = 0
        opponent_kings = 0

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = game_controller.board.get_piece(row, col)
                if piece:
                    if piece.color == self.color and piece.type == DAME:
                        my_kings += 1
                    elif piece.color == opponent_color and piece.type == DAME:
                        opponent_kings += 1

        my_value = my_pieces + (my_kings * 0.5)
        opponent_value = opponent_pieces + (opponent_kings * 0.5)

        return my_value - opponent_value

    def _evaluate_position(self, row, col, piece_type, game_phase):
        score = 0

        center_value = 4 - (abs(row - BOARD_SIZE//2) + abs(col - BOARD_SIZE//2)) / 2

        if game_phase == "opening":
            score += center_value * 0.8
        elif game_phase == "middle_game":
            score += center_value * 0.5
        else:
            score += center_value * 0.3

        if piece_type == DAME:
            edge_value = 0
            if row == 0 or row == BOARD_SIZE-1 or col == 0 or col == BOARD_SIZE-1:
                edge_value = 2
            score += edge_value

        if piece_type == PION:
            if self.color == WHITE:
                promotion_distance = row
            else:
                promotion_distance = BOARD_SIZE - 1 - row

            promotion_value = (BOARD_SIZE - promotion_distance) * 0.3

            if game_phase == "end_game":
                promotion_value *= 1.5

            score += promotion_value

        return score

    def _evaluate_from_history(self, game_controller, from_pos, to_pos, move_classification):
        try:
            moves_data = self.data_processor.load_game_moves()

            if moves_data.empty:
                return 0

            player_moves = moves_data[moves_data['player'] == self.color]

            score = 0

            for _, game_id in enumerate(player_moves['game_id'].unique()):
                game_moves = player_moves[player_moves['game_id'] == game_id]

                game_history = self.data_processor.load_game_history()
                if not game_history.empty:
                    game_result = game_history[game_history['game_id'] == game_id]

                    if not game_result.empty and game_result['winner'].iloc[0] == self.color:
                        win_bonus = 2.0
                    else:
                        win_bonus = 0.5

                    for _, move in game_moves.iterrows():
                        try:
                            if (int(move['from_row']), int(move['from_col'])) == from_pos and \
                               (int(move['to_row']), int(move['to_col'])) == to_pos:
                                score += 5 * win_bonus

                            if 'classification' in move and move['classification'] == move_classification:
                                score += 2 * win_bonus
                        except (ValueError, TypeError):
                            continue

            if not player_moves.empty and 'classification' in player_moves.columns:
                history = self.data_processor.load_game_history()
                if not history.empty:
                    winning_games = history[history['winner'] == self.color]['game_id'].tolist()
                    winning_moves = player_moves[player_moves['game_id'].isin(winning_games)]

                    if not winning_moves.empty and 'classification' in winning_moves.columns:
                        class_counts = winning_moves['classification'].value_counts()
                        if move_classification in class_counts:
                            frequency_bonus = min(3.0, class_counts[move_classification] / len(winning_games))
                            score += frequency_bonus

            return score

        except Exception as e:
            return 0