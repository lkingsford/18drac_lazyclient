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
        stock_round = 3
        operation_clear_track = 4
        operation_buy_office = 5
        operation_rampage = 6
        operation_buy_monsters = 7
        operation_force_sell_stock_round = 8
        bankruptcy = 9

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
        def __init__(self, game, id, display_name, color):
            self.started = False
            self.floated = False
            self.cash = 0
            self.stations_remaining = 4
            self.display_name = display_name
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

        def start_new_company(self, ipo, player):
            if ipo not in self.market.ipos():
                raise Game.GameRuleViolation(f"IPO {ipo} not in market IPOs ({self.market.ipos})")
            self.ipo = ipo
            self.market.ipo_place(self, ipo)
            self.started = True
            self.shares_in_ipo = 10
            self.president = player
            self.buy_share_ipo(player)
            self.buy_share_ipo(player)

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
                    'owners': [i.id for i in self.owners],
                    'sr_sellers': [i.id for i in self.sr_sellers],
                    'president': self.president.id if self.president is not None else None,
                    'shares_in_ipo': self.shares_in_ipo,
                    'shares_in_market': self.shares_in_market,
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

        def buy_share_ipo(self, player):
            assert self.shares_in_ipo > 0, "Not enough shares in ipo"
            assert player.cash > self.ipo
            assert player not in self.sr_sellers, f"{player.name} already sold this SR"
            # Todo: check share limit
            self.shares_in_ipo -= 1
            self.owners.append(player)
            self.game.transfer_cash(self.ipo, None, player)
            self.adjust_president()

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
            if (x < 0) or (y < 0):
                return None
            try:
                spot = self.table[y][x]
            except IndexError:
                return None
            assert spot.x == x and spot.y == y
            return spot

        def sold_share(self, company, amount):
            spot = self.get_company_spot(company)
            for i in range(amount):
                new_y += 1
                potential_spot = self.get_spot(spot.x, new_y)
                if potential_spot is not None:
                    spot.companies.remove(company)
                    spot = potential_spot
                    spot.companies.append(company)

        def all_sold(self, company):
            spot = self.get_company_spot(company)
            potential_spot = self.get_spot(spot.x, spot.y - 1)
            if potential_spot is not None:
                spot.companies.remove(company)
                potential_spot.companies.append(company)

        def paid_out(self, company):
            spot = self.get_company_spot(company)
            potential_spot = self.get_spot(spot.x + 1, spot.y)
            if not potential_spot:
                potential_spot = self.get_spot(spot.x, spot.y - 1)
            if not potential_spot:
                return
            spot.companies.remove(company)
            potential_spot.companies.append(company)

        def withheld(self, company):
            spot = self.get_company_spot(company)
            potential_spot = self.get_spot(spot.x - 1, spot.y)
            if not potential_spot:
                potential_spot = self.get_spot(spot.x, spot.y + 1)
            if not potential_spot:
                return
            # TODO: Bankrupt?
            spot.companies.remove(company)
            potential_spot.companies.append(company)

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

        self.sr_sold_this_turn = False
        self.sr_bought_this_turn = False
        self.priority = self.players[0]

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
        self.companies = {i[0]: Game.Company(self, i[0], i[1], i[4]) for i in companies}

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
        return self.players[player_id].cash - sum([sum([i[1] for i in j.bids if i[0].id == player_id]) for j in self.privates])

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
        self.priority = self.current_player
        self.sr_start = True

