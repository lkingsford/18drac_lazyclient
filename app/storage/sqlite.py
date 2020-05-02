import sqlite3
import json
from app.storage.storage import Storage

class Sqlite(Storage):
    def db(self):
        return sqlite3.connect(self.filename)

    def __init__(self, filename):
        self.filename = filename
        # Check if DB is brand new
        db = self.db()
        csr = db.cursor()
        csr.execute('SELECT count(*) FROM sqlite_master WHERE name="game"')
        result = csr.fetchone()[0]
        if result == 0:
            self.initialize_db()
    
    def initialize_db(self):
        create_tables_script = """
            CREATE TABLE game (state TEXT, last_update TEXT);
            """
        db = self.db()
        csr = db.cursor()
        csr.execute(create_tables_script)
        create_tables_script = """
            CREATE TABLE game_log (game_id INT NOT NULL, func_name TEXT, kwargs TEXT);
            """
        csr.execute(create_tables_script)
        db.commit()

    def save_game_state(self, game_id, game_state, timestamp):
        db = self.db()
        csr = db.cursor()
        if game_id:
            # Game exists, update
            csr.execute("""
                UPDATE game SET state=?, last_update=? WHERE rowid=?
                """, (game_state, timestamp, game_id))
        else:
            # Create new game
            csr.execute("""
                INSERT INTO game (state, last_update) VALUES (?, ?)
                """, (game_state, timestamp))
        db.commit()
        return csr.lastrowid

    def load_game_state(self, game_id):
        db = self.db()
        csr = db.cursor()
        csr.execute("""SELECT state, last_update FROM game WHERE rowid=?""", (game_id,))
        return csr.fetchone()[0]

    def get_games(self):
        db = self.db()
        csr = db.cursor()
        csr.execute("""SELECT rowid FROM game""")
        return [row[0] for row in csr.fetchall()]
    
    def log_action(self, game_id, func_name, kwargs):
        db = self.db()
        csr = db.cursor()
        csr.execute("""INSERT INTO game_log (game_id, func_name, kwargs) VALUES (?, ?, ?);""", (game_id, func_name, json.dumps(kwargs)))
        db.commit()