import csv
import json
import random
from enum import Enum
from itertools import chain
from . import testing_states

def int_or_none(s):
    if s == "":
        return None
    else:
        return int(s)

class Game:
    class GameRuleViolation(Exception):
        pass

    class GameTurnStatus(Enum):
        private_auction_buy_or_bid = 0
        private_auction_bid = 1
        first_stock_round = 2
        stock_round = 2
        operation_clear_track = 3
        operation_buy_office = 4
        operation_rampage = 5
        operation_buy_monsters = 6
        operation_force_sell_stock_round = 7
        bankruptcy = 8

    class Destination:
        def __init__(self):
            pass
        current_upgrades = 0

    class Route:
        def __init__(self):
            pass

    class PrivateCompany:
        def __init__(self, id, name, base_cost, revenue, description):
            self.id = id
            self.name = name
            self.base_cost = base_cost
            self.revenue = revenue
            self.description = description
            self.owner = None
            self.bids = []

        def bid(self, bidder, bid):
            self.bids = [i for i in self.bids if i[0] != bidder]
            self.bids.append((bidder, bid))

        def get_state(self):
            return {
                'owner': self.owner.id if self.owner is not None else None,
                'bids': [(i[0].id, i[1]) for i in self.bids],
            }

        def load_state(self, state, game):
            self.owner = game.players[state['owner']] if state['owner'] is not None else None
            self.bids = [(next(j for j in game.players if j.id == i[0]), i[1]) for i in state['bids']]

        def next_min_bid_amount(self, game):
            return self.bids[-1][1] + game.min_bid_increment if (len(self.bids) > 0) else self.base_cost + game.min_bid_increment

    class Company:
        def __init__(self, market, id, display_name, color):
            self.started = False
            self.floated = False
            self.cash = 0
            self.stations_remaining = 4
            self.display_name = display_name
            self.id = id
            self.color = color
            self.ipo = None
            self.market = market

        def start_new_company(self, ipo):
            if ipo not in self.market.ipos():
                raise Game.GameRuleViolation(f"IPO {ipo} not in market IPOs ({self.market.ipos})")
            self.ipo = ipo
            self.market.ipo_place(self, ipo)
            self.started = True

        def float(self):
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
                     }

        def load_state(self, state):
            self.started = state['started']
            self.floated = state['floated']
            self.cash = state['cash']
            self.stations_remaining = state['stations_remaining']
            self.ipo = state['ipo']

    class Market:
        class StockSpot:
            def __init__(self, price, color, x, y):
                self.price = price
                self.color = color
                self.ipo = False
                self.companies = []
                self.x = x
                self.y = y

        def __init__(self, reader):
            self.table = []
            for row in enumerate(reader):
                new_row = []
                for cell in enumerate(row[1]):
                    if cell[1] == "":
                        new_row.append(None)
                        continue
                    special = cell[1][0] in ['y', 'b', 'i']
                    price = int(cell[1][1:]) if special else int(cell[1])
                    color = cell[1][0] if special else 'w'
                    spot = Game.Market.StockSpot(price, color, cell[0], row[0])
                    spot.ipo = 'i' in cell[1][0]
                    new_row.append(spot)
                self.table.append(new_row)

        def ipos(self):
            return [i.price for i in chain.from_iterable(self.table) if i and i.ipo]

        def ipo_place(self, company, price):
            spot = [i for i in chain.from_iterable(self.table) if i and i.ipo and i.price == price][0]
            spot.companies.append(company)
            return spot

        def get_company_spot(self, company):
            spot = [i for i in chain.from_iterable(self.table) if i and company in i.companies][0]
            return spot

        def get_spot(self, x, y):
            spot = self.table[y][x]
            assert spot.x == x and spot.y == y
            return spot

        def get_state(self):
            occupied = [i for i in chain.from_iterable(self.table) if i and i.companies]
            return {f"{i.x},{i.y}": [j.id for j in i.companies] for i in occupied}

        def load_state(self, state, companies):
            for key, value in state.items():
                x, y = key.split(',')
                x = int(x)
                y = int(y)
                spot = self.get_spot(x, y)
                spot.companies = [companies[i] for i in value]

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

    def __init__(self, load_state = None):
        with open("app/assets/Market.csv") as market_file:
            reader = csv.reader(market_file)
            self.market = Game.Market(reader)
        with open("app/assets/Destinations.csv") as dest_file, \
             open("app/assets/Routes.csv") as route_file, \
             open("app/assets/Companies.csv") as companies_file:
            destination_reader = csv.reader(dest_file)
            route_reader = csv.reader(route_file)
            companies_list = [i for i in csv.reader(companies_file)]
            self.destinations = []
            self.routes = []
            self.players = []
            self.load_map(destination_reader, route_reader, companies_list)
            self.load_companies(companies_list)
        with open("app/assets/Privates.csv") as privates_file:
            privates_reader = csv.reader(privates_file)
            self.load_privates(privates_reader)
        with open("app/assets/rules.json") as rules_file:
            rules = json.load(rules_file)
            self.starting_cash = rules['starting_cash']
            self.bank_size = rules['bank_size']
            self.min_bid_increment = rules['min_bid_increment']
        if load_state:
            self.load_state(load_state)
        # Have to start game externally

    def start_game(self, players):
        if players[0] in testing_states.states:
            testing_states.states[players[0]](self)
            return

        self.phase = 0
        self.game_turn_status = Game.GameTurnStatus.private_auction_buy_or_bid
        # Randomize players
        random.shuffle(players)
        self.players = [Game.Player(i, j) for i, j in enumerate(players)]
        self.bank = self.bank_size
        # Deal starting cash
        starting_cash = int(self.starting_cash / len(self.players))
        for player in self.players:
            self.transfer_cash(starting_cash, player)
        self.current_player = self.players[0]
        self.pa_next_buy_player = self.players[0]
        self.pa_current_private = self.privates[0]

    def transfer_cash(self, quantity, to_party, from_party = None):
        # None = bank
        # transfer_cash(50, player) will transfer 50$ from bank to player
        if not to_party:
            self.bank += quantity
        else:
            to_party.cash += quantity
        if not from_party:
            self.bank -= quantity
        else:
            from_party.cash -= quantity

    def load_map(self, destinations, routes, companies):
        for row in destinations:
            destination = Game.Destination()
            destination.id = row[0]
            destination.display_name = row[1]
            destination.dest_type = row[2]
            destination.values=[int_or_none(row[3]), int_or_none(row[4]), int_or_none(row[5]), int_or_none(row[6])]
            destination.station_count=[int_or_none(row[7]), int_or_none(row[8]), int_or_none(row[9]), int_or_none(row[10])]
            destination.reserved=int_or_none(row[11])
            destination.upgrades = 0
            destination.stations=[]
            self.destinations.append(destination)
        for row in routes:
            route = Game.Route()
            route.place_1 = row[0]
            route.place_2 = row[1]
            route.color = row[2]
            route.amount = int_or_none(row[3]) or 0
            route.cost = int_or_none(row[4])
            self.routes.append(route)
        for company in companies:
            home_town_name = company[2]
            home = [i for i in self.destinations if i.id == home_town_name][0]
            home.stations.append(company[0])

    def load_companies(self, companies):
        self.companies = {i[0]: Game.Company(self.market, i[0], i[1], i[4]) for i in companies}

    def load_privates(self, privates):
        self.privates = [Game.PrivateCompany(i[0], i[1], int(i[2]), int(i[3]), i[5]) for i in privates]

    def start_on(self):
        return {
            Game.GameTurnStatus.private_auction_buy_or_bid: 'associate',
            Game.GameTurnStatus.private_auction_bid: 'associate',
            Game.GameTurnStatus.first_stock_round: 'fronts',
            Game.GameTurnStatus.stock_round: 'fronts',
            Game.GameTurnStatus.operation_clear_track: 'map',
            Game.GameTurnStatus.operation_buy_office: 'map',
            Game.GameTurnStatus.operation_rampage: 'map',
            # todo: change once there's a monster screen
            Game.GameTurnStatus.operation_buy_monsters: None,
            Game.GameTurnStatus.operation_force_sell_stock_round: 'fronts',
            Game.GameTurnStatus.bankruptcy: 'fronts'
        }[self.game_turn_status]