# STOCK ROUNDS
    def sr_show_buy_president(self, co):
        if self.game_turn_status not in [Game.GameTurnStatus.first_stock_round,
                                         Game.GameTurnStatus.stock_round]:
            return False
        if self.sr_bought_this_turn:
            return False
        if co.started:
            return False
        if self.current_player.cash < min(self.market.ipos()):
            return False
        return True

    def sr_show_buy_ipo(self, co):
        if self.game_turn_status not in [Game.GameTurnStatus.first_stock_round,
                                         Game.GameTurnStatus.stock_round]:
            return False
        if self.sr_bought_this_turn:
            return False
        if co.shares_in_ipo == 0:
            return False
        if self.current_player.cash < co.ipo:
            return False
        if self.current_player in co.sr_sellers:
            return False
        return True

    def sr_show_buy_market(self, co):
        if self.game_turn_status not in [Game.GameTurnStatus.first_stock_round,
                                         Game.GameTurnStatus.stock_round]:
            return False
        if self.sr_bought_this_turn:
            return False
        if co.shares_in_market == 0:
            return False
        if self.current_player.cash < co.current_price():
            return False
        if self.current_player in co.sr_sellers:
            return False
        return True

    def sr_show_sell(self, co):
        if self.game_turn_status not in [Game.GameTurnStatus.stock_round,
                                         Game.GameTurnStatus.operation_force_sell_stock_round]:
            return False
        if co.shares_in_market >= 5:
            return False
        if len([i for i in co.owners if i == self.current_player]) == 0:
            return False
        if co.president == self.current_player and co.no_next_president():
            return False
        return True

    def sr_show_pass(self):
        if self.game_turn_status not in [Game.GameTurnStatus.first_stock_round, Game.GameTurnStatus.stock_round]:
            return False
        return not (self.sr_sold_this_turn or self.sr_bought_this_turn)

    def sr_show_done(self):
        if self.game_turn_status not in [Game.GameTurnStatus.first_stock_round, Game.GameTurnStatus.stock_round]:
            return False
        return self.sr_sold_this_turn or self.sr_bought_this_turn

    def act_sr_done(self):
        self.priority = self.players[self.current_player.id - 1]
        self.current_player = self.players[(self.current_player.id + 1) % len(self.players)]
        self.sr_bought_this_turn = False
        self.sr_sold_this_turn = False
        if self.sr_start:
            self.sr_start = False

    def act_sr_pass(self):
        assert not self.sr_bought_this_turn, "Player has already bought a share this turn"
        assert not self.sr_sold_this_turn, "Player has already sold share[s] this turn"
        if not self.sr_start and (self.priority == self.current_player):
            # End of SR
            self.sr_finish()
        if self.sr_start:
            self.sr_start = False
        self.current_player = self.players[(self.current_player.id + 1) % len(self.players)]

    def act_sr_buy_president(self, company_id, ipo_price):
        assert not self.sr_bought_this_turn, "Player has already bought a share this turn"
        co = self.companies[company_id]
        co.start_new_company(ipo_price, self.current_player)
        self.sr_bought_this_turn = True
        if self.game_turn_status == Game.GameTurnStatus.first_stock_round:
            self.act_sr_done()

    def act_sr_buy_ipo(self, company_id):
        assert not self.sr_bought_this_turn, "Player has already bought a share this turn"
        co = self.companies[company_id]
        co.buy_share_ipo(self.current_player)
        self.sr_bought_this_turn = True
        if self.game_turn_status == Game.GameTurnStatus.first_stock_round:
            self.act_sr_done()

    def act_sr_buy_market(self, company_id):
        assert not self.sr_bought_this_turn, "Player has already bought a share this turn"
        co = self.companies[company_id]
        co.buy_share_market(self.current_player)
        self.sr_bought_this_turn = True

    def act_sr_sell(self, company_id, qty):
        co = self.companies[company_id]
        co.sell_share_market(self.current_player, qty)
        self.sr_sold_this_turn = True

    def sr_finish(self):
        for c in self.companies.values():
            c.adjust_at_end_of_sr()
        self.or_start()

# OR
    def or_start(self):
        self.game_turn_status = Game.GameTurnStatus.stock_round
        self.current_player = self.priority
        self.sr_start = True

# State

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
            "priority": self.priority.id,
            "sr_sold_this_turn": self.sr_sold_this_turn,
            "sr_bought_this_turn": self.sr_bought_this_turn,
            "sr_start": self.sr_start,
        }
        return json.dumps(state)

    def load_state(self, state):
        state = json.loads(state)
        self.phase = state["phase"]
        self.game_turn_status = Game.GameTurnStatus(state["game_turn_status"])
        self.market.load_state(state["market"], self.companies)
        for player_state in state["players"]:
            player = Game.Player()
            player.load_state(player_state)
            self.players.append(player)
        for id, co_state in state["companies"].items():
            self.companies[id].load_state(co_state)
        self.bank = state["bank"]
        self.current_player = self.players[state["current_player"]]
        self.pa_next_buy_player = self.players[state["pa_next_buy_player"]]
        for id, pr_state in enumerate(state["privates"]):
            self.privates[id].load_state(pr_state, self)
        self.pa_current_private = next(i for i in self.privates if i.id == state["pa_current_private"])
        self.priority = self.players[state["priority"]]
        self.sr_sold_this_turn = state["sr_sold_this_turn"]
        self.sr_bought_this_turn = state["sr_bought_this_turn"]
        self.sr_start = state["sr_start"]