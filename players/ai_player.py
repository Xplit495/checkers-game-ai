"""
Module de l'Intelligence Artificielle du jeu de dames

Ce module implémente une IA capable de jouer au jeu de dames en utilisant
une combinaison d'évaluation statique et d'analyse des données historiques.
L'IA apprend des parties précédentes pour améliorer sa stratégie au fil du temps.
"""

import random
import pandas as pd

from data_management.data_processor import DataProcessor
from game.constants import *
from players.player import Player


def _determine_move_classification(piece_type, captures, promotion, game_phase):
    """
    Détermine la classification d'un mouvement en fonction de ses caractéristiques.

    Cette classification est importante pour l'IA car elle permet de comparer
    des mouvements similaires dans les données historiques et de leur attribuer
    des poids différents selon leur nature.

    Args:
        piece_type (str): Le type de pièce (PION ou DAME)
        captures (list): Liste des pièces capturées par ce mouvement
        promotion (bool): Indique si le mouvement a entraîné une promotion
        game_phase (str): Phase de jeu actuelle (opening, middle_game, end_game)

    Returns:
        str: La classification du mouvement
    """
    classification = game_phase

    # Si le mouvement inclut une ou plusieurs captures
    if captures:
        if len(captures) > 1:
            classification = "multiple_capture"  # Capture multiple (plus de 1 pièce)
        else:
            classification = "capture"  # Capture simple (1 pièce)

    # Si le mouvement inclut une promotion
    if promotion:
        if captures:
            classification = "capture_promotion"  # Capture + promotion (combo puissant)
        else:
            classification = "promotion"  # Promotion simple

    # Si le mouvement est effectué par une dame et inclut une capture
    if piece_type == DAME:
        if "capture" in classification:
            classification = "king_capture"  # Capture par une dame

    return classification


