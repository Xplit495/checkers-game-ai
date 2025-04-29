"""
Module contrôleur du jeu de dames

Ce module implémente la logique centrale du jeu de dames, gérant les règles du jeu,
la validation des mouvements, le suivi de l'état du jeu, ainsi que l'enregistrement
des parties pour l'apprentissage de l'IA.
"""

from game.board import Board
from game.constants import *
from data_management.game_recorder import GameRecorder

class GameController:
    """
    Contrôleur principal du jeu de dames.

    Cette classe joue le rôle central d'orchestrateur du jeu. Elle maintient l'état
    actuel du jeu, gère la logique des règles, valide les mouvements, et enregistre
    les actions des joueurs. C'est le lien entre l'interface utilisateur, le plateau
    de jeu, et le système d'enregistrement pour l'IA.
    """

    def __init__(self, create_recorder=True):
        """
        Initialise un nouveau contrôleur de jeu.

        Args:
            create_recorder (bool): Si True, crée un GameRecorder pour enregistrer
                                   la partie pour l'apprentissage de l'IA.
        """
        # Initialiser un nouveau plateau
        self.board = Board()

        # État initial du jeu
        self.current_player = WHITE  # Le joueur blanc commence toujours
        self.selected_piece = None   # Aucune pièce sélectionnée au début
        self.valid_moves = {}        # Aucun mouvement valide disponible
        self.captures_available = False  # Pas de captures disponibles initialement
        self.game_over = False       # La partie n'est pas terminée
        self.winner = None           # Pas de gagnant

        # Compteur de pièces pour chaque joueur
        self.piece_count = {
            WHITE: 20,  # 20 pièces blanches au début
            BLACK: 20   # 20 pièces noires au début
        }

        # Créer un enregistreur si demandé (crucial pour l'apprentissage de l'IA)
        if create_recorder:
            self.game_recorder = GameRecorder(auto_save=True, save_interval=3)
        else:
            self.game_recorder = None

    def reset(self):
        """
        Réinitialise le jeu à son état initial.

        Cette méthode termine la partie en cours (si existante), enregistre
        son résultat, et prépare un nouveau jeu.
        """
        # Finaliser la partie en cours si un enregistreur existe
        if hasattr(self, 'game_recorder') and self.game_recorder:
            if self.game_over:
                self.game_recorder.end_game(self.winner)
            else:
                self.game_recorder.end_game(None)  # Partie abandonnée (pas de gagnant)

        # Réinitialiser le plateau et tous les états du jeu
        self.board.reset()
        self.current_player = WHITE
        self.selected_piece = None
        self.valid_moves = {}
        self.captures_available = False
        self.game_over = False
        self.winner = None
        self.piece_count = {WHITE: 20, BLACK: 20}

        # Créer un nouvel enregistreur pour la nouvelle partie
        self.game_recorder = GameRecorder(auto_save=True, save_interval=3)

    def check_captures_available(self):
        """
        Vérifie si des captures sont possibles pour le joueur actuel.

        Dans le jeu de dames, si une capture est possible, le joueur doit l'effectuer.
        Cette méthode vérifie toutes les pièces du joueur actuel pour déterminer
        si au moins une capture est possible.

        Returns:
            bool: True si au moins une capture est possible, False sinon
        """
        # Vérifier chaque position du plateau
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board.get_piece(row, col)
                # Si c'est une pièce du joueur actuel
                if piece and piece.color == self.current_player:
                    # Vérifier si cette pièce peut capturer
                    captures = self.board._get_captures(row, col)
                    if captures:
                        return True
        return False

    def can_piece_capture(self, row, col):
        """
        Vérifie si une pièce spécifique peut effectuer une capture.

        Args:
            row (int): Ligne de la pièce
            col (int): Colonne de la pièce

        Returns:
            bool: True si la pièce peut capturer, False sinon
        """
        captures = self.board._get_captures(row, col)
        return bool(captures)

    def select(self, row, col):
        """
        Sélectionne une pièce et trouve ses mouvements valides.

        Cette méthode est appelée lorsqu'un joueur clique sur une case du plateau.
        Si une pièce du joueur actuel s'y trouve, elle est sélectionnée et
        ses mouvements valides sont calculés. Si une pièce est déjà sélectionnée,
        un nouveau clic sur la même pièce la désélectionne.

        Args:
            row (int): Ligne de la case sélectionnée
            col (int): Colonne de la case sélectionnée

        Returns:
            bool: True si une pièce a été sélectionnée avec succès, False sinon
        """
        # Si la pièce est déjà sélectionnée, la désélectionner
        if self.selected_piece == (row, col):
            self.selected_piece = None
            self.valid_moves = {}
            return False

        # Vérifier si des captures sont disponibles pour le joueur actuel
        self.captures_available = self.check_captures_available()

        # Obtenir la pièce à la position sélectionnée
        piece = self.board.get_piece(row, col)
        if piece and piece.color == self.current_player:
            # Si des captures sont disponibles, seules les pièces qui peuvent capturer sont sélectionnables
            if self.captures_available and not self.can_piece_capture(row, col):
                return False

            # Sélectionner la pièce et récupérer ses mouvements valides
            self.selected_piece = (row, col)
            self.valid_moves = self.board.get_valid_moves(row, col, self.current_player)
            return True

        return False

    def _classify_move(self, from_pos, to_pos, piece_type, captures, promotion):
        """
        Classifie un mouvement selon plusieurs critères.

        Cette classification est importante pour l'IA, qui utilisera ces informations
        pour analyser les types de mouvements et leur efficacité dans différentes
        situations.

        Args:
            from_pos (tuple): Position de départ (row, col)
            to_pos (tuple): Position d'arrivée (row, col)
            piece_type (str): Type de pièce (PION ou DAME)
            captures (list): Liste des pièces capturées
            promotion (bool): Si le mouvement a entraîné une promotion

        Returns:
            str: Classification du mouvement
        """
        move_count = self.game_recorder.move_count if hasattr(self, 'game_recorder') and self.game_recorder else 0
        total_pieces = self.piece_count[WHITE] + self.piece_count[BLACK]

        # Classification basée sur la phase de jeu
        if move_count < 8:
            classification = "opening"       # Ouverture (8 premiers coups)
        elif total_pieces < 15:
            classification = "end_game"      # Fin de partie (moins de 15 pièces)
        else:
            classification = "middle_game"   # Milieu de partie

        # Classification basée sur le type de mouvement (priorité aux captures et promotions)
        if captures:
            if len(captures) > 1:
                classification = "multiple_capture"  # Capture multiple
            else:
                classification = "capture"           # Capture simple

        if promotion:
            if captures:
                classification = "capture_promotion"  # Capture avec promotion
            else:
                classification = "promotion"          # Promotion simple

        # Classification spéciale pour les captures par une dame
        if piece_type == DAME:
            if "capture" in classification:
                classification = "king_" + classification  # Préfixe pour captures par dame

        return classification

    def _calculate_move_score(self, piece_type, captures, promotion, to_pos):
        """
        Calcule un score pour un mouvement donné.

        Ce score reflète la qualité stratégique du mouvement et sera enregistré
        pour être utilisé par l'IA lors de l'analyse des parties précédentes.

        Args:
            piece_type (str): Type de pièce (PION ou DAME)
            captures (list): Liste des pièces capturées
            promotion (bool): Si le mouvement a entraîné une promotion
            to_pos (tuple): Position d'arrivée (row, col)

        Returns:
            float: Score du mouvement
        """
        score = 0

        # Score de base selon le type de pièce
        base_score = 5 if piece_type == PION else 7  # Une dame vaut plus qu'un pion

        # Bonus pour les captures
        if captures:
            capture_score = len(captures) * 10  # 10 points par pièce capturée
            score += capture_score

        # Bonus pour les promotions
        if promotion:
            score += 15  # Promotion vaut 15 points

        # Bonus pour la proximité du centre (positions stratégiques)
        to_row, to_col = to_pos
        center_distance = abs(to_row - BOARD_SIZE//2) + abs(to_col - BOARD_SIZE//2)
        center_score = max(0, (BOARD_SIZE - center_distance) * 0.5)
        score += center_score

        # Bonus pour les dames positionnées sur les bords (plus difficiles à capturer)
        if piece_type == DAME:
            if to_row == 0 or to_row == BOARD_SIZE-1 or to_col == 0 or to_col == BOARD_SIZE-1:
                score += 5

        return base_score + score

    def move(self, row, col):
        """
        Effectue un mouvement vers la position spécifiée.

        Cette méthode centrale est appelée lorsqu'un joueur confirme un mouvement.
        Elle vérifie si le mouvement est valide, l'exécute, gère les captures et
        promotions, enregistre le mouvement, et vérifie si la partie est terminée.

        Args:
            row (int): Ligne de destination
            col (int): Colonne de destination

        Returns:
            bool: True si le mouvement a été effectué avec succès, False sinon
        """
        # Vérifier si une pièce est sélectionnée et si la destination est valide
        if self.selected_piece and (row, col) in self.valid_moves:
            from_row, from_col = self.selected_piece
            from_pos = (from_row, from_col)
            to_pos = (row, col)

            # Obtenir la pièce et son type
            piece = self.board.get_piece(from_row, from_col)
            piece_type = piece.type if piece else None

            # Récupérer les captures associées à ce mouvement
            captured = self.valid_moves[(row, col)]
            was_promoted = False

            # Effectuer les captures
            if captured:
                for capt_row, capt_col in captured:
                    self.board.remove_piece(capt_row, capt_col)
                    # Décrémenter le compteur de pièces pour le joueur adverse
                    self.piece_count[BLACK if self.current_player == WHITE else WHITE] -= 1

            # Déplacer la pièce
            self.board.move_piece(from_row, from_col, row, col)

            # Vérifier et effectuer la promotion si nécessaire
            piece = self.board.get_piece(row, col)
            if piece and piece.type == PION:
                if (piece.color == WHITE and row == 0) or (piece.color == BLACK and row == BOARD_SIZE-1):
                    piece.type = DAME
                    was_promoted = True

            # Enregistrer le mouvement si un enregistreur existe
            if hasattr(self, 'game_recorder') and self.game_recorder:
                # Classifier le mouvement
                move_classification = self._classify_move(from_pos, to_pos, piece_type, captured, was_promoted)

                # Calculer un score pour ce mouvement
                move_score = self._calculate_move_score(piece_type, captured, was_promoted, to_pos)

                # Enregistrer toutes les informations du mouvement
                self.game_recorder.record_move(
                    player=self.current_player,
                    from_pos=from_pos,
                    to_pos=to_pos,
                    piece_type=piece_type,
                    captures=captured,
                    promotion=was_promoted,
                    classification=move_classification,
                    move_score=move_score
                )

                # Sauvegarder les mouvements
                self.game_recorder.save_moves()

            # Réinitialiser la sélection
            self.selected_piece = None
            self.valid_moves = {}

            # Vérifier si la partie est terminée (un joueur n'a plus de pièces)
            if self.piece_count[BLACK] == 0:
                self.game_over = True
                self.winner = WHITE
                if hasattr(self, 'game_recorder') and self.game_recorder:
                    self.game_recorder.end_game(self.winner)
            elif self.piece_count[WHITE] == 0:
                self.game_over = True
                self.winner = BLACK
                if hasattr(self, 'game_recorder') and self.game_recorder:
                    self.game_recorder.end_game(self.winner)

            # Passer au joueur suivant
            self.current_player = BLACK if self.current_player == WHITE else WHITE

            return True

        return False

    def get_game_state(self):
        """
        Retourne l'état actuel du jeu sous forme de dictionnaire.

        Cette méthode est principalement utilisée par l'interface utilisateur
        pour afficher l'état du jeu et par l'IA pour analyser la situation.

        Returns:
            dict: État actuel du jeu avec toutes les informations pertinentes
        """
        return {
            'current_player': self.current_player,            # Joueur actuel (WHITE ou BLACK)
            'white_pieces': self.piece_count[WHITE],          # Nombre de pièces blanches
            'black_pieces': self.piece_count[BLACK],          # Nombre de pièces noires
            'board': self.board.to_dict(),                    # État du plateau
            'selected': self.selected_piece,                  # Pièce sélectionnée
            'valid_moves': list(self.valid_moves.keys()) if self.valid_moves else [],  # Mouvements valides
            'game_over': self.game_over,                      # Si la partie est terminée
            'winner': self.winner                             # Gagnant (si game_over est True)
        }