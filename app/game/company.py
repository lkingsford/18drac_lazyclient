class Company:
    def __init__(self, game, id, name, private, color):
        self.started = False
        self.floated = False
        self.cash = 0
        self.stations_remaining = 4
        self.name = name
        self.id = id
        self.color = color
        self.ipo = None
        self.market = game.market
        self.game = game
        self.owners = []
        self.president = None
        self.shares_in_ipo = 0
        self.shares_in_market = 0
        self.sr_sellers = []
        self.acted_this_or = False
        self.public = private == "public"
        self.tokens = 3

    def start_new_company(self, ipo, player):
        assert ipo in self.market.ipos(), f"IPO {ipo} not in market IPOs ({self.market.ipos})"
        self.ipo = ipo
        self.market.ipo_place(self, ipo)
        self.started = True
        self.shares_in_ipo = 10
        self.president = player
        self.buy_share_ipo(player)
        self.buy_share_ipo(player)

    def float_co(self):
        self.cash = 10 * self.ipo
        self.floated = True

    def current_price(self):
        return self.market.get_company_spot(self).price

    def get_state(self):
        return {'started': self.started,
                'floated': self.floated,
                'cash': self.cash,
                'stations_remaining': self.stations_remaining,
                'ipo': self.ipo,
                'owners': [i.id for i in self.owners],
                'sr_sellers': [i.id for i in self.sr_sellers],
                'president': self.president.id if self.president is not None else None,
                'shares_in_ipo': self.shares_in_ipo,
                'shares_in_market': self.shares_in_market,
                'tokens': self.tokens,
                'acted_this_or': self.acted_this_or,
                    }

    def load_state(self, state):
        self.started = state['started']
        self.floated = state['floated']
        self.cash = int(state['cash'])
        self.stations_remaining = int(state['stations_remaining'])
        self.ipo = int(state['ipo']) if state['ipo'] is not None else None
        self.owners = [self.game.players[i] for i in state['owners']]
        self.sr_sellers = [self.game.players[i] for i in state['sr_sellers']]
        self.president = self.game.players[state['president']] if state['president'] is not None else None
        self.shares_in_ipo = int(state['shares_in_ipo'])
        self.shares_in_market = int(state['shares_in_market'])
        self.acted_this_or = int(state['acted_this_or'])
        self.tokens = int(state['tokens'])

    def buy_share_ipo(self, player):
        assert self.shares_in_ipo > 0, "Not enough shares in ipo"
        assert player.cash > self.ipo
        assert player not in self.sr_sellers, f"{player.name} already sold this SR"
        # Todo: check share limit
        self.shares_in_ipo -= 1
        self.owners.append(player)
        self.game.transfer_cash(self.ipo, None, player)
        self.adjust_president()
        if not self.floated and self.shares_in_ipo <= 4:
            self.float_co()

    def buy_share_market(self, player):
        assert self.shares_in_market > 0, "Not enough shares in market"
        assert player not in self.sr_sellers, f"{player.name} already sold this SR"
        market_spot = self.market.get_company_spot(self)
        assert player.cash > market_spot.price
        # Todo: check share limit
        self.shares_in_market -= 1
        self.owners.append(player)
        self.game.transfer_cash(market_spot.price, None, player)
        self.adjust_president()

    def sell_share_market(self, player, amount):
        # Todo: check market share limit
        assert amount in self.player_can_sell(player), f"Player can sell {self.player_can_sell(player)} shares"

        self.shares_in_market += amount
        market_spot = self.market.get_company_spot(self)
        self.game.transfer_cash(market_spot.price * amount, player)
        self.sr_sellers.append(player)
        for i in range(amount):
            self.owners.remove(player)
        self.market.sold_share(self, amount)
        self.adjust_president()

    def adjust_president(self):
        counts = [(i, len([j for j in self.owners if j == i])) for i in self.game.players]
        max_owned = max([i[1] for i in counts])
        counts = [(i[0], i[1]) for i in counts if i[1] >= max_owned]
        if len(counts) > 0:
            candidate = self.game.players[(self.president.id) % len(self.game.players)]
            while candidate not in [i[0] for i in counts]:
                candidate = self.game.players[(candidate.id + 1) % len(self.game.players)]
            self.president = candidate

    def adjust_at_end_of_sr(self):
        if self.started and \
            self.public and \
            self.shares_in_market == 0 and \
            self.shares_in_ipo == 0:
            self.market.all_sold(self)
        self.sr_sellers = []

    def no_next_president(self):
        counts = [(i, len([j for j in self.owners if j == i])) for i in self.game.players]
        counts = [(i[0], i[1]) for i in counts if i[1] >= 2]
        return len(counts) == 1

    def player_can_sell(self, player):
        player_owns = len([i for i in self.owners if i == player])
        if (self.president == player) and (self.no_next_president()):
            player_owns -= 2
        if player_owns <= 0:
            return []
        max_sell = min((5 - self.shares_in_market), player_owns)
        return list(range(1, max_sell + 1))

    def players_holdings(self):
        counts = [(i, len([j for j in self.owners if j == i])) for i in self.game.players]
        counts = [(i[0], i[1]) for i in counts if i[1] > 0]
        return counts

    def token_cost(self):
        return {0: None, 1: 100, 2: 100, 3: 40}[self.tokens]

    def monster_display(self):
        def monster_name(i):
            exp_str = f"(Eaten Phase {i.expires})" if i.expires else ""
            return i.name + exp_str

        holdings = [monster_name(i) for i in self.monsters()]
        if not holdings:
            return "None"
        else:
            return ", ".join(holdings)

    def monsters(self):
        return [i for i in self.game.monsters if i.owner == self] 

    def grouped_monsters(self):
        monsters = self.monsters()
        unique_ids = {i.id for i in monsters}
        return [(next(iter([i for i in monsters if i.id == _id])), len([i for i in monsters if i.id == _id])) for _id in unique_ids]

    def at_monster_limit(self):
        return self.monster_limit_count() >= self.game.monster_limits[self.game.phase]
    
    def monster_limit_count(self):
        return len(self.monsters())
    
    def monster_count(self):
        return len(self.monsters())