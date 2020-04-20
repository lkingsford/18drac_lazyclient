import io
from flask import send_file
from app import app
from app.game.game import Game
from app.game.generate import generate_map, generate_market

@app.route('/map')
def map_image():
    game = Game()
    image = io.BytesIO(generate_map(game))
    return send_file(image, mimetype="image/svg+xml")

@app.route('/market')
def market():
    game = Game()
    data = io.BytesIO(generate_market(game).encode("UTF-8"))
    return send_file(data, mimetype="image/svg+xml")