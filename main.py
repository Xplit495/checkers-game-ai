import sys
import os
import argparse
from ui import game_window as gw
from visualization.stats_generator import StatsGenerator
from data_management.data_processor import DataProcessor

def main():
    """Fonction principale du jeu de dames."""
    parser = argparse.ArgumentParser(description='Jeu de Dames avec IA')
    parser.add_argument('--stats', action='store_true', help='Générer les statistiques et quitter')
    args = parser.parse_args()

    # Si l'option --stats est utilisée, générer les statistiques et quitter
    if args.stats:
        print("Génération des statistiques en cours...")
        stats_generator = StatsGenerator()
        stats_files = stats_generator.generate_all_stats()

        if stats_files:
            print(f"Statistiques générées avec succès dans le dossier data/stats/")
            for file in stats_files:
                print(f" - {file}")
        else:
            print("Aucune statistique n'a pu être générée. Assurez-vous d'avoir des parties enregistrées.")

        return

    # Lancer le jeu
    game_window = gw.GameWindow()
    game_window.run()

if __name__ == "__main__":
    main()