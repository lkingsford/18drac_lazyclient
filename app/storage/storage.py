class Storage:
    def save_game_state(self, game_id, game_state, timestamp):
        raise NotImplementedError()

    def load_game_state(self, game_id):
        raise NotImplementedError()