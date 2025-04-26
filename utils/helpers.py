import os
import datetime
import json
import numpy as np
import pandas as pd
from game.constants import *

def get_current_date_time():
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d_%H-%M-%S")

def board_to_notation(from_pos, to_pos):
    from_row, from_col = from_pos
    to_row, to_col = to_pos

    from_col_letter = chr(97 + from_col)
    to_col_letter = chr(97 + to_col)

    from_row_num = BOARD_SIZE - from_row
    to_row_num = BOARD_SIZE - to_row

    return f"{from_col_letter}{from_row_num}-{to_col_letter}{to_row_num}"

def notation_to_position(notation):
    parts = notation.split('-')
    if len(parts) != 2:
        raise ValueError("Format de notation invalide. Utiliser par exemple 'a3-b4'")

    from_pos, to_pos = parts

    from_col_letter, from_row_num = from_pos[0], int(from_pos[1:])
    to_col_letter, to_row_num = to_pos[0], int(to_pos[1:])

    from_col = ord(from_col_letter) - 97
    to_col = ord(to_col_letter) - 97

    from_row = BOARD_SIZE - from_row_num
    to_row = BOARD_SIZE - to_row_num

    return (from_row, from_col), (to_row, to_col)

def export_data_to_json(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

def import_data_from_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return None

def create_board_matrix_from_dict(board_dict):
    matrix = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=np.int8)

    for pos, piece in board_dict.items():
        row, col = pos
        value = 1 if piece['color'] == WHITE else -1
        if piece['type'] == DAME:
            value *= 2
        matrix[row, col] = value

    return matrix

def get_basic_statistics():
    stats = {
        'total_games': 0,
        'white_wins': 0,
        'black_wins': 0,
        'avg_moves': 0,
        'total_captures': 0
    }

    history_file = os.path.join("data", "games", "games_history.csv")

    if not os.path.exists(history_file):
        return stats

    try:
        history = pd.read_csv(history_file)

        stats['total_games'] = len(history)

        stats['white_wins'] = len(history[history['winner'] == WHITE])
        stats['black_wins'] = len(history[history['winner'] == BLACK])

        stats['avg_moves'] = history['total_moves'].mean()

    except Exception as e:
        print(f"Erreur lors de la récupération des statistiques: {e}")

    return stats