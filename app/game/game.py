import csv

def int_or_none(s):
    if s == "":
        return None
    else:
        return int(s)

class Game:
    class Destination:
        def __init__(self):
            pass
        current_upgrades = 0
    class Route:
        def __init__(self):
            pass
    
    def __init__(self):
        with open("app/assets/Destinations.csv") as dest_file, open("app/assets/Routes.csv") as route_file:
            destination_reader = csv.reader(dest_file)
            route_reader = csv.reader(route_file)
            self.destinations = []
            self.routes = []
            self.phase = 0
            self.load_map(destination_reader, route_reader)
    
    def load_map(self, destinations, routes):
        for row in destinations:
            destination = Game.Destination()
            destination.id = row[0]
            destination.display_name = row[1]
            destination.dest_type = row[2]
            destination.values=[int_or_none(row[3]), int_or_none(row[4]), int_or_none(row[5]), int_or_none(row[6])]
            destination.stations=[int_or_none(row[7]), int_or_none(row[8]), int_or_none(row[9]), int_or_none(row[10])]
            destination.reserved=int_or_none(row[11])
            destination.upgrades = 0
            self.destinations.append(destination)
        for row in routes:
            route = Game.Route()
            route.place_1 = row[0]
            route.place_2 = row[1]
            route.color = row[2]
            route.amount = int_or_none(row[3]) or 0
            route.cost = int_or_none(row[4])
            self.routes.append(route)
