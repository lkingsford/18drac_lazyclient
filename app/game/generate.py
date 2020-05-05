import csv
from flask import url_for
import graphviz
import svgwrite
from functools import reduce
from operator import concat
from .game import GameTurnStatus

# Must be generated during query for url_for
def images():
    return {"CitySpace": ['app/assets/CitySpace.svg', url_for('static_assets', path='CitySpace.svg')],
            "CityCanOpen": ['app/assets/CityCanOpen.svg', url_for('static_assets', path='CityCanOpen.svg')],
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

def generate_map(game, game_id):
    # Lazy, 'cause I couldn't be bothered changing code
    destinations = game.map.destinations
    routes = game.map.routes

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

    if game.game_turn_status == GameTurnStatus.operation_buy_office and\
       game.or_co.cash >= game.or_co.token_cost():
        can_open_office = [i.id for i in game.map.get_open_offices(game.or_co)]
    else:
        can_open_office = []

    for destination in destinations:
        color = destination_colors[destination.dest_type]
        href = ""
        target = "_top"
        if game.game_turn_status in [GameTurnStatus.operation_rampage]:
            if game.or_rampage_valid_next_node(destination):
                href = url_for("or_add_node_to_route", game_id=game_id, node_id=destination.id)
                color = "#FF00FF"
            elif game.or_in_current_route(destination):
                color = "#FF0000"
            else:
                color = "#888888"

        if destination.dest_type == "Town":
            graph.node(destination.id,
                    f"<<TABLE>{get_value_row(destination.upgrades, destination.values, destination.station_count)}</TABLE>>",
                    xlabel=destination.name,
                    color=color,
                    style="filled",
                    href=href,
                    target=target,
                    shape=destination_shapes[destination.dest_type],
                    fontcolor=destination_text_colors[destination.dest_type],
                    fontsize = destination_text_size[destination.dest_type])
        else:
            max_stations = max([i or 0 for i in destination.station_count])
            label = f"<<TABLE HREF='{href}' TARGET='_top'>"
            label += "<TR>"
            label += f'<TD>{destination.name}</TD>'
            label += "</TR>"
            if max_stations > 0:
                label += "<TR><TD><TABLE><TR>"
                for station in range(max_stations):
                    if station < destination.station_count[destination.upgrades]:
                        image = 'CitySpace'
                        href = ""
                        if len(destination.stations) > station:
                            co = destination.stations[station]
                            started = game.companies[co].floated
                            image = co + ("" if started else "_flip")
                        elif destination.id in can_open_office:
                            image = "CityCanOpen"
                            href = url_for("or_buy_office", game_id=game_id, dest_id=destination.id)
                        label += f"<TD HREF='{href}' TARGET='_top'><IMG SRC='{(images()[image])[0]}'/></TD>"
                label += "</TR></TABLE></TD></TR>"
            label += "<TR><TD><TABLE>"
            label += get_value_row(destination.upgrades, destination.values, destination.station_count)
            label += "</TABLE></TD></TR></TABLE>>"
            graph.node(destination.id,
                    label,
                    color=color,
                    style="filled",
                    shape=destination_shapes[destination.dest_type],
                    fontcolor=destination_text_colors[destination.dest_type],
                    href=href,
                    target=target,
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
    route_rampage_colors = {"this_route":"#ff0000",
                            "available":"#000000",
                            "other_route":"#00ff00"}

    if game.game_turn_status in [GameTurnStatus.operation_rampage]:
        # Rampage map is different - no mid nodes
        for route in routes:
            if not route.can_go_through():
                continue
            pen_thick = 1
            node_size = .1
            start = route.place_1
            end = route.place_2
            id = f"{start}_{end}"
            length_weight = route_weight[route.color]
            min_len = "5"
            try:
                # Not good... this should be rejected in code review
                current_route=reduce(concat, game.or_get_route_routes(game.rampage_editing_route_monster_idx))
            except TypeError:
                current_route=[]
            try:
                other_routes=reduce(concat, reduce(concat, [game.or_get_route_routes(i) for i in range(len(game.or_co.monsters())) if i != game.rampage_editing_route_monster_idx]))
            except TypeError:
                other_routes=[]
            color=route_rampage_colors["available"]
            if route in other_routes:
                color = route_rampage_colors["other_route"]
            if route in current_route:
                color = route_rampage_colors["this_route"]
            graph.edge(start,
                    end,
                    color=color,
                    minlen=min_len,
                    penwidth=str(pen_thick),
                    length=str(length_weight))

    else:
        clear_routes = []
        clear_stage = game.game_turn_status == GameTurnStatus.operation_clear_track
        if clear_stage:
            clear_routes = list(game.map.get_clearing_routes(game.or_co))

        for route in routes:
            special_clear_format = route in clear_routes
            pen_thick = 3 if special_clear_format else 1
            node_size = .4 if special_clear_format else (.05 if clear_stage else .1)
            href = "" if not special_clear_format else url_for('or_clear_route', game_id=game_id, route_id=route.id)

            start = last_node = route.place_1
            end = route.place_2
            for i in range(route.amount):
                id = f"{start}_{end}_{i}"
                label = str(route.cost or "")
                # Length weight is COST of lengthening - high = short
                length_weight = 8 if i > 0 else route_weight[route.color]
                min_len = "5" if i == 0 else "0"
                filled = i >= (route.cleared)
                graph.node(id,
                        label,
                        color=route_colors[route.color],
                        fontcolor=route_text_colors[route.color],
                        fontsize="6",
                        shape="box",
                        width=str(node_size),
                        height=str(node_size),
                        fixedsize="true",
                        href=href,
                        target="_top",
                        style="filled" if filled else "")
                graph.edge(last_node,
                        id,
                        color=route_colors[route.color],
                        minlen=min_len,
                        penwidth=str(pen_thick),
                        length=str(length_weight))
                last_node = id
            graph.edge(last_node, end,
                    color=route_colors[route.color],
                    minlen="5",
                    penwidth=str(pen_thick),
                    length=str(route_weight[route.color]))
    svg_file = graph.pipe(format="svg")
    # Hacky, but we want the url to be correct for the image
    # Basically, graphviz's paths are different to the ones available on the
    # web app - so yeah.
    svg_file_text = svg_file.decode()
    for row in images().values():
        svg_file_text = svg_file_text.replace(row[0], row[1])
    return svg_file_text.encode('utf-8')

def generate_market(game):
    display = svgwrite.Drawing(size=("900px","550px"))
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
                                         insert=(cell[0] * scale + scale / 10,
                                                 row[0] * scale + scale / 3),
                                         fill="black"))

    for row in enumerate(market.table):
        for cell in enumerate(row[1]):
            if cell[1]:
                for number, company in reversed(list(enumerate(cell[1].companies))):
                    imgsize = 26
                    x = (1 + cell[0]) * scale - imgsize
                    y = (number) * scale / 5 + row[0] * scale
                    image = company.id + ("" if (company.floated and not company.acted_this_or) else "_flip")
                    display.add(display.image(href=images()[image][1],
                                            insert=(x, y),
                                            size=(imgsize, imgsize)))

    return display.tostring()