# PRIVATE AUCTION
    def pa_get_uncommitted_cash(self, player_id):
        return self.players[player_id].cash

    def pa_can_pass(self, company):
        # Cheapest unpurchased company
        if self.game_turn_status.value not in [0, 1]:
            return False
        return company == self.pa_current_private

    def pa_can_buy(self, company):
        if self.game_turn_status.value not in [0]:
            return False
        return company == self.pa_current_private

    def pa_can_bid(self, company):
        if self.game_turn_status.value not in [0, 1]:
            return False

        if company.owner is not None:
            return False

        if self.game_turn_status.value == 1:
            for i in self.privates:
                if i.id == company.id:
                    return True
                if i.owner is None:
                    return False

        return not self.pa_can_pass(company)

    def act_pa_pass(self):
        if self.game_turn_status.value == 0:
            self.pa_next_buy_player = self.players[(self.pa_next_buy_player.id + 1) % len(self.players)]
            self.current_player = self.pa_next_buy_player
        elif self.game_turn_status.value == 1:
            self.pa_current_private.bids = [i for i in self.pa_current_private.bids if i[0] != self.current_player]
            if len(self.pa_current_private.bids) == 1:
                bid = self.pa_current_private.bids[-1]
                self.transfer_cash(bid[1], None, bid[0])
                self.pa_current_private.owner = bid[0]
                self._pa_continue_waterfall()
            else:
                self._pa_set_next_bidder()

    def act_pa_bid(self, bid, private_id):
        private = next(i for i in self.privates if i.id == private_id)
        assert bid >= private.next_min_bid_amount(self), "Bid too low"
        if self.game_turn_status.value == 0:
            private.bid(self.current_player, bid)
            self.pa_next_buy_player = self.players[(self.pa_next_buy_player.id + 1) % len(self.players)]
            self.current_player = self.pa_next_buy_player
        elif self.game_turn_status.value == 1:
            private.bid(self.current_player, bid)
            self._pa_set_next_bidder()

    def act_pa_buy(self):
        self.transfer_cash(self.pa_current_private.base_cost, None, self.current_player)
        self.pa_current_private.owner = self.current_player
        # Waterfall!
        self._pa_continue_waterfall()
        self.pa_next_buy_player = self.players[(self.pa_next_buy_player.id + 1) % len(self.players)]
        if self.game_turn_status == 0:
            self.current_player = self.pa_next_buy_player

    def _pa_continue_waterfall(self):
        while self.pa_current_private.owner is not None:
            unowned = [i for i in self.privates if i.owner is None]
            if len(unowned) == 0:
                self._pa_finish()
                return
            self.pa_current_private = unowned[0]
            if len(self.pa_current_private.bids) == 1:
                self.transfer_cash(self.pa_current_private.bids[0][1], None, self.pa_current_private.bids[0][0])
                self.pa_current_private.owner = self.pa_current_private.bids[0][0]
            elif len(self.pa_current_private.bids) > 1:
                self._pa_set_next_bidder()
                return
            else:
                self.game_turn_status = Game.GameTurnStatus.private_auction_buy_or_bid
                self.current_player = self.pa_next_buy_player

    def _pa_set_next_bidder(self):
        high_bidder = self.pa_current_private.bids[-1][0]
        bidders = [i[0] for i in self.pa_current_private.bids if i[0] != high_bidder]
        check_bidder = high_bidder
        assert len(bidders) > 0
        while check_bidder not in bidders:
            check_bidder = self.players[(check_bidder.id + 1) % len(self.players)]
        self.current_player = check_bidder
        self.game_turn_status = Game.GameTurnStatus.private_auction_bid

    def _pa_finish(self):
        self.game_turn_status = Game.GameTurnStatus.first_stock_round
        # This should maybe not be hard coded here
        self.current_player = self.privates[0].owner

