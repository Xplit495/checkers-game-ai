import random

from data_management.data_processor import DataProcessor
from game.constants import *
from players.player import Player


def _determine_move_classification(piece_type, captures, promotion, game_phase):
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


class AIPlayer(Player):
    def __init__(self, color, difficulty="normal"):
        super().__init__(color)
        self.difficulty = difficulty
        self.data_processor = DataProcessor()

        self.weights = {
            "easy": {
                "material": 0.5,
                "position": 0.3,
                "history": 0.3,
                "captures": 0.3,
                "king": 0.2,
                "classification": 0.2,
                "recorded_score": 0.3
            },
            "normal": {
                "material": 0.7,
                "position": 0.6,
                "history": 0.6,
                "captures": 0.6,
                "king": 0.5,
                "classification": 0.5,
                "recorded_score": 0.6
            },
            "hard": {
                "material": 1.0,
                "position": 0.8,
                "history": 0.9,
                "captures": 0.9,
                "king": 0.7,
                "classification": 0.8,
                "recorded_score": 0.9
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


        self.outcome_weights = {
            "positive": 1.5,
            "negative": 0.3,
            "neutral": 0.8,
            "pending": 0.7
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

        print(f"AI considering {len(evaluated_moves)} possible moves:")
        for move, score in sorted(evaluated_moves.items(), key=lambda x: x[1], reverse=True)[:3]:
            (from_pos, to_pos) = move
            print(f"  From {from_pos} to {to_pos}: Score {score:.2f}")

        best_move = max(evaluated_moves.items(), key=lambda x: x[1])
        from_pos, to_pos = best_move[0]

        print(f"AI selected move from {from_pos} to {to_pos} with score {best_move[1]:.2f}")

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

            move_classification = _determine_move_classification(
                piece.type if piece else PION,
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

            history_data = self._evaluate_from_history(from_pos, to_pos, move_classification)
            history_score = history_data["history_score"]
            recorded_score = history_data["recorded_score"]

            score += history_score * self.weights[self.difficulty]["history"]
            score += recorded_score * self.weights[self.difficulty]["recorded_score"]

            evaluated_moves[move] = score

        return evaluated_moves

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

    def _evaluate_from_history(self, from_pos, to_pos, move_classification):
        result = {
            "history_score": 0,
            "recorded_score": 0
        }

        try:
            moves_data = self.data_processor.load_game_moves()

            if moves_data.empty:
                return result

            player_moves = moves_data[moves_data['player'] == self.color]

            if player_moves.empty:
                return result

            similar_moves = player_moves[
                (player_moves['from_row'].astype(int) == from_pos[0]) &
                (player_moves['from_col'].astype(int) == from_pos[1]) &
                (player_moves['to_row'].astype(int) == to_pos[0]) &
                (player_moves['to_col'].astype(int) == to_pos[1])
            ]

            if not similar_moves.empty:
                if 'move_score' in similar_moves.columns:
                    avg_score = similar_moves['move_score'].astype(float).mean()
                    result["recorded_score"] = avg_score

                if 'outcome_contribution' in similar_moves.columns:
                    contributions = similar_moves['outcome_contribution'].value_counts()

                    contribution_score = 0
                    total_contributions = 0

                    for contrib, count in contributions.items():
                        if contrib in self.outcome_weights:
                            contribution_score += self.outcome_weights[contrib] * count
                            total_contributions += count

                    if total_contributions > 0:
                        contribution_score = contribution_score / total_contributions
                        result["history_score"] += contribution_score * 5

            classification_moves = player_moves[player_moves['classification'] == move_classification]

            if not classification_moves.empty:
                if 'outcome_contribution' in classification_moves.columns:
                    positive_count = classification_moves[classification_moves['outcome_contribution'] == 'positive'].shape[0]
                    total_count = classification_moves.shape[0]

                    if total_count > 0:
                        success_rate = positive_count / total_count
                        result["history_score"] += success_rate * 3

            if not similar_moves.empty:
                frequency_bonus = min(3.0, len(similar_moves))
                result["history_score"] += frequency_bonus

            if result["recorded_score"] > 0:
                result["recorded_score"] = min(20, result["recorded_score"])

            return result

        except Exception as e:
            print(f"Erreur dans l'évaluation historique: {e}")
            return result