import csv
import graphviz

class Destination:
    def __init__(self):
        pass

class Route:
    def __init__(self):
        pass

destinations = []

def int_or_none(s):
    if s == "":
        return None
    else:
        return int(s)

with open('Destinations.csv') as csv_file:
    reader = csv.reader(csv_file)
    for row in reader:
        destination = Destination()
        destination.id = row[0]
        destination.display_name = row[1]
        destination.dest_type = row[2]
        destination.values=[int_or_none(row[3]), int_or_none(row[4]), int_or_none(row[5]), int_or_none(row[6])]
        destination.stations=[int_or_none(row[7]), int_or_none(row[8]), int_or_none(row[9]), int_or_none(row[10])]
        destination.reserved=int_or_none(row[11])
        destination.upgrades = 0
        destinations.append(destination)

routes = []
with open('Routes.csv') as csv_file:
    reader = csv.reader(csv_file)
    for row in reader:
        route = Route()
        route.place_1 = row[0]
        route.place_2 = row[1]
        route.color = row[2]
        route.amount = int_or_none(row[3]) or 0
        route.cost = int_or_none(row[4])
        routes.append(route)

phase = 0

destination_colors = {"Export":"#ffdddd", "City":"#ddddff", "Town":"#000000"}
destination_text_colors = {"Export":"#000000", "City":"#000000", "Town":"#000000"}
destination_text_size = {"Export":"8", "City":"8", "Town":"6"}
destination_dimensions = {"Export":(1, 1), "City":(.7, .7), "Town":(.4, .4)}
destination_shapes = {"Export":"none", "City":"none", "Town":"point"}

graph = graphviz.Graph(node_attr=[("nodesep","1")],
                       graph_attr=[("size", "25,25"),
                                   ("overlap", "false")])

def get_value_row(upgrades, values):
    max_value = max([i or 0 for i in values])
    values_culled = [i for i in values if i]
    result = "<TR>"
    for value in values_culled:
        result += f'<TD>{value}</TD>'
    result += "</TR>"
    return result

for destination in destinations:
    color = destination_colors[destination.dest_type]
    if destination.dest_type == "Town":
        graph.node(destination.id,
                   f"<<TABLE>{get_value_row(destination.upgrades, destination.values)}</TABLE>>",
                   xlabel=destination.display_name,
                   color=destination_colors[destination.dest_type],
                   style="filled",
                   shape=destination_shapes[destination.dest_type],
                   fontcolor=destination_text_colors[destination.dest_type],
                   fontsize = destination_text_size[destination.dest_type])
    else:
        max_stations = max([i or 0 for i in destination.stations])
        label = "<<TABLE>"
        label += "<TR>"
        label += f'<TD COLSPAN="{max(max_stations, 1)}">{destination.display_name}</TD>'
        label += "</TR>"
        if max_stations > 0:
            label += "<TR>"
            for station in range(max_stations):
                if station < destination.stations[phase]:
                    label += f"<TD><IMG SRC='CitySpace.png'/></TD>"
                else:
                    label += f"<TD><IMG SRC='CityNotYet.png'/></TD>"
            label += "</TR>"
        label += get_value_row(destination.upgrades, destination.values)
        label += "</TABLE>>"
        graph.node(destination.id,
                   label,
                   color=destination_colors[destination.dest_type],
                   style="filled",
                   shape=destination_shapes[destination.dest_type],
                   fontcolor=destination_text_colors[destination.dest_type],
                   fontsize = destination_text_size[destination.dest_type])

route_colors = {"red":"#cc0000",
                "green":"#00cc00",
                "blue":"#0000ff",
                "yellow": "#dddc00",
                "PHASE": "#ff00ff"}
route_text_colors = {"red":"#ffffff",
                     "green":"#000000",
                     "blue":"#ffffff",
                     "yellow": "#000000",
                     "PHASE": "#000000"}
route_weight = {"red":"1",
                "green":"1",
                "blue":"1",
                "yellow": "1",
                "PHASE": "0.5"}
for route in routes:
    start = last_node = route.place_1
    end = route.place_2
    for i in range(route.amount):
        id = f"{start}_{end}_{i}"
        label = str(route.cost or "")
        # Length weight is COST of lengthening - high = short
        length_weight = 8 if i > 0 else route_weight[route.color]
        graph.node(id,
                   label,
                   color=route_colors[route.color],
                   fontcolor=route_text_colors[route.color],
                   fontsize="6",
                   shape="box",
                   width=".1",
                   height=".1",
                   fixedsize="true",
                   style="filled")
        graph.edge(last_node,
                   id,
                   color=route_colors[route.color],
                   length=str(length_weight))
        last_node = id
    graph.edge(last_node, end, color=route_colors[route.color])

print(graph.source)