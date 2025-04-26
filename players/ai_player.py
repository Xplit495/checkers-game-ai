import random
import numpy as np
import pandas as pd
from game.constants import *
from data_management.data_processor import DataProcessor
from players.player import Player

class AIPlayer(Player):
    """
    Joueur IA pour le jeu de dames qui évalue et sélectionne les coups
    en fonction de règles stratégiques et de l'analyse des parties précédentes.
    """

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
                "history": 0.6,  # Augmenté pour accorder plus d'importance à l'historique
                "captures": 0.6,
                "king": 0.5,
                "classification": 0.5,
                "recorded_score": 0.6  # Nouveau poids pour les scores enregistrés
            },
            "hard": {
                "material": 1.0,
                "position": 0.8,
                "history": 0.9,  # Augmenté pour accorder plus d'importance à l'historique
                "captures": 0.9,
                "king": 0.7,
                "classification": 0.8,
                "recorded_score": 0.9  # Nouveau poids pour les scores enregistrés
            }
        }

        # Poids spécifiques pour les classifications de coups
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

        # Poids pour les contributions au résultat
        self.outcome_weights = {
            "positive": 1.5,   # Bonus pour les coups qui ont mené à une victoire
            "negative": 0.3,   # Malus pour les coups qui ont mené à une défaite
            "neutral": 0.8,    # Léger malus pour les coups des matchs nuls
            "pending": 0.7     # Valeur par défaut pour les coups sans résultat
        }

    def select_move(self, game_controller):
        """
        Sélectionne le meilleur coup à jouer selon l'évaluation.

        Args:
            game_controller (GameController): Contrôleur du jeu actuel

        Returns:
            tuple: Position de départ (from_row, from_col) et position d'arrivée (to_row, to_col)
        """
        # 1. Créer un dictionnaire des coups possibles
        possible_moves = self._get_possible_moves(game_controller)

        if not possible_moves:
            return None  # Aucun coup possible

        # 2. Évaluer chaque coup possible
        evaluated_moves = self._evaluate_moves(game_controller, possible_moves)

        # Ajouter un peu de hasard selon la difficulté
        if self.difficulty == "easy":
            random_factor = 0.3
        elif self.difficulty == "normal":
            random_factor = 0.1
        else:
            random_factor = 0.02

        for move in evaluated_moves:
            evaluated_moves[move] += random.uniform(0, random_factor * 10)

        # Afficher les scores pour le débogage
        print(f"AI considering {len(evaluated_moves)} possible moves:")
        for move, score in sorted(evaluated_moves.items(), key=lambda x: x[1], reverse=True)[:3]:
            (from_pos, to_pos) = move
            print(f"  From {from_pos} to {to_pos}: Score {score:.2f}")

        # 5. Sélectionner le coup avec le meilleur score
        best_move = max(evaluated_moves.items(), key=lambda x: x[1])
        from_pos, to_pos = best_move[0]

        print(f"AI selected move from {from_pos} to {to_pos} with score {best_move[1]:.2f}")

        return from_pos, to_pos

    def _get_possible_moves(self, game_controller):
        """
        Crée un dictionnaire des coups possibles.

        Args:
            game_controller (GameController): Contrôleur du jeu

        Returns:
            dict: Dictionnaire avec les coups possibles comme clés et 0 comme valeur initiale
        """
        possible_moves = {}

        # Vérifier d'abord s'il y a des captures disponibles
        captures_available = game_controller.check_captures_available()

        # Parcourir le plateau pour trouver les pièces du joueur
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = game_controller.board.get_piece(row, col)

                if piece and piece.color == self.color:
                    # Si des captures sont disponibles, on ne peut sélectionner que les pièces
                    # qui peuvent capturer
                    if captures_available and not game_controller.can_piece_capture(row, col):
                        continue

                    # Obtenir les mouvements valides pour cette pièce
                    valid_moves = game_controller.board.get_valid_moves(row, col, self.color)

                    # Ajouter chaque mouvement au dictionnaire
                    for to_pos, captures in valid_moves.items():
                        from_pos = (row, col)
                        possible_moves[(from_pos, to_pos)] = 0

        return possible_moves

    def _evaluate_moves(self, game_controller, possible_moves):
        """
        Évalue chaque coup possible selon plusieurs critères.

        Args:
            game_controller (GameController): Contrôleur du jeu
            possible_moves (dict): Dictionnaire des coups possibles

        Returns:
            dict: Dictionnaire des coups avec leur score d'évaluation
        """
        evaluated_moves = possible_moves.copy()

        # Obtenir la phase actuelle du jeu
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

            # Créer une copie du contrôleur de jeu pour simuler le coup
            from game.game_controller import GameController
            test_controller = GameController(create_recorder=False)  # Ne pas créer d'enregistreur pour les simulations
            test_controller.board = game_controller.board.copy()
            test_controller.current_player = self.color
            test_controller.piece_count = game_controller.piece_count.copy()

            # Simuler la sélection et le déplacement
            piece = test_controller.board.get_piece(from_row, from_col)
            test_controller.selected_piece = from_pos
            test_controller.valid_moves = test_controller.board.get_valid_moves(from_row, from_col, self.color)

            # Vérifier s'il y a des captures et si c'est une promotion potentielle
            captures = game_controller.board.get_valid_moves(from_row, from_col, self.color).get(to_pos, [])
            could_promote = False
            if piece and piece.type == PION:
                if (self.color == WHITE and to_row == 0) or (self.color == BLACK and to_row == BOARD_SIZE-1):
                    could_promote = True

            # Déterminer la classification du coup
            move_classification = self._determine_move_classification(
                from_pos, to_pos, piece.type if piece else PION,
                captures, could_promote, game_phase
            )

            # Appliquer le mouvement sur le plateau de test
            test_controller.move(to_row, to_col)

            # 3. Évaluer selon des critères stratégiques
            score = 0

            # 3.1 Matériel (nombre de pièces)
            material_score = self._evaluate_material(test_controller)
            score += material_score * self.weights[self.difficulty]["material"]

            # 3.2 Position sur le plateau
            position_score = self._evaluate_position(to_row, to_col, piece.type if piece else PION, game_phase)
            score += position_score * self.weights[self.difficulty]["position"]

            # 3.3 Captures
            capture_score = len(captures) * 10
            if len(captures) > 1:
                capture_score *= 1.5  # Bonus pour les captures multiples
            score += capture_score * self.weights[self.difficulty]["captures"]

            # 3.4 Promotion
            promotion_score = 0
            if could_promote:
                promotion_score = 15
            score += promotion_score * self.weights[self.difficulty]["king"]

            # 3.5 Classification du coup (basée sur l'historique et la stratégie)
            classification_score = self.classification_weights.get(move_classification, 0.5) * 10
            score += classification_score * self.weights[self.difficulty]["classification"]

            # 4. Évaluer selon l'historique des parties (incluant les scores enregistrés)
            history_data = self._evaluate_from_history(game_controller, from_pos, to_pos, move_classification)
            history_score = history_data["history_score"]
            recorded_score = history_data["recorded_score"]

            score += history_score * self.weights[self.difficulty]["history"]
            score += recorded_score * self.weights[self.difficulty]["recorded_score"]

            evaluated_moves[move] = score

        return evaluated_moves

    def _determine_move_classification(self, from_pos, to_pos, piece_type, captures, promotion, game_phase):
        """
        Détermine la classification d'un coup pour l'évaluation.

        Args:
            from_pos (tuple): Position de départ
            to_pos (tuple): Position d'arrivée
            piece_type (str): Type de pièce
            captures (list): Liste des captures
            promotion (bool): Si le coup mène à une promotion
            game_phase (str): Phase actuelle du jeu

        Returns:
            str: Classification du coup
        """
        # Classification de base selon la phase de jeu
        classification = game_phase

        # Raffiner selon le type d'action
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

        # Classification selon le type de pièce
        if piece_type == DAME:
            if "capture" in classification:
                classification = "king_capture"

        return classification

    def _evaluate_material(self, game_controller):
        """
        Évalue l'avantage matériel après un coup.

        Args:
            game_controller (GameController): État du jeu après le coup

        Returns:
            float: Score basé sur l'avantage matériel
        """
        opponent_color = BLACK if self.color == WHITE else WHITE

        my_pieces = game_controller.piece_count[self.color]
        opponent_pieces = game_controller.piece_count[opponent_color]

        # Compter les dames (qui valent plus que les pions)
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

        # Une dame vaut environ 1.5 fois un pion
        my_value = my_pieces + (my_kings * 0.5)
        opponent_value = opponent_pieces + (opponent_kings * 0.5)

        return my_value - opponent_value

    def _evaluate_position(self, row, col, piece_type, game_phase):
        """
        Évalue l'avantage positionnel d'un coup.

        Args:
            row, col (int): Position après le coup
            piece_type (str): Type de pièce (PION/DAME)
            game_phase (str): Phase du jeu

        Returns:
            float: Score basé sur la position
        """
        score = 0

        # Valeur du centre (différente selon la phase de jeu)
        center_value = 4 - (abs(row - BOARD_SIZE//2) + abs(col - BOARD_SIZE//2)) / 2

        if game_phase == "opening":
            # En ouverture, contrôler le centre est important
            score += center_value * 0.8
        elif game_phase == "middle_game":
            # En milieu de partie, le centre est toujours important mais moins
            score += center_value * 0.5
        else:  # end_game
            # En fin de partie, le centre est moins important
            score += center_value * 0.3

        # Avantage des bords pour les dames
        if piece_type == DAME:
            edge_value = 0
            if row == 0 or row == BOARD_SIZE-1 or col == 0 or col == BOARD_SIZE-1:
                edge_value = 2
            score += edge_value

        # Avancer vers la promotion pour les pions
        if piece_type == PION:
            if self.color == WHITE:
                promotion_distance = row  # Distance par rapport à la ligne 0
            else:
                promotion_distance = BOARD_SIZE - 1 - row  # Distance par rapport à la ligne 9

            # Plus on est proche de la promotion, meilleur c'est
            promotion_value = (BOARD_SIZE - promotion_distance) * 0.3

            # En fin de partie, les promotions sont plus importantes
            if game_phase == "end_game":
                promotion_value *= 1.5

            score += promotion_value

        return score

    def _evaluate_from_history(self, game_controller, from_pos, to_pos, move_classification):
        """
        Évalue un coup en fonction de l'historique des parties et de sa classification.

        Args:
            game_controller (GameController): État actuel du jeu
            from_pos, to_pos (tuple): Positions de départ et d'arrivée
            move_classification (str): Classification du coup

        Returns:
            dict: Scores basés sur l'historique et les scores enregistrés
        """
        result = {
            "history_score": 0,
            "recorded_score": 0
        }

        try:
            # Charger l'historique des parties
            moves_data = self.data_processor.load_game_moves()

            if moves_data.empty:
                return result  # Pas d'historique disponible

            # Filtrer les mouvements pour le joueur actuel
            player_moves = moves_data[moves_data['player'] == self.color]

            if player_moves.empty:
                return result  # Pas de mouvements pour ce joueur

            # 1. Rechercher des coups identiques ou similaires
            similar_moves = player_moves[
                (player_moves['from_row'].astype(int) == from_pos[0]) &
                (player_moves['from_col'].astype(int) == from_pos[1]) &
                (player_moves['to_row'].astype(int) == to_pos[0]) &
                (player_moves['to_col'].astype(int) == to_pos[1])
            ]

            # Vérifier si nous avons trouvé des mouvements similaires
            if not similar_moves.empty:
                # 2. Examiner les scores enregistrés pour ces coups
                if 'move_score' in similar_moves.columns:
                    avg_score = similar_moves['move_score'].astype(float).mean()
                    result["recorded_score"] = avg_score

                # 3. Examiner les contributions au résultat
                if 'outcome_contribution' in similar_moves.columns:
                    # Compter les différentes contributions
                    contributions = similar_moves['outcome_contribution'].value_counts()

                    # Calculer un score basé sur les contributions
                    contribution_score = 0
                    total_contributions = 0

                    for contrib, count in contributions.items():
                        if contrib in self.outcome_weights:
                            contribution_score += self.outcome_weights[contrib] * count
                            total_contributions += count

                    if total_contributions > 0:
                        contribution_score = contribution_score / total_contributions
                        result["history_score"] += contribution_score * 5  # Bonus pour les contributions positives

            # 4. Rechercher des coups de même classification
            classification_moves = player_moves[player_moves['classification'] == move_classification]

            if not classification_moves.empty:
                # Calculer un score basé sur l'efficacité historique de cette classification
                if 'outcome_contribution' in classification_moves.columns:
                    positive_count = classification_moves[classification_moves['outcome_contribution'] == 'positive'].shape[0]
                    total_count = classification_moves.shape[0]

                    if total_count > 0:
                        success_rate = positive_count / total_count
                        result["history_score"] += success_rate * 3  # Bonus basé sur le taux de succès

            # 5. Bonus global pour les coups fréquemment joués (suggère que c'est une bonne stratégie)
            if not similar_moves.empty:
                frequency_bonus = min(3.0, len(similar_moves))
                result["history_score"] += frequency_bonus

            # Si nous avons un score enregistré, assurons-nous qu'il a un impact significatif
            if result["recorded_score"] > 0:
                result["recorded_score"] = min(20, result["recorded_score"]) # Plafonner pour éviter des valeurs extrêmes

            return result

        except Exception as e:
            print(f"Erreur dans l'évaluation historique: {e}")
            # En cas d'erreur, renvoyer les scores par défaut
            return result