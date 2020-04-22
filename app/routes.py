import io
import datetime
from flask import send_file, render_template, redirect, url_for
from app import app, db
from app.game.game import Game
from app.game.generate import generate_map, generate_market

@app.route('/game/<game_id>/map')
def map_image(game_id):
    state = db.load_game_state(game_id)
    game = Game(state)
    image = io.BytesIO(generate_map(game))
    return send_file(image, mimetype="image/svg+xml")

@app.route('/game/<game_id>/market')
def market(game_id):
    state = db.load_game_state(game_id)
    game = Game(state)
    data = io.BytesIO(generate_market(game).encode("UTF-8"))
    return send_file(data, mimetype="image/svg+xml")

@app.route('/game/<game_id>/view')
def view(game_id):
    state = db.load_game_state(game_id)
    game = Game(state)
    return render_template("game_view.html", game_id=game_id)

@app.route('/create')
def create_form():
    return render_template('create.html')

@app.route('/create_game')
def create_game():
    game = Game()
    game_id = db.save_game_state(None, game.get_state(), datetime.datetime.now())
    return redirect(url_for("view", game_id=game_id))