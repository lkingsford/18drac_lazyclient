from itertools import chain
import json

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
                spot = Market.StockSpot(price, color, cell[0], row[0])
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
            if spot:
                assert spot.x == x and spot.y == y
        except IndexError:
            return None
        return spot

    def sold_share(self, company, amount):
        spot = self.get_company_spot(company)
        new_y = spot.y
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

    def get_hash(self):
        return hash(json.dumps(self.get_state()))

    def next_company(self):
        # Resolve highest price to lowest, then right to left, then top of stack to end
        all_spots = [i for i in chain.from_iterable(self.table) if i is not None and len([j for j in i.companies if not j.acted_this_or])]
        if len(all_spots) == 0:
            return None
        highest_spot = max(all_spots, key=lambda i: i.price + i.x / 100)
        return next(iter([i for i in highest_spot.companies if not i.acted_this_or]))

    def all_company_order(self, game):
        cos = [i for i in game.companies.values() if i.public and i.floated]
        cos.sort(key=lambda i: self.get_company_spot(i).price + \
             self.get_company_spot(i).x / 100 + \
            self.get_company_spot(i).y / 1000 + \
            (20 - self.get_company_spot(i).companies.index(i) / 10000), reverse=True)
        return cos
