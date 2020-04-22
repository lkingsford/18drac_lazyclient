import csv
import json
from enum import Enum

def int_or_none(s):
    if s == "":
        return None
    else:
        return int(s)

class Game:
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

    class Company:
        def __init__(self, id, display_name):
            self.started = False

    class Market:
        class StockSpot:
            def __init__(self, price, color):
                self.price = price
                self.color = color

        def __init__(self, reader):
            self.table = []
            for row in reader:
                new_row = []
                for cell in row:
                    if cell == "":
                        new_row.append(None)
                        continue
                    special = cell[0] in ['y', 'b', 'i']
                    price = int(cell[1:]) if special else int(cell) 
                    color = cell[0] if special else 'w'
                    spot = Game.Market.StockSpot(price, color)
                    new_row.append(spot)
                self.table.append(new_row)

    def __init__(self, load_state = None):
        with open("app/assets/Destinations.csv") as dest_file, \
             open("app/assets/Routes.csv") as route_file, \
             open("app/assets/Companies.csv") as companies_file:
            destination_reader = csv.reader(dest_file)
            route_reader = csv.reader(route_file)
            companies_list = [i for i in csv.reader(companies_file)]
            self.destinations = []
            self.routes = []
            self.load_map(destination_reader, route_reader, companies_list)
            self.load_companies(companies_list)
        with open("app/assets/Market.csv") as market_file:
            reader = csv.reader(market_file)
            self.market = Game.Market(reader)
        if load_state:
            self.load_state(load_state)
        else:
            self.start_game()

    def start_game(self):
        self.phase = 0
        self.game_turn_status = Game.GameTurnStatus.first_stock_round

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
        self.companies = [Game.Company(i[0], i[1]) for i in companies]
    
    def get_state(self):
        state = {
            "phase": self.phase,
            "game_turn_status": str(self.game_turn_status),
        }
        return json.dumps(state)

    def load_state(self, state):
        state = json.loads(state)
        self.phase = state["phase"]
        self.game_turn_status = state["game_turn_status"]