# Stock phase

    def get_state(self):
        state = {
            "phase": self.phase,
            "game_turn_status": self.game_turn_status.value,
            "market": self.market.get_state(),
            "companies": {company.id: company.get_state() for company in self.companies.values()},
            "players": [player.get_state() for player in self.players],
            "bank": self.bank,
            "current_player": self.current_player.id,
            "privates": [private.get_state() for private in self.privates],
            "pa_current_private": self.pa_current_private.id,
            "pa_next_buy_player": self.pa_next_buy_player.id,
        }
        return json.dumps(state)

    def load_state(self, state):
        state = json.loads(state)
        self.phase = state["phase"]
        self.game_turn_status = Game.GameTurnStatus(state["game_turn_status"])
        self.market.load_state(state["market"], self.companies)
        for id, co_state in state["companies"].items():
            self.companies[id].load_state(co_state)
        for player_state in state["players"]:
            player = Game.Player()
            player.load_state(player_state)
            self.players.append(player)
        self.bank = state["bank"]
        self.current_player = self.players[state["current_player"]]
        self.pa_next_buy_player = self.players[state["pa_next_buy_player"]]
        for id, pr_state in enumerate(state["privates"]):
            self.privates[id].load_state(pr_state, self)
        self.pa_current_private = next(i for i in self.privates if i.id == state["pa_current_private"])