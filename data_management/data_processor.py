"""
Module de traitement et d'analyse des données du jeu de dames

Ce module contient des fonctions et classes qui permettent de charger, traiter et analyser
les données des parties de dames enregistrées. Ces données sont essentielles pour l'IA
qui apprend des parties précédentes et pour générer des statistiques sur le jeu.
"""

import csv
import os

import numpy as np
import pandas as pd

from game.board import Board
from game.constants import *


def _extract_board_features(board):
    """
    Extrait des caractéristiques numériques d'un état de plateau pour l'IA.

    Cette fonction crée un vecteur de caractéristiques qui représente l'état
    actuel du plateau de jeu. Ces caractéristiques sont utilisées par l'IA
    pour reconnaître des situations similaires dans les parties précédentes.

    Args:
        board: L'objet Board représentant l'état du plateau

    Returns:
        list: Un vecteur de caractéristiques représentant l'état du plateau
    """
    features = []

    # Créer une matrice représentant l'état du plateau
    # (1 pour pions blancs, -1 pour pions noirs, 2/-2 pour dames)
    piece_map = np.zeros((BOARD_SIZE, BOARD_SIZE))

    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            piece = board.get_piece(row, col)
            if piece:
                # Valeur positive pour pièces blanches, négative pour noires
                # Valeur doublée pour les dames
                value = 1 if piece.color == WHITE else -1
                if piece.type == DAME:
                    value *= 2
                piece_map[row, col] = value

    # Aplatir la matrice en une liste et l'ajouter aux caractéristiques
    features.extend(piece_map.flatten())

    # Compter le nombre de pièces de chaque type
    white_pawns = 0
    white_kings = 0
    black_pawns = 0
    black_kings = 0

    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            piece = board.get_piece(row, col)
            if piece:
                if piece.color == WHITE:
                    if piece.type == PION:
                        white_pawns += 1
                    else:
                        white_kings += 1
                else:
                    if piece.type == PION:
                        black_pawns += 1
                    else:
                        black_kings += 1

    # Ajouter les compteurs aux caractéristiques
    features.extend([white_pawns, white_kings, black_pawns, black_kings])

    # Analyser les pièces en danger (qui peuvent être capturées au prochain coup)
    white_in_danger = 0
    black_in_danger = 0

    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            piece = board.get_piece(row, col)
            if not piece:
                continue

            # Pour chaque pièce, vérifier si elle peut être capturée par l'adversaire
            opponent_color = BLACK if piece.color == WHITE else WHITE
            for opp_row in range(BOARD_SIZE):
                for opp_col in range(BOARD_SIZE):
                    opp_piece = board.get_piece(opp_row, opp_col)
                    if opp_piece and opp_piece.color == opponent_color:
                        # Obtenir toutes les captures possibles pour cette pièce adverse
                        captures = board._get_captures(opp_row, opp_col)
                        for _, captured in captures.items():
                            for capt_row, capt_col in captured:
                                if (capt_row, capt_col) == (row, col):
                                    if piece.color == WHITE:
                                        white_in_danger += 1
                                    else:
                                        black_in_danger += 1

    # Ajouter le nombre de pièces en danger aux caractéristiques
    features.extend([white_in_danger, black_in_danger])

    return features


