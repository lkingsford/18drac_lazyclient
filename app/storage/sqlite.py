import sqlite3
from app.storage.storage import Storage

class Sqlite(Storage):
    def __init__(self, filename):
        self.db = sqlite3.connect(filename)
        # Check if DB is brand new
        csr = self.db.cursor()
        csr.execute('SELECT count(*) FROM sqlite_master WHERE name="game"')
        result = csr.fetchone()[0]
        if result == 0:
            self.initialize_db()
    
    def initialize_db(self):
        create_tables_script = """
            CREATE TABLE game (state TEXT, last_update TEXT);
            """
        csr = self.db.cursor()
        csr.execute(create_tables_script)
        self.db.commit()

    def save_game_state(self, game_id, game_state, timestamp):
        csr = self.db.cursor()
        if game_id:
            # Game exists, update
            csr.execute("""
                UPDATE game SET (state=?, last_update=?) WHERE (rowid=?)
                """, (game_state, timestamp, game_id))
        else:
            # Create new game
            csr.execute("""
                INSERT INTO game (state, last_update) VALUES (?, ?)
                """, (timestamp, game_id))
        self.db.commit()
        return csr.lastrowid

    def load_game_state(self, game_id):
        csr = self.db.cursor()
        csr.execute("""SELECT state, last_update FROM game WHERE rowid=?""", (game_id,))
        return csr.fetchone()[0]
