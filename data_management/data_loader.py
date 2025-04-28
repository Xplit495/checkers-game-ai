import os

import numpy as np
import pandas as pd

from game.constants import *


def load_performance_stats():
    stats_file = os.path.join("data", "stats", "performance.csv")

    if not os.path.exists(stats_file):
        print(f"Fichier de statistiques introuvable: {stats_file}")
        return pd.DataFrame()

    try:
        return pd.read_csv(stats_file)
    except Exception as e:
        print(f"Erreur lors du chargement des statistiques: {e}")
        return pd.DataFrame()


class DataLoader:
    def __init__(self, data_dir=None):
        self.data_dir = data_dir or os.path.join("data", "games")

    def load_all_games(self):
        if not os.path.exists(self.data_dir):
            print(f"Répertoire de données introuvable: {self.data_dir}")
            return pd.DataFrame()

        game_files = []
        for file in os.listdir(self.data_dir):
            if file.startswith("game_") and file.endswith(".csv") and file != "games_history.csv":
                game_files.append(os.path.join(self.data_dir, file))

        if not game_files:
            print("Aucun fichier de jeu trouvé")
            return pd.DataFrame()

        all_data = []
        for file in game_files:
            try:
                data = pd.read_csv(file)
                all_data.append(data)
            except Exception as e:
                print(f"Erreur lors du chargement de {file}: {e}")

        if not all_data:
            return pd.DataFrame()

        return pd.concat(all_data, ignore_index=True)

    def load_game_history(self):
        history_file = os.path.join(self.data_dir, "games_history.csv")

        if not os.path.exists(history_file):
            print(f"Fichier d'historique introuvable: {history_file}")
            return pd.DataFrame()

        try:
            return pd.read_csv(history_file)
        except Exception as e:
            print(f"Erreur lors du chargement de l'historique: {e}")
            return pd.DataFrame()

    def get_move_matrix(self):
        all_games = self.load_all_games()

        if all_games.empty:
            return np.zeros((BOARD_SIZE, BOARD_SIZE))

        move_matrix = np.zeros((BOARD_SIZE, BOARD_SIZE))

        for _, move in all_games.iterrows():
            try:
                to_row = int(move['to_row'])
                to_col = int(move['to_col'])
                if 0 <= to_row < BOARD_SIZE and 0 <= to_col < BOARD_SIZE:
                    move_matrix[to_row, to_col] += 1
            except (ValueError, KeyError):
                continue

        return move_matrix

    def get_capture_data(self):
        all_games = self.load_all_games()

        if all_games.empty:
            return {'white': 0, 'black': 0}

        all_games['capture_count'] = all_games['captures'].apply(
            lambda x: 0 if pd.isna(x) or x == '' else len(str(x).split(';'))
        )

        white_captures = all_games[all_games['player'] == WHITE]['capture_count'].sum()
        black_captures = all_games[all_games['player'] == BLACK]['capture_count'].sum()

        return {
            'white': white_captures,
            'black': black_captures,
            'total': white_captures + black_captures
        }

    def get_promotion_data(self):
        all_games = self.load_all_games()

        if all_games.empty:
            return {'white': 0, 'black': 0}

        all_games['promotion'] = all_games['promotion'].apply(
            lambda x: x.lower() == 'true' if isinstance(x, str) else bool(x)
        )

        white_promotions = all_games[all_games['player'] == WHITE]['promotion'].sum()
        black_promotions = all_games[all_games['player'] == BLACK]['promotion'].sum()

        return {
            'white': white_promotions,
            'black': black_promotions,
            'total': white_promotions + black_promotions
        }