class AIPlayer(Player):
    """
    Intelligence artificielle pour le jeu de dames.

    Cette classe implémente un joueur IA qui utilise une combinaison d'évaluation
    statique du plateau et d'analyse des données historiques pour choisir ses mouvements.
    L'IA apprend des parties précédentes et privilégie les mouvements qui ont
    historiquement conduit à des victoires.
    """

    def __init__(self, color):
        """
        Initialise un joueur IA.

        Args:
            color (str): Couleur des pièces de l'IA (WHITE ou BLACK)
        """
        super().__init__(color)
        # DataProcessor permet d'accéder aux données des parties précédentes
        self.data_processor = DataProcessor()

        # Poids pour différents aspects de l'évaluation des mouvements
        # Ces valeurs ont été optimisées pour favoriser les données historiques
        self.weights = {
            "material": 0.7,     # Avantage matériel (nombre de pièces)
            "position": 0.6,     # Position stratégique sur le plateau
            "history": 1.5,      # Données historiques des parties précédentes
            "captures": 0.9,     # Captures possibles
            "king": 0.7,         # Promotions en dame
            "classification": 0.8, # Type de mouvement
            "recorded_score": 1.8  # Score enregistré dans les données historiques
        }

        # Poids pour les différents types de mouvements
        # Ces valeurs définissent l'importance relative de chaque type de mouvement
        self.classification_weights = {
            "opening": 0.6,           # Phase d'ouverture
            "middle_game": 0.5,        # Phase de milieu de partie
            "end_game": 0.7,           # Phase de fin de partie
            "capture": 0.8,            # Capture simple
            "multiple_capture": 1.0,   # Capture multiple (très valorisée)
            "promotion": 0.7,          # Promotion
            "capture_promotion": 0.9,  # Capture + promotion
            "king_capture": 0.85       # Capture par une dame
        }

        # Poids pour les contributions aux résultats des parties précédentes
        # Ces valeurs définissent l'importance de l'historique des résultats
        self.outcome_weights = {
            "positive": 1.5,   # Mouvement ayant contribué à une victoire
            "negative": 0.3,   # Mouvement ayant contribué à une défaite
            "neutral": 0.8,    # Mouvement neutre (partie nulle)
            "pending": 0.7     # Résultat pas encore déterminé
        }

    def select_move(self, game_controller):
        """
        Sélectionne le meilleur mouvement à jouer selon l'IA.

        Cette méthode est le point d'entrée principal pour l'IA.
        Elle récupère tous les mouvements possibles, les évalue,
        et sélectionne celui avec le meilleur score.

        Args:
            game_controller: Le contrôleur de jeu contenant l'état actuel

        Returns:
            tuple: Un tuple (from_pos, to_pos) représentant le mouvement choisi,
                  ou None si aucun mouvement n'est possible
        """
        # Obtenir tous les mouvements possibles
        possible_moves = self._get_possible_moves(game_controller)

        if not possible_moves:
            return None  # Aucun mouvement possible

        # Évaluer chaque mouvement possible
        evaluated_moves = self._evaluate_moves(game_controller, possible_moves)

        # Ajouter un facteur aléatoire minimal pour éviter la prévisibilité
        random_factor = 0.02
        for move in evaluated_moves:
            evaluated_moves[move] += random.uniform(0, random_factor * 10)

        # Afficher les 3 meilleurs mouvements (pour le débogage)
        print(f"AI considering {len(evaluated_moves)} possible moves:")
        for move, score in sorted(evaluated_moves.items(), key=lambda x: x[1], reverse=True)[:3]:
            (from_pos, to_pos) = move
            print(f"  From {from_pos} to {to_pos}: Score {score:.2f}")

        # Sélectionner le mouvement avec le meilleur score
        best_move = max(evaluated_moves.items(), key=lambda x: x[1])
        from_pos, to_pos = best_move[0]

        print(f"AI selected move from {from_pos} to {to_pos} with score {best_move[1]:.2f}")

        return from_pos, to_pos

    def _get_possible_moves(self, game_controller):
        """
        Récupère tous les mouvements possibles pour l'IA dans l'état actuel du jeu.

        Cette méthode parcourt le plateau et identifie tous les mouvements
        légaux pour les pièces de l'IA. Si des captures sont possibles,
        seuls les mouvements de capture sont considérés (règle du jeu de dames).

        Args:
            game_controller: Le contrôleur de jeu contenant l'état actuel

        Returns:
            dict: Un dictionnaire des mouvements possibles avec des scores initiaux à 0
        """
        possible_moves = {}

        # Vérifier si des captures sont possibles
        captures_available = game_controller.check_captures_available()

        # Parcourir toutes les cases du plateau
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = game_controller.board.get_piece(row, col)

                # Si une pièce de l'IA est présente
                if piece and piece.color == self.color:
                    # Si des captures sont possibles, ignorer les pièces qui ne peuvent pas capturer
                    if captures_available and not game_controller.can_piece_capture(row, col):
                        continue

                    # Obtenir les mouvements valides pour cette pièce
                    valid_moves = game_controller.board.get_valid_moves(row, col, self.color)

                    # Ajouter chaque mouvement valide à la liste des mouvements possibles
                    for to_pos, captures in valid_moves.items():
                        from_pos = (row, col)
                        possible_moves[(from_pos, to_pos)] = 0

        return possible_moves

    def _evaluate_moves(self, game_controller, possible_moves):
        """
        Évalue chaque mouvement possible et lui attribue un score.

        Cette méthode est le cœur de l'intelligence de l'IA. Elle utilise
        plusieurs critères pour évaluer chaque mouvement :
        1. L'analyse des données historiques des parties précédentes
        2. L'avantage matériel résultant du mouvement
        3. La position stratégique sur le plateau
        4. Les captures possibles
        5. Les promotions possibles

        Args:
            game_controller: Le contrôleur de jeu contenant l'état actuel
            possible_moves: Dictionnaire des mouvements possibles à évaluer

        Returns:
            dict: Le même dictionnaire avec des scores actualisés
        """
        evaluated_moves = possible_moves.copy()

        # Déterminer la phase de jeu actuelle
        total_pieces = game_controller.piece_count[WHITE] + game_controller.piece_count[BLACK]
        move_count = game_controller.game_recorder.move_count if hasattr(game_controller, 'game_recorder') and game_controller.game_recorder else 0

        if move_count < 8:
            game_phase = "opening"       # Phase d'ouverture (8 premiers coups)
        elif total_pieces < 15:
            game_phase = "end_game"      # Phase de fin (moins de 15 pièces)
        else:
            game_phase = "middle_game"   # Phase de milieu de partie

        # Analyser les données historiques pour identifier des patterns avantageux
        historical_advantages = self._analyze_historical_patterns(game_controller)

        # Évaluer chaque mouvement possible
        for move, _ in evaluated_moves.items():
            (from_pos, to_pos) = move
            from_row, from_col = from_pos
            to_row, to_col = to_pos

            # Créer un contrôleur de jeu temporaire pour simuler le mouvement
            from game.game_controller import GameController
            test_controller = GameController(create_recorder=False)
            test_controller.board = game_controller.board.copy()
            test_controller.current_player = self.color
            test_controller.piece_count = game_controller.piece_count.copy()

            # Obtenir la pièce à déplacer
            piece = test_controller.board.get_piece(from_row, from_col)
            test_controller.selected_piece = from_pos
            test_controller.valid_moves = test_controller.board.get_valid_moves(from_row, from_col, self.color)

            # Déterminer si le mouvement inclut des captures ou une promotion
            captures = game_controller.board.get_valid_moves(from_row, from_col, self.color).get(to_pos, [])
            could_promote = False
            if piece and piece.type == PION:
                if (self.color == WHITE and to_row == 0) or (self.color == BLACK and to_row == BOARD_SIZE-1):
                    could_promote = True

            # Classifier le type de mouvement
            move_classification = _determine_move_classification(
                piece.type if piece else PION,
                captures, could_promote, game_phase
            )

            # Simuler le mouvement
            test_controller.move(to_row, to_col)

            # Initialiser le score du mouvement
            score = 0

            # 1. Évaluer les données historiques (facteur majeur dans la décision)
            history_data = self._evaluate_from_history(from_pos, to_pos, move_classification)
            history_score = history_data["history_score"]
            recorded_score = history_data["recorded_score"]

            # Appliquer un bonus pour les mouvements historiquement avantageux
            key = (from_row, from_col, to_row, to_col)
            if key in historical_advantages:
                history_score += historical_advantages[key] * 3.0  # Bonus significatif

            # 2. Autres facteurs d'évaluation (moins importants mais toujours considérés)
            material_score = self._evaluate_material(test_controller)
            position_score = self._evaluate_position(to_row, to_col, piece.type if piece else PION, game_phase)

            # Score pour les captures
            capture_score = len(captures) * 10
            if len(captures) > 1:
                capture_score *= 1.5  # Bonus pour les captures multiples

            # Score pour les promotions
            promotion_score = 0
            if could_promote:
                promotion_score = 15

            # Score pour le type de mouvement
            classification_score = self.classification_weights.get(move_classification, 0.5) * 10

            # Somme pondérée de tous les scores
            score += history_score * self.weights["history"]
            score += recorded_score * self.weights["recorded_score"]
            score += material_score * self.weights["material"]
            score += position_score * self.weights["position"]
            score += capture_score * self.weights["captures"]
            score += promotion_score * self.weights["king"]
            score += classification_score * self.weights["classification"]

            # Attribuer le score final au mouvement
            evaluated_moves[move] = score

        return evaluated_moves

    def _analyze_historical_patterns(self, game_controller):
        """
        Analyse les données des parties précédentes pour identifier des patterns stratégiques.

        Cette méthode est cruciale pour l'apprentissage de l'IA. Elle analyse
        les parties précédentes pour identifier les mouvements qui ont souvent
        conduit à des victoires, et recherche des positions de plateau similaires
        à la position actuelle pour s'inspirer des coups qui ont fonctionné.

        Args:
            game_controller: Le contrôleur de jeu contenant l'état actuel

        Returns:
            dict: Un dictionnaire des avantages historiques pour chaque mouvement
        """
        advantages = {}

        try:
            # Charger toutes les données des mouvements des parties précédentes
            moves_data = self.data_processor.load_game_moves()
            if moves_data.empty:
                return advantages

            # Identifier les mouvements qui ont souvent conduit à des victoires
            positive_moves = moves_data[moves_data['outcome_contribution'] == 'positive']

            if not positive_moves.empty:
                # Compter les occurrences de chaque mouvement positif
                move_counts = positive_moves.groupby(['from_row', 'from_col', 'to_row', 'to_col']).size().reset_index(name='count')

                # Normaliser les scores pour obtenir une valeur entre 0 et 10
                total_count = move_counts['count'].sum()
                if total_count > 0:
                    for _, row in move_counts.iterrows():
                        key = (int(row['from_row']), int(row['from_col']), int(row['to_row']), int(row['to_col']))
                        advantages[key] = row['count'] / total_count * 10

            # Identifier les positions de plateau similaires et les bons mouvements associés
            current_board_state = self._get_board_state_key(game_controller.board)

            # Simuler la reconstruction des états de plateau pour les parties précédentes
            game_ids = moves_data['game_id'].unique()
            # Limiter à 10 parties pour l'efficacité
            for game_id in game_ids[:min(10, len(game_ids))]:
                game_moves = moves_data[moves_data['game_id'] == game_id].sort_values('move_number')

                # Simuler chaque partie pour trouver des états de plateau similaires
                from game.board import Board
                sim_board = Board()

                for idx, move in game_moves.iterrows():
                    board_state_before = self._get_board_state_key(sim_board)

                    # Si l'état du plateau est similaire à l'état actuel (similarité > 70%)
                    if self._states_similarity(board_state_before, current_board_state) > 0.7:
                        key = (int(move['from_row']), int(move['from_col']),
                               int(move['to_row']), int(move['to_col']))

                        # Ajouter un avantage si ce coup a contribué à une victoire
                        if move['outcome_contribution'] == 'positive':
                            advantages[key] = advantages.get(key, 0) + 5.0

                    # Mettre à jour la simulation en appliquant le mouvement
                    try:
                        from_row, from_col = int(move['from_row']), int(move['from_col'])
                        to_row, to_col = int(move['to_row']), int(move['to_col'])

                        # Simuler les captures
                        if not pd.isna(move['captures']) and move['captures']:
                            for capture in str(move['captures']).split(';'):
                                if capture:
                                    capt_row, capt_col = map(int, capture.split(','))
                                    sim_board.remove_piece(capt_row, capt_col)

                        # Déplacer la pièce
                        sim_board.move_piece(from_row, from_col, to_row, to_col)

                        # Simuler la promotion
                        if not pd.isna(move['promotion']) and str(move['promotion']).lower() == 'true':
                            piece = sim_board.get_piece(to_row, to_col)
                            if piece:
                                piece.type = DAME
                    except Exception:
                        # En cas d'erreur de simulation, continuer avec le prochain mouvement
                        continue

        except Exception as e:
            print(f"Erreur lors de l'analyse des modèles historiques: {e}")

        return advantages

    def _get_board_state_key(self, board):
        """
        Crée une représentation de l'état du plateau pour faciliter les comparaisons.

        Cette représentation est utilisée pour comparer rapidement différents
        états de plateau et identifier des situations similaires dans les parties précédentes.

        Args:
            board: L'objet plateau à représenter

        Returns:
            list: Une liste de tuples (row, col, val) représentant l'état du plateau
        """
        state = []
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = board.get_piece(row, col)
                if piece:
                    # Valeur positive pour les pièces blanches, négative pour les noires
                    # Valeur doublée pour les dames
                    val = 1 if piece.color == WHITE else -1
                    if piece.type == DAME:
                        val *= 2
                    state.append((row, col, val))
        return state

    def _states_similarity(self, state1, state2):
        """
        Calcule le degré de similarité entre deux états de plateau.

        Cette méthode utilise le coefficient de Jaccard pour mesurer
        la similarité entre deux plateaux (intersection/union des pièces).

        Args:
            state1: Premier état du plateau
            state2: Deuxième état du plateau

        Returns:
            float: Valeur entre 0 et 1 indiquant le degré de similarité
        """
        if not state1 or not state2:
            return 0

        # Convertir en ensembles de positions pour une comparaison efficace
        set1 = set((r, c) for r, c, _ in state1)
        set2 = set((r, c) for r, c, _ in state2)

        # Calculer le coefficient de Jaccard (intersection / union)
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        return intersection / union if union > 0 else 0

    def _evaluate_material(self, game_controller):
        """
        Évalue l'avantage matériel après un mouvement.

        Cette méthode calcule la différence entre le nombre de pièces de l'IA
        et de l'adversaire, en accordant un bonus aux dames.

        Args:
            game_controller: Le contrôleur de jeu contenant l'état après simulation

        Returns:
            float: Score d'avantage matériel
        """
        opponent_color = BLACK if self.color == WHITE else WHITE

        # Compter le nombre de pièces
        my_pieces = game_controller.piece_count[self.color]
        opponent_pieces = game_controller.piece_count[opponent_color]

        # Compter le nombre de dames
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

        # Calculer l'avantage matériel (une dame vaut 1.5 pions)
        my_value = my_pieces + (my_kings * 0.5)
        opponent_value = opponent_pieces + (opponent_kings * 0.5)

        return my_value - opponent_value

    def _evaluate_position(self, row, col, piece_type, game_phase):
        """
        Évalue la qualité stratégique d'une position sur le plateau.

        Différents critères sont utilisés selon la phase de jeu et le type de pièce :
        - La proximité du centre est valorisée, surtout en début de partie
        - Pour les dames, les bords du plateau sont valorisés
        - Pour les pions, la proximité de la promotion est valorisée

        Args:
            row: Ligne de la position à évaluer
            col: Colonne de la position à évaluer
            piece_type: Type de pièce (PION ou DAME)
            game_phase: Phase de jeu actuelle

        Returns:
            float: Score de position
        """
        score = 0

        # Évaluer la proximité du centre (valorisée en début de partie)
        center_value = 4 - (abs(row - BOARD_SIZE//2) + abs(col - BOARD_SIZE//2)) / 2

        # Ajuster l'importance selon la phase de jeu
        if game_phase == "opening":
            score += center_value * 0.8  # Très important en ouverture
        elif game_phase == "middle_game":
            score += center_value * 0.5  # Moyennement important en milieu de partie
        else:
            score += center_value * 0.3  # Moins important en fin de partie

        # Pour les dames, valoriser les bords du plateau (sécurité et mobilité)
        if piece_type == DAME:
            edge_value = 0
            if row == 0 or row == BOARD_SIZE-1 or col == 0 or col == BOARD_SIZE-1:
                edge_value = 2
            score += edge_value

        # Pour les pions, valoriser la proximité de la promotion
        if piece_type == PION:
            if self.color == WHITE:
                promotion_distance = row  # Distance à la ligne 0
            else:
                promotion_distance = BOARD_SIZE - 1 - row  # Distance à la ligne 9

            promotion_value = (BOARD_SIZE - promotion_distance) * 0.3

            # La proximité de promotion est plus importante en fin de partie
            if game_phase == "end_game":
                promotion_value *= 1.5

            score += promotion_value

        return score

    def _evaluate_from_history(self, from_pos, to_pos, move_classification):
        """
        Évalue un mouvement en se basant sur les données historiques.

        Cette méthode examine les parties précédentes pour trouver des mouvements
        similaires et déterminer leur efficacité historique. C'est un élément
        crucial pour l'apprentissage de l'IA.

        Args:
            from_pos: Position de départ
            to_pos: Position d'arrivée
            move_classification: Type de mouvement

        Returns:
            dict: Scores basés sur l'historique
        """
        result = {
            "history_score": 0,
            "recorded_score": 0
        }

        try:
            # Charger toutes les données des mouvements des parties précédentes
            moves_data = self.data_processor.load_game_moves()

            if moves_data.empty:
                return result

            # Filtrer pour ne garder que les mouvements de la même couleur
            player_moves = moves_data[moves_data['player'] == self.color]

            if player_moves.empty:
                return result

            # Trouver des mouvements identiques dans l'historique
            similar_moves = player_moves[
                (player_moves['from_row'].astype(int) == from_pos[0]) &
                (player_moves['from_col'].astype(int) == from_pos[1]) &
                (player_moves['to_row'].astype(int) == to_pos[0]) &
                (player_moves['to_col'].astype(int) == to_pos[1])
            ]

            if not similar_moves.empty:
                # Utiliser le score moyen enregistré pour ces mouvements
                if 'move_score' in similar_moves.columns:
                    avg_score = similar_moves['move_score'].astype(float).mean()
                    # Multiplié par 1.5 pour donner plus de poids aux scores enregistrés
                    result["recorded_score"] = avg_score * 1.5

                # Analyser les contributions aux résultats (victoire/défaite)
                if 'outcome_contribution' in similar_moves.columns:
                    contributions = similar_moves['outcome_contribution'].value_counts()

                    contribution_score = 0
                    total_contributions = 0

                    # Calculer un score basé sur les contributions passées
                    for contrib, count in contributions.items():
                        if contrib in self.outcome_weights:
                            contribution_score += self.outcome_weights[contrib] * count
                            total_contributions += count

                    if total_contributions > 0:
                        contribution_score = contribution_score / total_contributions
                        # Multiplié par 8 pour donner beaucoup d'importance
                        result["history_score"] += contribution_score * 8

            # Trouver des mouvements du même type (même classification)
            classification_moves = player_moves[player_moves['classification'] == move_classification]

            if not classification_moves.empty:
                # Analyser le taux de succès de ce type de mouvement
                if 'outcome_contribution' in classification_moves.columns:
                    positive_count = classification_moves[classification_moves['outcome_contribution'] == 'positive'].shape[0]
                    total_count = classification_moves.shape[0]

                    if total_count > 0:
                        success_rate = positive_count / total_count
                        # Multiplié par 5 pour valoriser les types de mouvements qui réussissent souvent
                        result["history_score"] += success_rate * 5

            # Bonus pour les mouvements fréquemment joués
            if not similar_moves.empty:
                frequency_bonus = min(5.0, len(similar_moves))
                result["history_score"] += frequency_bonus

            # Limiter le score enregistré à une valeur maximale
            if result["recorded_score"] > 0:
                result["recorded_score"] = min(25, result["recorded_score"])

            return result

        except Exception as e:
            print(f"Erreur dans l'évaluation historique: {e}")
            return result