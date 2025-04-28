import csv
import os

import numpy as np
import pandas as pd

from game.board import Board
from game.constants import *


def _extract_board_features(board):
    features = []

    piece_map = np.zeros((BOARD_SIZE, BOARD_SIZE))

    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            piece = board.get_piece(row, col)
            if piece:
                value = 1 if piece.color == WHITE else -1
                if piece.type == DAME:
                    value *= 2
                piece_map[row, col] = value

    features.extend(piece_map.flatten())

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

    features.extend([white_pawns, white_kings, black_pawns, black_kings])

    white_in_danger = 0
    black_in_danger = 0

    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            piece = board.get_piece(row, col)
            if not piece:
                continue

            opponent_color = BLACK if piece.color == WHITE else WHITE
            for opp_row in range(BOARD_SIZE):
                for opp_col in range(BOARD_SIZE):
                    opp_piece = board.get_piece(opp_row, opp_col)
                    if opp_piece and opp_piece.color == opponent_color:
                        captures = board._get_captures(opp_row, opp_col)
                        for _, captured in captures.items():
                            for capt_row, capt_col in captured:
                                if (capt_row, capt_col) == (row, col):
                                    if piece.color == WHITE:
                                        white_in_danger += 1
                                    else:
                                        black_in_danger += 1

    features.extend([white_in_danger, black_in_danger])

    return features


class DataProcessor:
    def __init__(self, data_dir=None):
        self.data_dir = data_dir or os.path.join("data", "games")

    def get_game_files(self):
        files = []
        if os.path.exists(self.data_dir):
            for file in os.listdir(self.data_dir):
                if file.startswith("game_") and file.endswith(".csv") and not file == "games_history.csv":
                    files.append(os.path.join(self.data_dir, file))
        return files

    def load_game_history(self):
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
        files = self.get_game_files()
        moves_data = []

        for file in files:
            if game_id and game_id not in file:
                continue

            try:
                with open(file, 'r', newline='') as f:
                    reader = csv.reader(f)
                    headers = next(reader)

                    for row in reader:
                        if len(row) == len(headers):
                            move_data = dict(zip(headers, row))
                            moves_data.append(move_data)
            except Exception as e:
                print(f"Erreur lors du chargement de {file}: {e}")

        return pd.DataFrame(moves_data)

    def reconstruct_board_state(self, game_id, move_number):
        moves = self.load_game_moves(game_id)

        moves = moves[moves['game_id'] == game_id]

        if moves.empty:
            return Board()

        moves['move_number'] = pd.to_numeric(moves['move_number'], errors='coerce')
        moves = moves[moves['move_number'] <= move_number]
        moves = moves.sort_values(by='move_number')


        board = Board()

        for _, move in moves.iterrows():
            try:
                from_row = int(move['from_row'])
                from_col = int(move['from_col'])
                to_row = int(move['to_row'])
                to_col = int(move['to_col'])

                captures_str = move['captures']
                if captures_str and captures_str != '':
                    for capture in captures_str.split(';'):
                        if capture:
                            try:
                                capt_row, capt_col = map(int, capture.split(','))
                                board.remove_piece(capt_row, capt_col)
                            except (ValueError, TypeError):
                                continue

                board.move_piece(from_row, from_col, to_row, to_col)

                promotion = move['promotion']
                if isinstance(promotion, str) and promotion.lower() == 'true':
                    piece = board.get_piece(to_row, to_col)
                    if piece:
                        piece.type = DAME
            except (ValueError, TypeError, KeyError):
                continue

        return board

    def extract_features_for_ai(self, num_games=None):
        history = self.load_game_history()

        if history.empty:
            return np.array([]), np.array([])

        if num_games and num_games < len(history):
            history = history.sort_values(by='end_time', ascending=False).head(num_games)

        game_ids = history['game_id'].tolist()

        features = []
        labels = []

        for game_id in game_ids:
            moves = self.load_game_moves(game_id)
            if moves.empty:
                continue

            moves = moves[moves['game_id'] == game_id]

            for _, move in moves.iterrows():
                try:
                    move_number = int(move['move_number'])
                    if move_number <= 1:
                        continue

                    board_before = self.reconstruct_board_state(game_id, move_number - 1)

                    board_features = _extract_board_features(board_before)

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
        history = self.load_game_history()

        if history.empty:
            return {WHITE: 0, BLACK: 0, 'draw': 0}

        win_counts = history['winner'].value_counts()
        total_games = len(history)

        win_rates = {}
        for color in [WHITE, BLACK, 'draw']:
            if color in win_counts:
                win_rates[color] = (win_counts[color] / total_games) * 100
            else:
                win_rates[color] = 0

        return win_rates

    def get_average_moves_per_game(self):
        history = self.load_game_history()

        if history.empty:
            return 0

        if 'total_moves' in history.columns:
            return history['total_moves'].astype(int).mean()
        return 0

    def get_capture_statistics(self):
        moves_data = self.load_game_moves()

        if moves_data.empty:
            return {'total': 0, WHITE: 0, BLACK: 0, 'per_game': 0}

        if 'captures' in moves_data.columns:
            moves_data['capture_count'] = moves_data['captures'].apply(
                lambda x: 0 if pd.isna(x) or x == '' else len(str(x).split(';'))
            )

            total_captures = moves_data['capture_count'].sum()
            white_captures = moves_data[moves_data['player'] == WHITE]['capture_count'].sum() if WHITE in moves_data['player'].values else 0
            black_captures = moves_data[moves_data['player'] == BLACK]['capture_count'].sum() if BLACK in moves_data['player'].values else 0

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
        moves_data = self.load_game_moves()

        if moves_data.empty or 'promotion' not in moves_data.columns:
            return {'total': 0, WHITE: 0, BLACK: 0, 'per_game': 0}

        moves_data['promotion'] = moves_data['promotion'].apply(
            lambda x: str(x).lower() == 'true' if not pd.isna(x) else False
        )

        total_promotions = moves_data['promotion'].sum()
        white_promotions = moves_data[moves_data['player'] == WHITE]['promotion'].sum() if WHITE in moves_data['player'].values else 0
        black_promotions = moves_data[moves_data['player'] == BLACK]['promotion'].sum() if BLACK in moves_data['player'].values else 0

        history = self.load_game_history()
        total_games = len(history) if not history.empty else 1

        return {
            'total': total_promotions,
            WHITE: white_promotions,
            BLACK: black_promotions,
            'per_game': total_promotions / total_games
        }

    def get_position_heatmap_data(self):
        moves_data = self.load_game_moves()

        if moves_data.empty:
            return np.zeros((BOARD_SIZE, BOARD_SIZE))

        position_matrix = np.zeros((BOARD_SIZE, BOARD_SIZE))

        for _, move in moves_data.iterrows():
            try:
                to_row = int(move['to_row'])
                to_col = int(move['to_col'])
                position_matrix[to_row, to_col] += 1
            except (ValueError, TypeError, KeyError):
                continue

        return position_matrix