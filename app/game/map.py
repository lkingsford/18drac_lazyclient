def int_or_none(s):
    if s == "":
        return None
    else:
        return int(s)

class Map():
    class Destination:
        def __init__(self, game, id, display_name, dest_type, values, station_count):
            self.game = game
            self.upgrades = 0
            self.stations = []
            self.id = id
            self.display_name = display_name
            self.dest_type = dest_type
            self.values = values
            self.station_count = station_count

        def cur_station_count(self):
            cur_count = None
            idx = self.upgrades
            while cur_count is None:
                if idx < 0:
                    return 0
                cur_count = self.station_count[self.upgrades]
                idx -= 1
            return cur_count

        def can_pass_through(self, company):
            if self.dest_type in ['Export']:
                return False
            if company.id in self.stations:
                return True
            cur_station_count = self.cur_station_count()
            if cur_station_count == 0:
                return True
            occ_station_count = len([i for i in self.stations if self.game.companies[i].floated])
            return cur_station_count > occ_station_count

        def buy_office(self, company):
            assert company.tokens > 0
            assert company.cash >= company.token_cost()
            self.game.transfer_cash(company.token_cost(), None, company)
            company.tokens -= 1
            self.stations.append(company.id)
        
        def current_value(self):
            cur_val = None
            idx = self.game.phase if self.dest_type == 'Export' else self.upgrades
            while cur_val is None:
                if idx < 0:
                    return 0
                cur_val = self.values[self.upgrades]
                idx -= 1
            return cur_val

        def get_state(self):
            if len(self.stations) > 0 or \
                self.upgrades > 0:
                return {'stations': self.stations,
                        'upgrades': self.upgrades}
            else:
                return None

        def load_state(self, state):
            self.upgrades = int(state['upgrades'])
            self.stations = state['stations']

    class Route:
        def __init__(self, place_1, place_2, color, amount, cost):
            self.place_1 = place_1
            self.place_2 = place_2
            self.color = color
            self.amount = amount
            self.cost = cost
            self.cleared = 0
            self.id = f"{place_1}_{place_2}"

        def clear(self):
            assert self.cleared < self.amount
            self.cleared += 1

        def get_state(self):
            if self.cleared > 0:
                return {'cleared': self.cleared}
            else:
                return None

        def can_go_through(self):
            return self.amount == 0 or self.cleared == self.amount

        def load_state(self, state):
            self.cleared = int(state['cleared'])

    def __init__(self, game, destination_reader, route_reader, companies_list):
        self.game = game
        self.destinations = []
        self.routes = []
        self.load_map(destination_reader, route_reader, companies_list)

    def load_map(self, destinations, routes, companies):
        for row in destinations:
            _id = row[0]
            display_name = row[1]
            dest_type = row[2]
            values=[int_or_none(row[3]), int_or_none(row[4]), int_or_none(row[5]), int_or_none(row[6])]
            station_count=[int_or_none(row[7]), int_or_none(row[8]), int_or_none(row[9]), int_or_none(row[10])]
            reserved=int_or_none(row[11])
            destination = Map.Destination(self.game, _id, display_name, dest_type, values, station_count,)
            self.destinations.append(destination)
        for row in routes:
            place_1 = row[0]
            place_2 = row[1]
            color = row[2]
            amount = int_or_none(row[3]) or 0
            cost = int_or_none(row[4])
            route = Map.Route(place_1, place_2, color, amount, cost)
            self.routes.append(route)
        for company in companies:
            home_town_name = company[2]
            home = [i for i in self.destinations if i.id == home_town_name][0]
            home.stations.append(company[0])

    def _breadth_first_search(self, company, is_routes, store_condition):
        # Init queue with tokens
        queue = [i for i in self.destinations if company.id in i.stations]
        # Breadth first search
        visited = {i: False for i in self.destinations}
        for i in queue:
            visited[i] = True
        result = set()
        while queue:
            dest = queue.pop()
            routes = self.get_routes_from(dest)
            open_routes = [i for i in routes if i.cleared >= i.amount]
            if is_routes:
                result |= set([i for i in routes if store_condition(i)])
            else:
                if store_condition(dest):
                    result.add(dest)
            for route in open_routes:
                next_dest_id = route.place_1 if route.place_2 == dest.id else route.place_2
                next_dest = next(iter(i for i in self.destinations if i.id == next_dest_id))
                if next_dest.can_pass_through(company) and not visited[next_dest]:
                    queue.append(next_dest)
                    visited[next_dest] = True
        return result

    def get_clearing_routes(self, company):
        return self._breadth_first_search(company, True, \
            lambda i: self.game.can_clear(i.color) \
                        and i.cleared < i.amount \
                        and company.cash >= (i.cost or 0))

    def get_open_offices(self, company):
        return self._breadth_first_search(company, False, \
            lambda i: company.id not in i.stations \
                        and len(i.stations) < (i.station_count[i.upgrades] or 0))

    def get_routes_from(self, dest):
        return [i for i in self.routes if (i.place_1 == dest.id) or (i.place_2 == dest.id)]

    def get_route(self, a, b):
        return [i for i in self.routes if (i.place_1 == a.id and i.place_2 == b.id) or (i.place_2 == a.id and i.place_1 == b.id)]

    def clear_route(self, company, route):
        assert company.cash >= (route.cost or 0)
        assert self.game.can_clear(route.color)
        self.game.transfer_cash(route.cost or 0, None, company)
        self.game.cubes[route.color] += 1
        route.clear()

    def get_destination(self, dest):
        return next(iter([i for i in self.destinations if i.id == dest]))

    def get_state(self):
        return {"destinations": {i.id: i.get_state() for i in self.destinations if i.get_state()},
                "routes": {i[0]: i[1].get_state() for i in enumerate(self.routes) if i[1].get_state()}}

    def load_state(self, state):
        for dest_id, value in state['destinations'].items():
            dest = self.get_destination(dest_id)
            dest.load_state(value)
        for route_idx, value in state['routes'].items():
            route = self.routes[int(route_idx)]
            route.load_state(value)
