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
