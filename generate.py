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
        destination.station=[int_or_none(row[7]), int_or_none(row[8]), int_or_none(row[9]), int_or_none(row[10])]
        destination.reserved=int_or_none(row[11])
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

destination_colors = {"Export":"#ffdddd", "City":"#ddddff", "Town":"#000000"}
destination_text_colors = {"Export":"#000000", "City":"#000000", "Town":"#000000"}
destination_text_size = {"Export":"12", "City":"8", "Town":"6"}
destination_dimensions = {"Export":(1, 1), "City":(.7, .7), "Town":(.4, .4)}
destination_shapes = {"Export":"circle", "City":"circle", "Town":"point"}

graph = graphviz.Graph(node_attr=[("nodesep",".2")],
                       graph_attr=[("size", "16,16"),
                                   ("overlap", "false")])
for destination in destinations:
    color = destination_colors[destination.dest_type]
    xlabel = destination.display_name if destination.dest_type == "Town" else "";
    graph.node(destination.id,
               destination.display_name,
               xlabel=xlabel,
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
                "green":"1.5",
                "blue":"1",
                "yellow": "2",
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