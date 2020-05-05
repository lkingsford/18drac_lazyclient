class PrivateCompany:
    def __init__(self, id, name, base_cost, revenue, expires, description):
        self.id = id
        self.name = name
        self.base_cost = base_cost
        self.revenue = revenue
        self.description = description
        self.owner = None
        self.bids = []
        self.open = True
        self.closes_on = int(expires) if expires != "" else None

    def bid(self, bidder, bid):
        self.bids = [i for i in self.bids if i[0] != bidder]
        self.bids.append((bidder, bid))

    def get_state(self):
        return {
            'owner': self.owner.id if self.owner is not None else None,
            'bids': [(i[0].id, i[1]) for i in self.bids],
            'open': self.open,
        }

    def load_state(self, state, game):
        self.owner = game.players[state['owner']] if state['owner'] is not None else None
        self.bids = [(next(j for j in game.players if j.id == i[0]), i[1]) for i in state['bids']]
        self.open = state['open']

    def next_min_bid_amount(self, game):
        return self.bids[-1][1] + game.min_bid_increment if (len(self.bids) > 0) else self.base_cost + game.min_bid_increment
