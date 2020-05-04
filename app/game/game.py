import csv
import json
import random
from functools import reduce
from operator import concat
from itertools import chain
from enum import Enum
from . import testing_states
from .map import Map
from .company import Company
from .private_company import PrivateCompany
from .market import Market
from .player import Player
from .monster import Monster, SpecialRules as MonsterSpecialRules

def int_or_none(s):
    if s == "" or s == None:
        return None
    else:
        return int(s)

class Game:
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

    def __init__(self, load_state = None):
        with open("app/assets/Market.csv") as market_file:
            reader = csv.reader(market_file)
            self.market = Market(reader)
        with open("app/assets/Destinations.csv", encoding="utf8") as dest_file, \
             open("app/assets/Routes.csv") as route_file, \
             open("app/assets/Companies.csv") as companies_file:
            destination_reader = csv.reader(dest_file)
            route_reader = csv.reader(route_file)
            companies_list = [i for i in csv.reader(companies_file)]
            self.destinations = []
            self.routes = []
            self.players = []
            self.map = Map(self, destination_reader, route_reader, companies_list)
            self.load_companies(companies_list)
        with open("app/assets/Privates.csv") as privates_file:
            privates_reader = csv.reader(privates_file)
            self.load_privates(privates_reader)
        with open("app/assets/rules.json") as rules_file:
            rules = json.load(rules_file)
            self.starting_cash = rules['starting_cash']
            self.bank_size = rules['bank_size']
            self.min_bid_increment = rules['min_bid_increment']
            self.monster_limits = rules['monster_limits']
            self.monster_sales_for_phase = rules['monster_sales_for_phase']
            self.extra_phase_available = rules['extra_phase_available']
        with open("app/assets/monsters.csv", encoding="utf8") as monsters_file:
            monsters = csv.reader(monsters_file)
            self.monsters = []
            for monster in monsters:
                special_rules = [MonsterSpecialRules(i) for i in monster[7].split(',') if len(i) > 0]
                id = monster[0]
                name = monster[1]
                phase = int(monster[3])
                cost = int(monster[4])
                expires = int_or_none(monster[5])
                movement = int(monster[6])
                trade_cost = [(i.split(':')[0],i.split(':')[1]) for i in monster[8].split(',') if len(monster[8]) > 0]
                for i in range(int(monster[2])):
                    self.monsters.append(Monster(self, id, name, phase, cost, expires, movement, special_rules, trade_cost))
        self.turn_number = 0
        self.ors_this_turn = 0
        self.or_subnumber = 0
        self.or_co = None
        self.cubes = {'yellow':0, 'green':0, 'blue':0, 'red':0}
        self.phase_sales_remaining = 0
        self.rampage_editing_route_monster_idx = None
        self.rampage_current_routes_ids = []
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
        self.players = [Player(i, j) for i, j in enumerate(players)]
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
        self.turn_number = 0
        self.ors_this_turn = 0
        self.or_subnumber = 0
        self.or_co = None
        self.phase_sales_remaining = self.monster_sales_for_phase[0]

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

    def load_companies(self, companies):
        self.companies = {i[0]: Company(self, i[0], i[1], i[3], i[4]) for i in companies}

    def load_privates(self, privates):
        self.privates = [PrivateCompany(i[0], i[1], int(i[2]), int(i[3]), i[5]) for i in privates]

    def start_on(self):
        return {
            Game.GameTurnStatus.private_auction_buy_or_bid: 'associate',
            Game.GameTurnStatus.private_auction_bid: 'associate',
            Game.GameTurnStatus.first_stock_round: 'fronts',
            Game.GameTurnStatus.stock_round: 'fronts',
            Game.GameTurnStatus.operation_clear_track: 'map',
            Game.GameTurnStatus.operation_buy_office: 'map',
            Game.GameTurnStatus.operation_rampage: 'map',
            Game.GameTurnStatus.operation_buy_monsters: "monster",
            Game.GameTurnStatus.operation_force_sell_stock_round: 'fronts',
            Game.GameTurnStatus.bankruptcy: 'fronts'
        }[self.game_turn_status]

    def round_name(self):
        return {
            Game.GameTurnStatus.private_auction_buy_or_bid: 'AA',
            Game.GameTurnStatus.private_auction_bid: 'AA',
            Game.GameTurnStatus.first_stock_round: 'SR1',
            Game.GameTurnStatus.stock_round: f'SR{self.turn_number}',
            Game.GameTurnStatus.operation_clear_track: f'OR{self.turn_number}.{self.or_subnumber}/{self.ors_this_turn} - {self.or_co.display_name if self.or_co else ""} (Clear Track)',
            Game.GameTurnStatus.operation_buy_office: f'OR{self.turn_number}.{self.or_subnumber}/{self.ors_this_turn} - {self.or_co.display_name if self.or_co else ""} (Buy Office)',
            Game.GameTurnStatus.operation_rampage: f'OR{self.turn_number}.{self.or_subnumber}/{self.ors_this_turn} - {self.or_co.display_name if self.or_co else ""} (RAMPAGE!)',
            # todo: change once there's a monster screen
            Game.GameTurnStatus.operation_buy_monsters: f'OR{self.turn_number}.{self.or_subnumber}/{self.ors_this_turn} - {self.or_co.display_name if self.or_co else ""} (Buy monsters)',
            Game.GameTurnStatus.operation_force_sell_stock_round: f'OR{self.turn_number}.{self.or_subnumber}/{self.ors_this_turn} {self.or_co.display_name if self.or_co else ""} (Force sell)',
            Game.GameTurnStatus.bankruptcy: 'Game over'
        }[self.game_turn_status]

    def increment_phase(self):
        self.phase += 1
        self.phase_sales_remaining = self.monster_sales_for_phase[self.phase]

    def get_phase_ors(self):
        return {
            1: 1,
            2: 2,
            3: 2,
            4: 3,
            5: 3
        }[min(self.phase, 5)]

    def can_clear(self, color):
        return {
            1: color in ['yellow'],
            2: color in ['yellow', 'green'],
            3: color in ['yellow', 'green', 'red'],
            4: True,
        }[min(self.phase, 4)]

    def important_status(self):
        return {
            Game.GameTurnStatus.private_auction_buy_or_bid: '',
            Game.GameTurnStatus.private_auction_bid: '',
            Game.GameTurnStatus.first_stock_round: '',
            Game.GameTurnStatus.stock_round: '',
            Game.GameTurnStatus.operation_clear_track: '',
            Game.GameTurnStatus.operation_buy_office: f'{self.or_co.display_name} has {self.or_co.cash}pts of Blood Remaining' if self.or_co else '',
            Game.GameTurnStatus.operation_rampage: f'{self.or_co.display_name} has {self.or_co.cash}pts of Blood Remaining' if self.or_co else '',
            Game.GameTurnStatus.operation_buy_monsters: f'{self.or_co.display_name} has {self.or_co.cash}pts of Blood Remaining. Owns {len(self.or_co.monsters())}/{self.monster_limits[self.phase]} monsters.' if self.or_co else '',
            Game.GameTurnStatus.operation_force_sell_stock_round: '',
            Game.GameTurnStatus.bankruptcy: ''
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
        self.pa_next_buy_player = self.players[(self.pa_next_buy_player.id + 1) % len(self.players)]
        # Waterfall!
        self._pa_continue_waterfall()
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
        # This should maybe not be hard coded here
        self.priority = self.privates[0].owner
        # Start special privates
        ll = next(i for i in self.privates if i.id == 'll')
        self.companies['ll'].president = ll.owner
        self.companies['ll'].started = True
        self.companies['ll'].floated = True
        self.companies['ll'].cash = 30
        # Add nurses
        ll.open = False

        bt = next(i for i in self.privates if i.id == 'bt')
        self.companies['bt'].president = bt.owner
        self.companies['bt'].started = True
        self.companies['bt'].floated = True
        # Add monster
        bt.open = False

        self.increment_phase()
        self.sr_start()

# STOCK ROUNDS
    def sr_start(self):
        self.turn_number += 1
        self.game_turn_status = Game.GameTurnStatus.first_stock_round \
            if self.turn_number == 1 \
            else Game.GameTurnStatus.stock_round
        self.current_player = self.priority

    def sr_show_buy_president(self, co):
        if self.game_turn_status not in [Game.GameTurnStatus.first_stock_round,
                                         Game.GameTurnStatus.stock_round]:
            return False
        if self.sr_bought_this_turn:
            return False
        if co.started:
            return False
        if not co.public:
            return False
        if self.current_player.cash < (min(self.market.ipos()) * 2):
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
        if not co.public:
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
        if not co.public:
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
        if not co.public:
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

    def act_sr_pass(self):
        assert not self.sr_bought_this_turn, "Player has already bought a share this turn"
        assert not self.sr_sold_this_turn, "Player has already sold share[s] this turn"
        if self.priority == self.players[self.current_player.id - 1]:
            # End of SR
            self.sr_finish()
        else:
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
        self.ors_this_turn = self.get_phase_ors()
        self.or_subnumber = 0
        self.or_next_sub()

    def or_next_sub(self):
        # Next sub turn (or2.2 to or2.3)
        self.or_subnumber += 1
        if self.or_subnumber > self.ors_this_turn:
            self.sr_start()
            return
        for co in self.companies.values():
            co.acted_this_or = False
        self._or_pay_privates()
        self.or_next_co()

    def or_next_co(self):
        # Next company in this sub turn
        if not self.companies['ll'].acted_this_or:
            next_co = self.companies['ll']
        elif not self.companies['bt'].acted_this_or:
            next_co = self.companies['bt']
        else:
            next_co = self.market.next_company()
        if next_co:
            self.or_co = next_co
            self.current_player = self.or_co.president
            self.or_co.acted_this_or = True
            self.game_turn_status = Game.GameTurnStatus.operation_clear_track
        else:
            self.or_next_sub()

    def _or_pay_privates(self):
        for i in self.privates:
            if i.open:
                self.transfer_cash(i.revenue, i.owner)

    def act_or_pass(self):
        if self.game_turn_status == Game.GameTurnStatus.operation_clear_track:
            self.start_or_buy_office()
        elif self.game_turn_status == Game.GameTurnStatus.operation_buy_office:
            self.start_or_rampage()
        elif self.game_turn_status == Game.GameTurnStatus.operation_buy_monsters:
            self.or_next_co()

    def act_or_buy_office(self, dest_id):
        dest = self.map.get_destination(dest_id)
        dest.buy_office(self.or_co)
        self.start_or_rampage()

    def act_or_clear_route(self, route_id):
        route = next(iter([i for i in self.map.routes if i.id == route_id]))
        self.map.clear_route(self.or_co, route)
        self.start_or_buy_office()

    def start_or_buy_office(self):
        self.game_turn_status = Game.GameTurnStatus.operation_buy_office
        if len(self.map.get_open_offices(self.or_co)) == 0 or \
           self.or_co.stations_remaining == 0:
            self.start_or_rampage()

    def start_or_rampage(self):
        if len(self.or_co.monsters()) == 0:
            if self.or_co.public:
                self._or_withhold(0)
                return
            else:
                self.start_or_buy_monsters()
                return
        self.rampage_current_routes_ids = [[] for _ in self.or_co.monsters()]
        self.game_turn_status = Game.GameTurnStatus.operation_rampage

    def _or_withhold(self, amount):
        self.transfer_cash(amount, self.or_co)
        if self.or_co.public:
            self.market.withheld(self.or_co)
        self.start_or_buy_monsters()

    def _or_dividends(self, amount):
        amount_per_share = int(amount / 10)
        for payee in self.or_co.owners:
            self.transfer_cash(amount_per_share, payee)
        self.transfer_cash(amount_per_share * self.or_co.shares_in_market, self.or_co)
        if self.or_co.public:
            self.market.paid_out(self.or_co)
        self.start_or_buy_monsters()

    def act_or_rampage_edit_route(self, monster_idx):
        self.rampage_editing_route_monster_idx = monster_idx

    def act_or_rampage_clear_route(self, monster_idx):
        self.rampage_current_routes_ids[monster_idx] = []

    def act_or_rampage_add_to_route(self, dest_id):
        dest = self.map.get_destination(dest_id)
        self.rampage_current_routes_ids[self.rampage_editing_route_monster_idx].append(dest_id)

    def or_rampage_valid_next_node(self, destination):
        route = self.or_get_route_dests()
        if len(route) == 0:
            return True
        last = route[-1]
        if not last.can_pass_through(self.or_co) and len(route) > 1:
            return False
        r = [self.or_get_route_routes(i) for i in range(len(self.or_co.monsters()))]
        if (r):
            r1 = reduce(concat, r)
            if r1:
                used_routes = reduce(concat, r1)
            else:
                used_routes = []
        else:
            used_routes = []

        open_routes = [i for i in self.map.get_routes_from(last) \
                       if i.can_go_through() \
                           and i not in used_routes]
        all_conns = [i for i in chain([i.place_1 for i in open_routes], [i.place_2 for i in open_routes]) if i not in [j.id for j in route]]
        return destination.id in all_conns

    def or_get_route_dests(self):
        return [self.map.get_destination(i) for i in self.rampage_current_routes_ids[self.rampage_editing_route_monster_idx]]

    def or_get_route_routes(self, monster_idx):
        # TODO: Add spread
        dests = [self.map.get_destination(i) for i in self.rampage_current_routes_ids[monster_idx]]
        if len(dests) <= 1:
            return []
        routes = []
        last = dests.pop(0)
        while len(dests) > 0:
            next_dest = dests.pop(0)
            routes.append(self.map.get_route(last, next_dest))
            last = next_dest
        return routes

    def or_in_current_route(self, destination):
        return destination in self.or_get_route_dests()

    def or_validate_route(self, monster_idx):
        dests = [self.map.get_destination(i) for i in self.rampage_current_routes_ids[monster_idx]]
        payment = sum([i.current_value() for i in dests]) 
        if len(dests) == 0:
            return True, "No routes", payment
        if not any([self.or_co.id in i.stations for i in dests]):
            return False, "No token on route", payment
        # TODO: check for blocked
        # TODO: check for special rules
        # TODO: check for length
        # TODO: check for other routes using
        # TODO: check for amount of 1 size monsters on cities
        return True, "", payment
    
    def or_validate_all_routes(self):
        return all([self.or_validate_route(i)[0] for i in range(len(self.or_co.monsters()))])
    
    def or_all_routes_value(self):
        return sum([self.or_validate_route(i)[2] for i in range(len(self.or_co.monsters()))])
    
    def act_or_rampage_pay(self):
        self._or_dividends(self.or_all_routes_value())

    def act_or_rampage_withhold(self):
        self._or_withhold(self.or_all_routes_value())

    def _or_can_buy_any_monster(self):
        can_buy = [i[0] for i in self.or_available_monsters() if self.or_can_buy_monster(i[0])]
        if self.or_co.at_monster_limit() or \
           len(can_buy) == 0:
            return False
        return True

    def start_or_buy_monsters(self):
        self.game_turn_status = Game.GameTurnStatus.operation_buy_monsters
        if not self._or_can_buy_any_monster():
            self.or_next_co()

    def or_show_pass(self):
        return self.game_turn_status in [Game.GameTurnStatus.operation_clear_track,
                                         Game.GameTurnStatus.operation_buy_office,
                                         Game.GameTurnStatus.operation_buy_monsters]

    def or_available_monsters(self):
        phases_available = []
        if self.monster_sales_for_phase and self.phase_sales_remaining == 0:
            phases_available.append(self.phase + 1)
        else:
            phases_available.append(self.phase)
        if self.phase == self.extra_phase_available[self.phase]:
            phases_available.append(self.extra_phase_available[self.phase])
        all_relevant = [i for i in self.monsters if i.phase in phases_available and i.owner is None]
        unique_ids = {i.id for i in all_relevant}
        monsters = [(next(iter([i for i in all_relevant if i.id == _id])), len([i for i in all_relevant if i.id == _id])) for _id in unique_ids]
        return monsters

    def or_future_monsters(self):
        all_relevant = [i for i in self.monsters if i.phase > self.phase ]
        unique_ids = {i.id for i in all_relevant}
        monsters = [(next(iter([i for i in all_relevant if i.id == _id])), len([i for i in all_relevant if i.id == _id])) for _id in unique_ids]
        return monsters

    def or_can_buy_monster(self, monster):
        # todo: check monster limit
        if self.or_co.at_monster_limit():
            return False
        phases_available = []
        if self.monster_sales_for_phase and (self.phase_sales_remaining == 0):
            phases_available.append(self.phase + 1)
        else:
            phases_available.append(self.phase)
        if self.phase == self.extra_phase_available[self.phase]:
            phases_available.append(self.extra_phase_available[self.phase])
        return self.game_turn_status == GameTurnStatus.operation_buy_monsters and \
               (monster.phase in phases_available) and \
               (monster.owner == None) and \
               (self.or_co.cash >= monster.cost)

    def act_or_buy_monster(self, monster_id):
        monster = next(iter([i for i in self.monsters if i.id == monster_id and i.owner is None]))
        assert self.or_can_buy_monster(monster)
        assert monster
        monster.owner = self.or_co
        self.transfer_cash(monster.cost, None, self.or_co)
        self.phase_sales_remaining -= 1
        if self.monster_sales_for_phase[self.phase] > 0 and \
           self.phase_sales_remaining == -1:
            self.increment_phase()
        if not self._or_can_buy_any_monster():
            self.or_next_co()

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
            "turn_number": self.turn_number,
            "ors_this_turn": self.ors_this_turn,
            "or_subnumber": self.or_subnumber,
            "or_co": self.or_co.id if self.or_co is not None else None,
            "map": self.map.get_state(),
            "cubes": self.cubes,
            "monsters": {i[0]: i[1].get_state() for i in enumerate(self.monsters) if len(i[1].get_state()) > 0},
            "phase_sales_remaining": self.phase_sales_remaining,
            "rampage_editing_route_monster": self.rampage_editing_route_monster_idx,
            "rampage_current_routes_ids" : self.rampage_current_routes_ids,
        }
        return json.dumps(state)

    def load_state(self, state):
        state = json.loads(state)
        self.phase = state["phase"]
        self.game_turn_status = Game.GameTurnStatus(state["game_turn_status"])
        self.market.load_state(state["market"], self.companies)
        for player_state in state["players"]:
            player = Player()
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
        self.turn_number = state["turn_number"]
        self.ors_this_turn = state["ors_this_turn"]
        self.or_subnumber = state["or_subnumber"]
        self.or_co = self.companies[state["or_co"]] if state['or_co'] else None
        self.map.load_state(state["map"])
        self.cubes = state['cubes']
        for i, j in state['monsters'].items():
            self.monsters[int(i)].load_state(j)
        self.phase_sales_remaining = int_or_none(state['phase_sales_remaining'])
        self.rampage_editing_route_monster_idx = int_or_none(state['rampage_editing_route_monster'])
        self.rampage_current_routes_ids = state['rampage_current_routes_ids']

    def get_hash(self):
        return hash(self.get_state())

# For import
GameTurnStatus = Game.GameTurnStatus
