import csv
import os
import uuid
from datetime import datetime


class GameRecorder:
    def __init__(self, auto_save=True, save_interval=3):
        self.game_id = str(uuid.uuid4())[:8]
        self.moves = []
        self.move_count = 0
        self.start_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.auto_save = auto_save
        self.save_interval = save_interval

        self.data_dir = os.path.join("data", "games")
        os.makedirs(self.data_dir, exist_ok=True)

        self.filename = os.path.join(self.data_dir, f"game_{self.game_id}_{self.start_time}.csv")

        self._create_file()

        print(f"GameRecorder initialized. Recording to: {self.filename}")

    def _create_file(self):
        with open(self.filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                'game_id',
                'move_number',
                'player',
                'from_row',
                'from_col',
                'to_row',
                'to_col',
                'piece_type',
                'captures',
                'promotion',
                'classification',
                'move_score',
                'outcome_contribution',
                'timestamp'
            ])
        print(f"Created game record file: {self.filename}")

    def record_move(self, player, from_pos, to_pos, piece_type, captures=None, promotion=False, classification="normal", move_score=0):
        self.move_count += 1

        from_row, from_col = from_pos
        to_row, to_col = to_pos

        if classification == "normal":
            if self.move_count <= 8:
                classification = "opening"
            elif self.move_count > 30:
                classification = "end_game"
            else:
                classification = "middle_game"

            if captures:
                classification = "capture"
            elif promotion:
                classification = "promotion"

        captures_str = ""
        if captures:
            captures_str = ";".join([f"{row},{col}" for row, col in captures])

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
            "pending",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]

        self.moves.append(move_entry)

        print(f"Recorded move: {player} from ({from_row},{from_col}) to ({to_row},{to_col}) with score {move_score}")

        if self.auto_save and self.move_count % self.save_interval == 0:
            self.save_moves()

        return move_entry

    def save_moves(self):
        if not self.moves:
            print("No moves to save")
            return

        try:
            with open(self.filename, 'a', newline='') as file:
                writer = csv.writer(file)
                for move in self.moves:
                    writer.writerow(move)

            print(f"Saved {len(self.moves)} moves to {self.filename}")

            self.moves = []
        except Exception as e:
            print(f"Error saving moves: {e}")

    def _update_outcome_contributions(self, winner):
        try:
            all_moves = []
            with open(self.filename, 'r', newline='') as file:
                reader = csv.reader(file)
                headers = next(reader)
                outcome_index = headers.index('outcome_contribution')
                player_index = headers.index('player')

                for row in reader:
                    player = row[player_index]
                    if winner:
                        if player == winner:
                            row[outcome_index] = "positive"
                        else:
                            row[outcome_index] = "negative"
                    else:
                        row[outcome_index] = "neutral"

                    all_moves.append(row)

            with open(self.filename, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(headers)
                writer.writerows(all_moves)

            print(f"Updated outcome contributions for game {self.game_id}")
        except Exception as e:
            print(f"Error updating outcome contributions: {e}")

    def end_game(self, winner):
        self.save_moves()

        self._update_outcome_contributions(winner)

        results_file = os.path.join(self.data_dir, "games_history.csv")

        file_exists = os.path.isfile(results_file)

        try:
            with open(results_file, 'a', newline='') as file:
                writer = csv.writer(file)

                if not file_exists:
                    writer.writerow([
                        'game_id',
                        'start_time',
                        'end_time',
                        'total_moves',
                        'winner'
                    ])

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
        moves = []
        try:
            with open(filename, 'r', newline='') as file:
                reader = csv.reader(file)
                next(reader)

                for row in reader:
                    if len(row) >= 12:
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