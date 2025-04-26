import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from data_management.data_processor import DataProcessor
from game.constants import *

class StatsGenerator:
    def __init__(self):
        self.data_processor = DataProcessor()
        self.output_dir = os.path.join("data", "stats")
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_all_stats(self):
        stats_files = []

        stats_files.append(self.generate_win_rate_stats())
        stats_files.append(self.generate_game_length_stats())
        stats_files.append(self.generate_captures_stats())
        stats_files.append(self.generate_promotion_stats())
        stats_files.append(self.generate_heatmap_stats())

        summary_file = self.generate_statistics_summary()
        if summary_file:
            stats_files.append(summary_file)

        return [f for f in stats_files if f]

    def generate_win_rate_stats(self):
        try:
            history = self.data_processor.load_game_history()

            if history.empty or 'winner' not in history.columns:
                print("Attention: Pas assez de données d'historique pour générer des statistiques de victoire.")
                plt.figure(figsize=(10, 6))
                plt.text(0.5, 0.5, "Pas assez de données - Jouez plus de parties complètes",
                        ha='center', va='center', fontsize=16)
                plt.axis('off')

                output_file = os.path.join(self.output_dir, "win_rate.png")
                plt.tight_layout()
                plt.savefig(output_file)
                plt.close()

                return output_file

            win_counts = history['winner'].value_counts()

            plt.figure(figsize=(10, 6))

            colors = ['white', 'black', 'gray']

            labels = []
            values = []
            chart_colors = []

            for color in [WHITE, BLACK, 'draw']:
                if color in win_counts:
                    labels.append(f"{color.capitalize()}")
                    values.append(win_counts[color])
                    chart_colors.append(colors[0] if color == WHITE else
                                        colors[1] if color == BLACK else colors[2])

            plt.bar(labels, values, color=chart_colors)

            total_games = sum(values)
            for i, v in enumerate(values):
                percentage = (v / total_games) * 100
                plt.text(i, v + 0.5, f"{percentage:.1f}%", ha='center', fontweight='bold')

            plt.title('Taux de victoire par couleur', fontsize=16)
            plt.ylabel('Nombre de parties gagnées', fontsize=12)
            plt.grid(axis='y', linestyle='--', alpha=0.7)

            win_rate = {}
            for color in [WHITE, BLACK]:
                if color in win_counts:
                    win_rate[color] = (win_counts[color] / total_games) * 100
                else:
                    win_rate[color] = 0

            plt.figtext(0.5, 0.01,
                        f"Total des parties: {total_games} | "
                        f"Taux de victoire Blanc: {win_rate.get(WHITE, 0):.1f}% | "
                        f"Taux de victoire Noir: {win_rate.get(BLACK, 0):.1f}%",
                        ha="center", fontsize=12, bbox={"facecolor":"orange", "alpha":0.2, "pad":5})

            output_file = os.path.join(self.output_dir, "win_rate.png")
            plt.tight_layout()
            plt.savefig(output_file)
            plt.close()

            return output_file

        except Exception as e:
            print(f"Erreur lors de la génération des stats de taux de victoire: {e}")
            return None

    def generate_game_length_stats(self):
        try:
            history = self.data_processor.load_game_history()

            if history.empty:
                return None

            plt.figure(figsize=(10, 6))

            history['total_moves'] = pd.to_numeric(history['total_moves'])

            max_moves = history['total_moves'].max()
            min_moves = history['total_moves'].min()

            bin_width = max(1, (max_moves - min_moves) // 10)
            bins = range(int(min_moves), int(max_moves) + bin_width, bin_width)

            plt.hist(history['total_moves'], bins=bins, color='skyblue', edgecolor='black', alpha=0.7)

            plt.title('Distribution du nombre de coups par partie', fontsize=16)
            plt.xlabel('Nombre de coups', fontsize=12)
            plt.ylabel('Nombre de parties', fontsize=12)
            plt.grid(True, linestyle='--', alpha=0.7)

            avg_moves = history['total_moves'].mean()
            median_moves = history['total_moves'].median()
            max_moves = history['total_moves'].max()
            min_moves = history['total_moves'].min()

            plt.figtext(0.5, 0.01,
                        f"Moyenne: {avg_moves:.1f} coups | "
                        f"Médiane: {median_moves:.1f} coups | "
                        f"Min: {min_moves} coups | "
                        f"Max: {max_moves} coups",
                        ha="center", fontsize=12, bbox={"facecolor":"lightgreen", "alpha":0.2, "pad":5})

            output_file = os.path.join(self.output_dir, "game_length.png")
            plt.tight_layout()
            plt.savefig(output_file)
            plt.close()

            return output_file

        except Exception as e:
            print(f"Erreur lors de la génération des stats de durée de partie: {e}")
            return None

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

    def generate_statistics_summary(self):
        try:
            history = self.data_processor.load_game_history()
            moves_data = self.data_processor.load_game_moves()

            if history.empty or moves_data.empty:
                return None

            stats = {}

            stats['total_games'] = len(history)

            win_counts = history['winner'].value_counts()
            stats['white_wins'] = win_counts.get(WHITE, 0)
            stats['black_wins'] = win_counts.get(BLACK, 0)
            stats['draws'] = win_counts.get('draw', 0)

            stats['white_win_rate'] = (stats['white_wins'] / stats['total_games']) * 100
            stats['black_win_rate'] = (stats['black_wins'] / stats['total_games']) * 100
            stats['draw_rate'] = (stats['draws'] / stats['total_games']) * 100

            stats['avg_moves_per_game'] = history['total_moves'].mean()
            stats['max_moves'] = history['total_moves'].max()
            stats['min_moves'] = history['total_moves'].min()

            moves_data['capture_count'] = moves_data['captures'].apply(
                lambda x: 0 if pd.isna(x) or x == '' else len(x.split(';'))
            )
            stats['total_captures'] = moves_data['capture_count'].sum()
            stats['avg_captures_per_game'] = stats['total_captures'] / stats['total_games']

            white_captures = moves_data[moves_data['player'] == WHITE]['capture_count'].sum()
            black_captures = moves_data[moves_data['player'] == BLACK]['capture_count'].sum()
            stats['white_captures'] = white_captures
            stats['black_captures'] = black_captures
            stats['white_captures_per_game'] = white_captures / stats['total_games']
            stats['black_captures_per_game'] = black_captures / stats['total_games']

            moves_data['promotion'] = moves_data['promotion'].apply(
                lambda x: x.lower() == 'true' if isinstance(x, str) else bool(x)
            )
            stats['total_promotions'] = moves_data['promotion'].sum()
            stats['white_promotions'] = moves_data[moves_data['player'] == WHITE]['promotion'].sum()
            stats['black_promotions'] = moves_data[moves_data['player'] == BLACK]['promotion'].sum()

            stats_df = pd.DataFrame([stats])
            output_file = os.path.join(self.output_dir, "performance.csv")
            stats_df.to_csv(output_file, index=False)

            return output_file

        except Exception as e:
            print(f"Erreur lors de la génération du résumé statistique: {e}")
            return None