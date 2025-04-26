import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import io
import os
from game.constants import *

class PlotGenerator:
    @staticmethod
    def create_win_rate_pie_chart(data_processor):
        history = data_processor.load_game_history()

        if history.empty:
            return None

        win_counts = history['winner'].value_counts()

        labels = []
        sizes = []
        colors = []

        for color in [WHITE, BLACK, 'draw']:
            if color in win_counts:
                labels.append(f"{color.capitalize()}")
                sizes.append(win_counts[color])
                colors.append('white' if color == WHITE else
                             'black' if color == BLACK else 'gray')

        plt.figure(figsize=(8, 8))
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                shadow=True, startangle=90)
        plt.axis('equal')
        plt.title('Répartition des victoires par couleur')

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)

        return buf.getvalue()

    @staticmethod
    def create_move_distribution_chart(data_processor, player=None):
        moves_data = data_processor.load_game_moves()

        if moves_data.empty:
            return None

        if player:
            moves_data = moves_data[moves_data['player'] == player]

        moves_data['move_type'] = 'Normal'

        moves_data.loc[moves_data['captures'].notna() & (moves_data['captures'] != ''), 'move_type'] = 'Capture'

        moves_data.loc[moves_data['promotion'].map(lambda x: str(x).lower() == 'true'), 'move_type'] = 'Promotion'

        captures_mask = moves_data['captures'].notna() & (moves_data['captures'] != '')
        promotion_mask = moves_data['promotion'].map(lambda x: str(x).lower() == 'true')
        moves_data.loc[captures_mask & promotion_mask, 'move_type'] = 'Capture + Promotion'

        move_counts = moves_data['move_type'].value_counts()

        plt.figure(figsize=(10, 6))

        colors = {
            'Normal': 'skyblue',
            'Capture': 'salmon',
            'Promotion': 'lightgreen',
            'Capture + Promotion': 'gold'
        }

        bars = plt.bar(move_counts.index, move_counts.values,
                color=[colors.get(t, 'gray') for t in move_counts.index])

        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{height}', ha='center', fontweight='bold')

        plt.title(f'Distribution des types de coups{" pour " + player if player else ""}')
        plt.ylabel('Nombre de coups')
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)

        return buf.getvalue()

    @staticmethod
    def create_performance_trend_chart(data_processor, player=None):
        history = data_processor.load_game_history()

        if history.empty:
            return None

        history['end_time'] = pd.to_datetime(history['end_time'])

        history = history.sort_values('end_time')

        if player:
            history['result'] = (history['winner'] == player).astype(int)
        else:
            history['result'] = np.where(history['winner'] == WHITE, 1,
                                         np.where(history['winner'] == BLACK, -1, 0))

        history['moving_avg'] = history['result'].rolling(window=min(5, len(history)), min_periods=1).mean()

        plt.figure(figsize=(12, 6))

        plt.plot(history['end_time'], history['moving_avg'], marker='o', linestyle='-', color='blue')

        if player:
            plt.title(f'Évolution du taux de victoire pour {player}')
            plt.axhline(y=0.5, color='r', linestyle='--', alpha=0.7)
            plt.ylabel('Taux de victoire (moyenne mobile)')
            plt.ylim(0, 1)
        else:
            plt.title('Évolution des performances (Blanc vs Noir)')
            plt.axhline(y=0, color='r', linestyle='--', alpha=0.7)
            plt.ylabel('Performance (1=Blanc, -1=Noir, 0=Nul)')
            plt.ylim(-1, 1)

        plt.xlabel('Date')
        plt.grid(True, linestyle='--', alpha=0.7)

        plt.xticks(rotation=45)

        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close()
        buf.seek(0)

        return buf.getvalue()

    @staticmethod
    def create_game_length_histogram(data_processor):
        history = data_processor.load_game_history()

        if history.empty:
            return None

        history['total_moves'] = pd.to_numeric(history['total_moves'])

        plt.figure(figsize=(10, 6))

        max_moves = history['total_moves'].max()
        min_moves = history['total_moves'].min()
        bin_width = max(1, (max_moves - min_moves) // 10)
        bins = range(int(min_moves), int(max_moves) + bin_width, bin_width)

        plt.hist(history['total_moves'], bins=bins, color='skyblue', edgecolor='black', alpha=0.7)

        plt.title('Distribution du nombre de coups par partie')
        plt.xlabel('Nombre de coups')
        plt.ylabel('Nombre de parties')
        plt.grid(True, linestyle='--', alpha=0.7)

        avg_moves = history['total_moves'].mean()
        median_moves = history['total_moves'].median()

        plt.axvline(x=avg_moves, color='r', linestyle='--', alpha=0.7, label=f'Moyenne: {avg_moves:.1f}')
        plt.axvline(x=median_moves, color='g', linestyle='--', alpha=0.7, label=f'Médiane: {median_moves:.1f}')
        plt.legend()

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)

        return buf.getvalue()