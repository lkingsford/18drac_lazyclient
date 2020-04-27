import io
import datetime
from flask import send_file, render_template, redirect, url_for, request
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
    # Add things to help game separate logic
    for i in game.companies:
        game.companies[i].token_img = url_for('static_assets', path=f'tokens/{i}.svg')
    return render_template("game_view.html", game_id=game_id, game=game)

@app.route('/create')
def create_form():
    return render_template('create.html')

@app.route('/create_game', methods=['POST'])
def create_game():
    game = Game()
    player_1 = request.form.get('player_1_name')
    player_2 = request.form.get('player_2_name')
    player_3 = request.form.get('player_3_name')
    player_4 = request.form.get('player_4_name')
    player_5 = request.form.get('player_5_name')
    player_6 = request.form.get('player_6_name')
    players = [i for i in [player_1, player_2, player_3, player_4, player_5, player_6] if i and i != ""]
    game.start_game(players)
    game_id = db.save_game_state(None, game.get_state(), datetime.datetime.now())
    return redirect(url_for("view", game_id=game_id))

# Game play
@app.route('/game/<game_id>/pa/pass')
def pa_pass(game_id, game=None):
    state = db.load_game_state(game_id)
    game = Game(state)
    game.act_pa_pass()
    db.save_game_state(game_id, game.get_state(), datetime.datetime.now())
    return redirect(url_for("view", game_id=game_id))

@app.route('/game/<game_id>/pa/buy')
def pa_buy(game_id):
    state = db.load_game_state(game_id)
    game = Game(state)
    game.act_pa_buy()
    db.save_game_state(game_id, game.get_state(), datetime.datetime.now())
    return redirect(url_for("view", game_id=game_id))

@app.route('/game/<game_id>/pa/bid/<private_id>', methods=['POST'])
def pa_bid(game_id, private_id):
    state = db.load_game_state(game_id)
    game = Game(state)
    bid = int(request.form.get("bid_amt"))
    game.act_pa_bid(bid, private_id)
    db.save_game_state(game_id, game.get_state(), datetime.datetime.now())
    return redirect(url_for("view", game_id=game_id))@app.route('/game/<game_id>/pa/buy')

@app.route('/game/<game_id>/<company_id>/start/', methods=['POST'])
def sr_buy_president(game_id, company_id):
    state = db.load_game_state(game_id)
    game = Game(state)
    ipo_price = int(request.form.get('president_price'))
    game.act_sr_buy_president(company_id, ipo_price)
    db.save_game_state(game_id, game.get_state(), datetime.datetime.now())
    return redirect(url_for("view", game_id=game_id))

@app.route('/game/<game_id>/<company_id>/buy_ipo/', methods=['POST'])
def sr_buy_ipo(game_id, company_id):
    state = db.load_game_state(game_id)
    game = Game(state)
    game.act_sr_buy_ipo(company_id)
    db.save_game_state(game_id, game.get_state(), datetime.datetime.now())
    return redirect(url_for("view", game_id=game_id))

@app.route('/game/<game_id>/<company_id>/buy_market/', methods=['POST'])
def sr_buy_market(game_id, company_id):
    state = db.load_game_state(game_id)
    game = Game(state)
    game.act_sr_buy_market(company_id)
    db.save_game_state(game_id, game.get_state(), datetime.datetime.now())
    return redirect(url_for("view", game_id=game_id))

@app.route('/game/<game_id>/<company_id>/sell/', methods=['POST'])
def sr_sell(game_id, company_id):
    state = db.load_game_state(game_id)
    game = Game(state)
    amount = int(request.form.get('qty'))
    game.act_sr_sell(company_id, amount)
    db.save_game_state(game_id, game.get_state(), datetime.datetime.now())
    return redirect(url_for("view", game_id=game_id))

@app.route('/game/<game_id>/sr_pass/', methods=['POST'])
def sr_pass(game_id):
    state = db.load_game_state(game_id)
    game = Game(state)
    game.act_sr_pass()
    db.save_game_state(game_id, game.get_state(), datetime.datetime.now())
    return redirect(url_for("view", game_id=game_id))

@app.route('/game/<game_id>/sr_done/', methods=['POST'])
def sr_done(game_id):
    state = db.load_game_state(game_id)
    game = Game(state)
    game.act_sr_done()
    db.save_game_state(game_id, game.get_state(), datetime.datetime.now())
    return redirect(url_for("view", game_id=game_id))



