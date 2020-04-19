import io
from flask import send_file
from app import app
from app.game.game import Game
from app.game.generate import generate_map

@app.route('/map')
def map_image():
    game = Game()
    image = io.BytesIO(generate_map(game))
    return send_file(image, mimetype="image/svg+xml")

@app.route('/market')
def market():
    game = Game()
    market = game.market
    doc = "<html>"
    doc += "<body>"
    doc += "<table border=1>"
    for row in market.table:
        doc += "<tr>"
        for cell in row:
            if cell:
                color = {"y":"#cccc00",
                         "b":"#deaa87",
                         "w":"#ffffff",
                         "i":"#ffcccc"}[cell.color]
                doc += f"<td bgcolor='{color}'>{cell.price}</td>"
            else:
                doc += "<td></td>"
        doc += "</tr>"
    doc += "</table>"
    doc += "</body>"
    doc += "</html>"
    return doc