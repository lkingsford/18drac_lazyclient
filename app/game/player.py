class Player():
    def __init__(self, id = 0, name = None):
        self.id = id
        self.name = name
        self.cash = 0

    def get_state(self):
        return {'name': self.name,
                'cash': self.cash,
                'id': self.id}

    def load_state(self, state):
        self.name = state['name']
        self.cash = state['cash']
        self.id = int(state['id'])