import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure

from data_management.data_processor import DataProcessor
from game.constants import *


class StatsGenerator:
    def __init__(self):
        self.data_processor = DataProcessor()
        self.output_dir = os.path.join("data", "stats")
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_all_stats(self):
        stats_files = [self.generate_captures_stats(), self.generate_promotion_stats(), self.generate_heatmap_stats()]

        return [f for f in stats_files if f]

    def generate_captures_stats(self):
        try:
            moves_data = self.data_processor.load_game_moves()

            if moves_data.empty:
                return None

            moves_data['has_capture'] = moves_data['captures'].apply(lambda x: 0 if pd.isna(x) or x == '' else 1)
            moves_data['capture_count'] = moves_data['captures'].apply(
                lambda x: 0 if pd.isna(x) or x == '' else len(x.split(';'))
            )

            captures_by_game_player = moves_data.groupby(['game_id', 'player'])['capture_count'].sum().reset_index()

            captures_by_player = captures_by_game_player.groupby('player')['capture_count'].mean().reset_index()

            plt.figure(figsize=(10, 6))

            colors = {'white': 'lightgray', 'black': 'dimgray'}

            plt.bar(captures_by_player['player'], captures_by_player['capture_count'],
                    color=[colors.get(p.lower(), 'blue') for p in captures_by_player['player']])

            plt.title('Nombre moyen de captures par partie et par joueur', fontsize=16)
            plt.ylabel('Nombre moyen de captures', fontsize=12)
            plt.grid(axis='y', linestyle='--', alpha=0.7)

            for i, v in enumerate(captures_by_player['capture_count']):
                plt.text(i, v + 0.1, f"{v:.1f}", ha='center', fontweight='bold')

            output_file = os.path.join(self.output_dir, "captures.png")
            plt.tight_layout()
            plt.savefig(output_file)
            plt.close()

            return output_file

        except Exception as e:
            print(f"Erreur lors de la génération des stats de captures: {e}")
            return None

    def generate_promotion_stats(self):
        try:
            moves_data = self.data_processor.load_game_moves()

            if moves_data.empty:
                return None

            moves_data['promotion'] = moves_data['promotion'].apply(
                lambda x: x.lower() == 'true' if isinstance(x, str) else bool(x)
            )

            promotions_by_game_player = moves_data.groupby(['game_id', 'player'])['promotion'].sum().reset_index()

            promotions_by_player = promotions_by_game_player.groupby('player')['promotion'].mean().reset_index()

            plt.figure(figsize=(10, 6))

            colors = {'white': 'lightgray', 'black': 'dimgray'}

            plt.bar(promotions_by_player['player'], promotions_by_player['promotion'],
                    color=[colors.get(p.lower(), 'blue') for p in promotions_by_player['player']])

            plt.title('Nombre moyen de promotions par partie et par joueur', fontsize=16)
            plt.ylabel('Nombre moyen de promotions', fontsize=12)
            plt.grid(axis='y', linestyle='--', alpha=0.7)

            for i, v in enumerate(promotions_by_player['promotion']):
                plt.text(i, v + 0.02, f"{v:.2f}", ha='center', fontweight='bold')

            output_file = os.path.join(self.output_dir, "promotions.png")
            plt.tight_layout()
            plt.savefig(output_file)
            plt.close()

            return output_file

        except Exception as e:
            print(f"Erreur lors de la génération des stats de promotions: {e}")
            return None

    def generate_heatmap_stats(self):
        try:
            moves_data = self.data_processor.load_game_moves()

            if moves_data.empty:
                return None

            position_matrix = np.zeros((BOARD_SIZE, BOARD_SIZE))

            for _, move in moves_data.iterrows():
                try:
                    to_row = int(move['to_row'])
                    to_col = int(move['to_col'])
                    position_matrix[to_row, to_col] += 1
                except (ValueError, TypeError, IndexError):
                    continue

            plt.figure(figsize=(10, 10))

            mask = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=bool)
            for row in range(BOARD_SIZE):
                for col in range(BOARD_SIZE):
                    if (row + col) % 2 == 0:
                        mask[row, col] = True

            masked_position_matrix = np.ma.array(position_matrix, mask=mask)

            cmap = plt.cm.viridis
            cmap.set_bad('white')

            plt.imshow(masked_position_matrix, cmap=cmap)
            plt.colorbar(label='Fréquence d\'utilisation')

            plt.title('Heatmap des positions les plus utilisées', fontsize=16)

            plt.xticks(range(BOARD_SIZE))
            plt.yticks(range(BOARD_SIZE))
            plt.grid(False)

            output_file = os.path.join(self.output_dir, "position_heatmap.png")
            plt.tight_layout()
            plt.savefig(output_file)
            plt.close()

            return output_file

        except Exception as e:
            print(f"Erreur lors de la génération de la heatmap: {e}")
            return None