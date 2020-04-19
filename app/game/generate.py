import csv
import graphviz
import svgwrite

def generate_map(game):
    # Lazy, 'cause I couldn't be bothered changing code
    destinations = game.destinations
    routes = game.routes

    destination_colors = {"Export":"#ffdddd", "City":"#ddddff", "Town":"#000000"}
    destination_text_colors = {"Export":"#000000", "City":"#000000", "Town":"#000000"}
    destination_text_size = {"Export":"8", "City":"8", "Town":"6"}
    destination_shapes = {"Export":"none", "City":"none", "Town":"point"}

    graph = graphviz.Graph(engine="sfdp",
                           graph_attr=[("size", "20,20"),
                                       ("overlap","false"),
                                       #("splines","true"),
                                       ("pack","true"),
                                       ("sep","+7,7")])

    def get_value_row(upgrades, values, stations):
        values_culled = [i for i in values if i or i == 0]
        result = "<TR>"
        last_stations = stations[0] or 0
        for value in enumerate(values_culled):
            result += f'<TD>{value[1]}'
            if last_stations < (stations[value[0]] or last_stations):
                result += "<BR/>"
                for i in range(stations[value[0]] or 0):
                    result += "O"
                last_stations = stations[value[0]] or last_stations
            result += '</TD>'
        result += "</TR>"
        return result

    for destination in destinations:
        color = destination_colors[destination.dest_type]
        if destination.dest_type == "Town":
            graph.node(destination.id,
                    f"<<TABLE>{get_value_row(destination.upgrades, destination.values, destination.stations)}</TABLE>>",
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
            label += f'<TD>{destination.display_name}</TD>'
            label += "</TR>"
            if max_stations > 0:
                label += "<TR><TD><TABLE><TR>"
                for station in range(max_stations):
                    # TODO: Fix this. It's wrong. It should be amount upgrades
                    # in city, not phase of the station
                    if station < destination.stations[destination.current_upgrades]:
                        label += f"<TD><IMG SRC='app/assets/CitySpace.svg'/></TD>"
                label += "</TR></TABLE></TD></TR>"
            label += "<TR><TD><TABLE>"
            label += get_value_row(destination.upgrades, destination.values, destination.stations)
            label += "</TABLE></TD></TR></TABLE>>"
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
    route_weight = {"red":"0.5",
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
            min_len = "5" if i == 0 else "0"
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
                    minlen=min_len,
                    length=str(length_weight))
            last_node = id
        graph.edge(last_node, end,
                color=route_colors[route.color],
                minlen="5",
                length=str(length_weight))
    return graph.pipe(format="svg")

def generate_market(game):
    display = svgwrite.Drawing(size=("20,20"))
    return display.tostring()
    pass