class DataProcessor:
    """
    Classe principale pour le traitement et l'analyse des données de jeu.

    Cette classe fournit des méthodes pour charger les données des parties précédentes,
    reconstruire les états de plateau, extraire des caractéristiques pour l'IA, et
    calculer diverses statistiques sur les parties jouées.
    """

    def __init__(self, data_dir=None):
        """
        Initialise le processeur de données.

        Args:
            data_dir (str, optional): Chemin vers le répertoire contenant les données.
                                     Par défaut, utilise "data/games".
        """
        self.data_dir = data_dir or os.path.join("data", "games")

    def get_game_files(self):
        """
        Récupère la liste de tous les fichiers de jeu CSV.

        Cette méthode cherche tous les fichiers commençant par "game_" et
        se terminant par ".csv" dans le répertoire de données.

        Returns:
            list: Liste des chemins complets vers les fichiers de jeu
        """
        files = []
        if os.path.exists(self.data_dir):
            for file in os.listdir(self.data_dir):
                if file.startswith("game_") and file.endswith(".csv") and not file == "games_history.csv":
                    files.append(os.path.join(self.data_dir, file))
        return files

    def load_game_history(self):
        """
        Charge le fichier d'historique global des parties.

        Le fichier games_history.csv contient un résumé de toutes les parties
        jouées, avec leur résultat, leur durée, etc.

        Returns:
            DataFrame: Un DataFrame pandas contenant l'historique des parties,
                      ou un DataFrame vide en cas d'erreur
        """
        history_file = os.path.join(self.data_dir, "games_history.csv")

        if not os.path.exists(history_file):
            return pd.DataFrame()

        try:
            if os.path.getsize(history_file) == 0:
                return pd.DataFrame()

            return pd.read_csv(history_file)
        except Exception as e:
            if "No columns to parse from file" in str(e):
                return pd.DataFrame()
            print(f"Erreur lors du chargement de l'historique: {e}")
            return pd.DataFrame()

    def load_game_moves(self, game_id=None):
        """
        Charge les mouvements de toutes les parties ou d'une partie spécifique.

        Cette méthode est CRUCIALE pour l'IA car elle lui permet d'accéder
        à tous les mouvements enregistrés dans les parties précédentes.

        Args:
            game_id (str, optional): ID de la partie à charger.
                                    Si None, charge toutes les parties.

        Returns:
            DataFrame: Un DataFrame pandas contenant tous les mouvements
        """
        files = self.get_game_files()
        moves_data = []

        # Parcourir tous les fichiers de jeu
        for file in files:
            # Si un game_id est spécifié, ignorer les fichiers qui ne correspondent pas
            if game_id and game_id not in file:
                continue

            try:
                with open(file, 'r', newline='') as f:
                    reader = csv.reader(f)
                    headers = next(reader)  # Lire l'en-tête

                    # Lire chaque ligne et créer un dictionnaire pour ce mouvement
                    for row in reader:
                        if len(row) == len(headers):
                            move_data = dict(zip(headers, row))
                            moves_data.append(move_data)
            except Exception as e:
                print(f"Erreur lors du chargement de {file}: {e}")

        # Retourner un DataFrame avec tous les mouvements
        return pd.DataFrame(moves_data)

    def reconstruct_board_state(self, game_id, move_number):
        """
        Reconstruit l'état du plateau à un moment précis d'une partie.

        Cette méthode "rejoue" tous les mouvements d'une partie jusqu'à
        un certain point pour recréer l'état exact du plateau à ce moment-là.

        Args:
            game_id (str): ID de la partie à reconstruire
            move_number (int): Numéro du mouvement jusqu'auquel reconstruire

        Returns:
            Board: Un objet Board représentant l'état du plateau
        """
        moves = self.load_game_moves(game_id)

        # Filtrer pour ne garder que les mouvements de la partie spécifiée
        moves = moves[moves['game_id'] == game_id]

        if moves.empty:
            return Board()  # Retourner un plateau vide si aucun mouvement

        # Convertir les numéros de mouvement en nombres et filtrer
        moves['move_number'] = pd.to_numeric(moves['move_number'], errors='coerce')
        moves = moves[moves['move_number'] <= move_number]
        moves = moves.sort_values(by='move_number')

        # Créer un nouveau plateau et y appliquer tous les mouvements
        board = Board()

        for _, move in moves.iterrows():
            try:
                from_row = int(move['from_row'])
                from_col = int(move['from_col'])
                to_row = int(move['to_row'])
                to_col = int(move['to_col'])

                # Appliquer les captures si présentes
                captures_str = move['captures']
                if captures_str and captures_str != '':
                    for capture in captures_str.split(';'):
                        if capture:
                            try:
                                capt_row, capt_col = map(int, capture.split(','))
                                board.remove_piece(capt_row, capt_col)
                            except (ValueError, TypeError):
                                continue

                # Déplacer la pièce
                board.move_piece(from_row, from_col, to_row, to_col)

                # Appliquer la promotion si nécessaire
                promotion = move['promotion']
                if isinstance(promotion, str) and promotion.lower() == 'true':
                    piece = board.get_piece(to_row, to_col)
                    if piece:
                        piece.type = DAME
            except (ValueError, TypeError, KeyError):
                continue

        return board

    def extract_features_for_ai(self, num_games=None):
        """
        Extrait des caractéristiques et labels pour entraîner l'IA.

        Cette méthode prépare des données structurées pour que l'IA
        puisse apprendre des parties précédentes. Elle associe des états
        de plateau (features) aux mouvements qui ont été joués (labels).

        Args:
            num_games (int, optional): Nombre de parties à utiliser.
                                      Si None, utilise toutes les parties.

        Returns:
            tuple: (features, labels) - Deux arrays numpy contenant
                  les caractéristiques et les labels correspondants
        """
        history = self.load_game_history()

        if history.empty:
            return np.array([]), np.array([])

        # Limiter le nombre de parties si spécifié
        if num_games and num_games < len(history):
            history = history.sort_values(by='end_time', ascending=False).head(num_games)

        game_ids = history['game_id'].tolist()

        features = []
        labels = []

        # Pour chaque partie
        for game_id in game_ids:
            moves = self.load_game_moves(game_id)
            if moves.empty:
                continue

            moves = moves[moves['game_id'] == game_id]

            # Pour chaque mouvement (sauf le premier)
            for _, move in moves.iterrows():
                try:
                    move_number = int(move['move_number'])
                    if move_number <= 1:
                        continue  # Ignorer le premier mouvement

                    # Reconstruire l'état du plateau juste avant ce mouvement
                    board_before = self.reconstruct_board_state(game_id, move_number - 1)

                    # Extraire les caractéristiques de cet état
                    board_features = _extract_board_features(board_before)

                    # Le label est le mouvement qui a été joué dans cette situation
                    label = (
                        int(move['from_row']),
                        int(move['from_col']),
                        int(move['to_row']),
                        int(move['to_col'])
                    )

                    features.append(board_features)
                    labels.append(label)
                except (ValueError, TypeError, KeyError):
                    continue

        return np.array(features), np.array(labels)

    def get_win_rates(self):
        """
        Calcule les taux de victoire pour chaque couleur.

        Returns:
            dict: Dictionnaire contenant les pourcentages de victoire
                 pour WHITE, BLACK, et 'draw' (match nul)
        """
        history = self.load_game_history()

        if history.empty:
            return {WHITE: 0, BLACK: 0, 'draw': 0}

        # Compter les occurrences de chaque résultat
        win_counts = history['winner'].value_counts()
        total_games = len(history)

        # Calculer les pourcentages
        win_rates = {}
        for color in [WHITE, BLACK, 'draw']:
            if color in win_counts:
                win_rates[color] = (win_counts[color] / total_games) * 100
            else:
                win_rates[color] = 0

        return win_rates

    def get_average_moves_per_game(self):
        """
        Calcule le nombre moyen de coups par partie.

        Returns:
            float: Nombre moyen de coups par partie
        """
        history = self.load_game_history()

        if history.empty:
            return 0

        if 'total_moves' in history.columns:
            return history['total_moves'].astype(int).mean()
        return 0

    def get_capture_statistics(self):
        """
        Calcule des statistiques sur les captures.

        Returns:
            dict: Dictionnaire contenant le nombre total de captures,
                 les captures par couleur, et la moyenne par partie
        """
        moves_data = self.load_game_moves()

        if moves_data.empty:
            return {'total': 0, WHITE: 0, BLACK: 0, 'per_game': 0}

        if 'captures' in moves_data.columns:
            # Compter le nombre de pièces capturées dans chaque mouvement
            moves_data['capture_count'] = moves_data['captures'].apply(
                lambda x: 0 if pd.isna(x) or x == '' else len(str(x).split(';'))
            )

            # Calculer les statistiques
            total_captures = moves_data['capture_count'].sum()
            white_captures = moves_data[moves_data['player'] == WHITE]['capture_count'].sum() if WHITE in moves_data['player'].values else 0
            black_captures = moves_data[moves_data['player'] == BLACK]['capture_count'].sum() if BLACK in moves_data['player'].values else 0

            # Calculer la moyenne par partie
            history = self.load_game_history()
            total_games = len(history) if not history.empty else 1

            return {
                'total': total_captures,
                WHITE: white_captures,
                BLACK: black_captures,
                'per_game': total_captures / total_games
            }

        return {'total': 0, WHITE: 0, BLACK: 0, 'per_game': 0}

    def get_promotion_statistics(self):
        """
        Calcule des statistiques sur les promotions.

        Returns:
            dict: Dictionnaire contenant le nombre total de promotions,
                 les promotions par couleur, et la moyenne par partie
        """
        moves_data = self.load_game_moves()

        if moves_data.empty or 'promotion' not in moves_data.columns:
            return {'total': 0, WHITE: 0, BLACK: 0, 'per_game': 0}

        # Convertir les valeurs de promotion en booléens
        moves_data['promotion'] = moves_data['promotion'].apply(
            lambda x: str(x).lower() == 'true' if not pd.isna(x) else False
        )

        # Calculer les statistiques
        total_promotions = moves_data['promotion'].sum()
        white_promotions = moves_data[moves_data['player'] == WHITE]['promotion'].sum() if WHITE in moves_data['player'].values else 0
        black_promotions = moves_data[moves_data['player'] == BLACK]['promotion'].sum() if BLACK in moves_data['player'].values else 0

        # Calculer la moyenne par partie
        history = self.load_game_history()
        total_games = len(history) if not history.empty else 1

        return {
            'total': total_promotions,
            WHITE: white_promotions,
            BLACK: black_promotions,
            'per_game': total_promotions / total_games
        }

    def get_position_heatmap_data(self):
        """
        Génère des données pour créer une heatmap des positions les plus utilisées.

        Cette méthode compte combien de fois chaque case du plateau a été
        utilisée comme destination d'un mouvement, pour identifier les
        positions les plus stratégiques.

        Returns:
            ndarray: Matrice 2D contenant les comptes pour chaque position
        """
        moves_data = self.load_game_moves()

        if moves_data.empty:
            return np.zeros((BOARD_SIZE, BOARD_SIZE))

        # Initialiser une matrice pour compter les positions
        position_matrix = np.zeros((BOARD_SIZE, BOARD_SIZE))

        # Compter les occurrences de chaque position d'arrivée
        for _, move in moves_data.iterrows():
            try:
                to_row = int(move['to_row'])
                to_col = int(move['to_col'])
                position_matrix[to_row, to_col] += 1
            except (ValueError, TypeError, KeyError):
                continue

        return position_matrix