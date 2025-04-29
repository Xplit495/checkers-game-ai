"""
Module d'enregistrement des parties de jeu de dames

Ce module est chargé d'enregistrer chaque mouvement effectué au cours d'une partie
de dames, de les analyser, les classifier et les sauvegarder dans des fichiers CSV.
Ces données enregistrées servent ensuite de base d'apprentissage pour l'IA.
"""

import csv
import os
import uuid
from datetime import datetime


class GameRecorder:
    """
    Classe responsable de l'enregistrement des parties et de leurs mouvements.

    Cette classe joue un rôle CRUCIAL dans le système d'apprentissage de l'IA.
    Elle capture chaque mouvement, l'évalue, et l'enregistre avec son contexte
    et son résultat final. Ces données servent ensuite de "mémoire" à l'IA
    pour apprendre des parties précédentes.
    """

    def __init__(self, auto_save=True, save_interval=3):
        """
        Initialise un enregistreur de partie.

        Args:
            auto_save (bool): Si True, sauvegarde automatiquement les mouvements
                              à intervalles réguliers
            save_interval (int): Nombre de mouvements après lesquels sauvegarder
                                automatiquement (si auto_save est True)
        """
        # Générer un ID unique pour cette partie
        self.game_id = str(uuid.uuid4())[:8]
        self.moves = []  # Liste temporaire des mouvements en attente de sauvegarde
        self.move_count = 0  # Compteur de mouvements
        self.start_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.auto_save = auto_save
        self.save_interval = save_interval

        # Préparer le dossier et le fichier de sauvegarde
        self.data_dir = os.path.join("data", "games")
        os.makedirs(self.data_dir, exist_ok=True)

        # Nom du fichier CSV pour cette partie (format: game_ID_DATE.csv)
        self.filename = os.path.join(self.data_dir, f"game_{self.game_id}_{self.start_time}.csv")

        # Créer le fichier avec les en-têtes
        self._create_file()

        print(f"GameRecorder initialized. Recording to: {self.filename}")

    def _create_file(self):
        """
        Crée le fichier CSV avec les en-têtes pour la nouvelle partie.

        Cette méthode initialise le fichier CSV avec toutes les colonnes
        nécessaires pour enregistrer les informations détaillées sur chaque mouvement.
        """
        with open(self.filename, 'w', newline='') as file:
            writer = csv.writer(file)
            # En-têtes définissant toutes les données qui seront enregistrées pour chaque mouvement
            writer.writerow([
                'game_id',              # Identifiant unique de la partie
                'move_number',          # Numéro séquentiel du mouvement
                'player',               # Couleur du joueur (WHITE ou BLACK)
                'from_row',             # Ligne de départ
                'from_col',             # Colonne de départ
                'to_row',               # Ligne d'arrivée
                'to_col',               # Colonne d'arrivée
                'piece_type',           # Type de pièce (PION ou DAME)
                'captures',             # Pièces capturées (format: "ligne1,col1;ligne2,col2;...")
                'promotion',            # Indique si le mouvement a entraîné une promotion
                'classification',       # Type de mouvement (opening, capture, promotion, etc.)
                'move_score',           # Score attribué au mouvement (qualité stratégique)
                'outcome_contribution', # Contribution au résultat final (pending jusqu'à la fin)
                'timestamp'             # Horodatage du mouvement
            ])
        print(f"Created game record file: {self.filename}")

    def record_move(self, player, from_pos, to_pos, piece_type, captures=None, promotion=False, classification="normal", move_score=0):
        """
        Enregistre un mouvement avec toutes ses caractéristiques.

        Cette méthode est appelée après chaque mouvement pour l'enregistrer
        avec toutes ses informations contextuelles. Ces données sont essentielles
        pour l'IA qui pourra ensuite analyser les mouvements par type, résultat, etc.

        Args:
            player (str): Couleur du joueur (WHITE ou BLACK)
            from_pos (tuple): Position de départ (row, col)
            to_pos (tuple): Position d'arrivée (row, col)
            piece_type (str): Type de pièce (PION ou DAME)
            captures (list, optional): Liste des positions capturées
            promotion (bool, optional): Si le mouvement a entraîné une promotion
            classification (str, optional): Type de mouvement
            move_score (float, optional): Score du mouvement

        Returns:
            list: Les données du mouvement enregistré
        """
        self.move_count += 1

        from_row, from_col = from_pos
        to_row, to_col = to_pos

        # Déterminer automatiquement la classification du mouvement si "normal"
        if classification == "normal":
            # Classification basée sur la phase de jeu
            if self.move_count <= 8:
                classification = "opening"      # Phase d'ouverture
            elif self.move_count > 30:
                classification = "end_game"     # Phase finale
            else:
                classification = "middle_game"  # Phase de milieu de partie

            # Priorité aux captures et promotions dans la classification
            if captures:
                classification = "capture"      # Capture
            elif promotion:
                classification = "promotion"    # Promotion

        # Formater les captures pour le CSV (format: "ligne1,col1;ligne2,col2;...")
        captures_str = ""
        if captures:
            captures_str = ";".join([f"{row},{col}" for row, col in captures])

        # Créer l'entrée complète pour ce mouvement
        move_entry = [
            self.game_id,
            self.move_count,
            player,
            from_row,
            from_col,
            to_row,
            to_col,
            piece_type,
            captures_str,
            promotion,
            classification,
            move_score,
            "pending",  # Sera mis à jour à la fin de la partie (positive/negative/neutral)
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]

        # Ajouter à la liste des mouvements en attente
        self.moves.append(move_entry)

        print(f"Recorded move: {player} from ({from_row},{from_col}) to ({to_row},{to_col}) with score {move_score}")

        # Sauvegarder automatiquement si nécessaire
        if self.auto_save and self.move_count % self.save_interval == 0:
            self.save_moves()

        return move_entry

    def save_moves(self):
        """
        Sauvegarde les mouvements en attente dans le fichier CSV.

        Cette méthode écrit les mouvements accumulés dans le fichier CSV
        et vide la liste temporaire une fois qu'ils sont sauvegardés.
        """
        if not self.moves:
            print("No moves to save")
            return

        try:
            with open(self.filename, 'a', newline='') as file:
                writer = csv.writer(file)
                for move in self.moves:
                    writer.writerow(move)

            print(f"Saved {len(self.moves)} moves to {self.filename}")

            # Vider la liste des mouvements après sauvegarde
            self.moves = []
        except Exception as e:
            print(f"Error saving moves: {e}")

    def _update_outcome_contributions(self, winner):
        """
        Met à jour la contribution de chaque mouvement au résultat final.

        Cette méthode est CRUCIALE pour l'apprentissage de l'IA. Elle marque
        chaque mouvement comme ayant contribué positivement ou négativement
        au résultat final, ce qui permet à l'IA d'apprendre quels mouvements
        ont tendance à mener à la victoire ou à la défaite.

        Args:
            winner (str): Couleur du gagnant (WHITE, BLACK, ou None pour match nul)
        """
        try:
            all_moves = []
            with open(self.filename, 'r', newline='') as file:
                reader = csv.reader(file)
                headers = next(reader)
                outcome_index = headers.index('outcome_contribution')
                player_index = headers.index('player')

                # Pour chaque mouvement, déterminer sa contribution
                for row in reader:
                    player = row[player_index]
                    if winner:
                        # Si le joueur est le gagnant, contribution positive
                        # Sinon, contribution négative
                        if player == winner:
                            row[outcome_index] = "positive"
                        else:
                            row[outcome_index] = "negative"
                    else:
                        # Si match nul, contribution neutre
                        row[outcome_index] = "neutral"

                    all_moves.append(row)

            # Réécrire le fichier avec les contributions mises à jour
            with open(self.filename, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(headers)
                writer.writerows(all_moves)

            print(f"Updated outcome contributions for game {self.game_id}")
        except Exception as e:
            print(f"Error updating outcome contributions: {e}")

    def end_game(self, winner):
        """
        Finalise la partie et enregistre son résultat.

        Cette méthode est appelée à la fin d'une partie pour :
        1. Sauvegarder les derniers mouvements
        2. Mettre à jour les contributions de chaque mouvement
        3. Enregistrer le résultat final dans l'historique global

        Args:
            winner (str): Couleur du gagnant (WHITE, BLACK, ou None pour match nul)

        Returns:
            str: Chemin du fichier de la partie enregistrée, ou None en cas d'erreur
        """
        # Sauvegarder les derniers mouvements
        self.save_moves()

        # Mettre à jour les contributions de chaque mouvement
        self._update_outcome_contributions(winner)

        # Fichier d'historique global des parties
        results_file = os.path.join(self.data_dir, "games_history.csv")

        file_exists = os.path.isfile(results_file)

        try:
            with open(results_file, 'a', newline='') as file:
                writer = csv.writer(file)

                # Créer l'en-tête si c'est un nouveau fichier
                if not file_exists:
                    writer.writerow([
                        'game_id',
                        'start_time',
                        'end_time',
                        'total_moves',
                        'winner'
                    ])

                # Enregistrer le résumé de cette partie
                writer.writerow([
                    self.game_id,
                    self.start_time,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    self.move_count,
                    winner if winner else "draw"
                ])

            print(f"Game {self.game_id} ended. Winner: {winner if winner else 'draw'}")
            print(f"Game result saved to {results_file}")

            return self.filename
        except Exception as e:
            print(f"Error saving game result: {e}")
            return None

    @staticmethod
    def load_game(filename):
        """
        Charge une partie enregistrée à partir de son fichier CSV.

        Cette méthode statique permet de charger et d'analyser
        les mouvements d'une partie précédemment enregistrée.

        Args:
            filename (str): Chemin vers le fichier CSV de la partie

        Returns:
            list: Liste des mouvements de la partie avec toutes leurs informations
        """
        moves = []
        try:
            with open(filename, 'r', newline='') as file:
                reader = csv.reader(file)
                next(reader)  # Ignorer l'en-tête

                # Parcourir chaque ligne (mouvement)
                for row in reader:
                    if len(row) >= 12:
                        # Convertir les données brutes en structure plus pratique
                        move_data = {
                            'game_id': row[0],
                            'move_number': int(row[1]),
                            'player': row[2],
                            'from_pos': (int(row[3]), int(row[4])),
                            'to_pos': (int(row[5]), int(row[6])),
                            'piece_type': row[7],
                            'captures': [(int(r), int(c)) for r, c in
                                        [pos.split(',') for pos in row[8].split(';')]] if row[8] else [],
                            'promotion': row[9].lower() == 'true',
                            'classification': row[10],
                            'move_score': float(row[11]) if row[11] and row[11] != 'pending' else 0,
                            'outcome_contribution': row[12] if len(row) > 12 else 'pending',
                            'timestamp': row[13] if len(row) > 13 else None
                        }
                        moves.append(move_data)
                    else:
                        print(f"Warning: Invalid row format: {row}")
            return moves
        except Exception as e:
            print(f"Error loading game: {e}")
            return []