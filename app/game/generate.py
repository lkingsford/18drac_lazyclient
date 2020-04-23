import csv
from flask import url_for
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

    images = {"CitySpace": ['app/assets/CitySpace.svg', url_for('static_assets', path='CitySpace.svg')],
              "bh": ['app/assets/tokens/bh.svg', url_for('static_assets', path="tokens/bh.svg")],
              "bh_flip": ['app/assets/tokens/bh_flip.svg', url_for('static_assets', path="tokens/bh_flip.svg")],
              "bt": ['app/assets/tokens/bt.svg', url_for('static_assets', path="tokens/bt.svg")],
              "bt_flip": ['app/assets/tokens/bt_flip.svg', url_for('static_assets', path="tokens/bt_flip.svg")],
              "ett": ['app/assets/tokens/ett.svg', url_for('static_assets', path="tokens/ett.svg")],
              "ett_flip": ['app/assets/tokens/ett_flip.svg', url_for('static_assets', path="tokens/ett_flip.svg")],
              "gs": ['app/assets/tokens/gs.svg', url_for('static_assets', path="tokens/gs.svg")],
              "gs_flip": ['app/assets/tokens/gs_flip.svg', url_for('static_assets', path="tokens/gs_flip.svg")],
              "gw": ['app/assets/tokens/gw.svg', url_for('static_assets', path="tokens/gw.svg")],
              "gw_flip": ['app/assets/tokens/gw_flip.svg', url_for('static_assets', path="tokens/gw_flip.svg")],
              "ibs": ['app/assets/tokens/ibs.svg', url_for('static_assets', path="tokens/ibs.svg")],
              "ibs_flip": ['app/assets/tokens/ibs_flip.svg', url_for('static_assets', path="tokens/ibs_flip.svg")],
              "ka": ['app/assets/tokens/ka.svg', url_for('static_assets', path="tokens/ka.svg")],
              "ka_flip": ['app/assets/tokens/ka_flip.svg', url_for('static_assets', path="tokens/ka_flip.svg")],
              "ll": ['app/assets/tokens/ll.svg', url_for('static_assets', path="tokens/ll.svg")],
              "ll_flip": ['app/assets/tokens/ll_flip.svg', url_for('static_assets', path="tokens/ll_flip.svg")],
              "ss": ['app/assets/tokens/ss.svg', url_for('static_assets', path="tokens/ss.svg")],
              "ss_flip": ['app/assets/tokens/ss_flip.svg', url_for('static_assets', path="tokens/ss_flip.svg")],
              "uu": ['app/assets/tokens/uu.svg', url_for('static_assets', path="tokens/uu.svg")],
              "uu_flip": ['app/assets/tokens/uu_flip.svg', url_for('static_assets', path="tokens/uu_flip.svg")]}


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
                    f"<<TABLE>{get_value_row(destination.upgrades, destination.values, destination.station_count)}</TABLE>>",
                    xlabel=destination.display_name,
                    color=destination_colors[destination.dest_type],
                    style="filled",
                    shape=destination_shapes[destination.dest_type],
                    fontcolor=destination_text_colors[destination.dest_type],
                    fontsize = destination_text_size[destination.dest_type])
        else:
            max_stations = max([i or 0 for i in destination.station_count])
            label = "<<TABLE>"
            label += "<TR>"
            label += f'<TD>{destination.display_name}</TD>'
            label += "</TR>"
            if max_stations > 0:
                label += "<TR><TD><TABLE><TR>"
                for station in range(max_stations):
                    if station < destination.station_count[destination.current_upgrades]:
                        image = 'CitySpace'
                        if len(destination.stations) > station:
                            co = destination.stations[station]
                            started = game.companies[co].started
                            image = co + ("" if started else "_flip")
                        label += f"<TD fixedsize='true'><IMG SRC='{(images[image])[0]}'/></TD>"
                label += "</TR></TABLE></TD></TR>"
            label += "<TR><TD><TABLE>"
            label += get_value_row(destination.upgrades, destination.values, destination.station_count)
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
    svg_file = graph.pipe(format="svg")
    # Hacky, but we want the url to be correct for the image
    # Basically, graphviz's paths are different to the ones available on the
    # web app - so yeah.
    svg_file_text = svg_file.decode()
    for row in images.values():
        svg_file_text = svg_file_text.replace(row[0], row[1])
    return svg_file_text.encode('utf-8')

def generate_market(game):
    display = svgwrite.Drawing(size=("900px","500px"))
    market = game.market
    scale = 50
    for row in enumerate(market.table):
        for cell in enumerate(row[1]):
            if cell[1]:
                color = {"y":"#cccc00",
                         "b":"#deaa87",
                         "w":"#ffffff",
                         "i":"#ffcccc"}[cell[1].color]
                display.add(display.rect((cell[0] * scale, row[0] * scale),
                            (scale, scale),
                            stroke="black", fill=color))
                display.add(display.text(cell[1].price,
                                         insert=(cell[0] * scale + scale / 5,
                                                 row[0] * scale + scale / 2),
                                         fill="black"))

    return display.tostring()
