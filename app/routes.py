import io
import datetime
from functools import wraps
from flask import send_file, render_template, redirect, url_for, request
from app import app, db
from app.game.game import Game
from app.game.generate import generate_map, generate_market

def bind_game(save=False):
    """A decorator that builds a game object from the database, and passes it
    in to the decorated function using the 'game' parameter.
    """
    def outer(func):
        @wraps(func)
        def inner(*args, **kwargs):
            game_id = kwargs["game_id"]
            state = db.load_game_state(game_id)
            game = Game(state)
            result = func(*args, **kwargs, game=game)

            if save:
                db.save_game_state(game_id, game.get_state(), datetime.datetime.now())

            return result
        return inner
    return outer


@app.route('/game/<game_id>/map')
@bind_game()
def map_image(game, game_id):
    image = io.BytesIO(generate_map(game, game_id))
    return send_file(image, mimetype="image/svg+xml")

@app.route('/game/<game_id>/market')
@bind_game()
def market(game, game_id):
    data = io.BytesIO(generate_market(game).encode("UTF-8"))
    return send_file(data, mimetype="image/svg+xml")

@app.route('/game/<game_id>/view')
@bind_game()
def view(game, game_id):
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
@bind_game(save=True)
def pa_pass(game, game_id):
    game.act_pa_pass()
    return redirect(url_for("view", game_id=game_id))

@app.route('/game/<game_id>/pa/buy')
@bind_game(save=True)
def pa_buy(game, game_id):
    game.act_pa_buy()
    return redirect(url_for("view", game_id=game_id))

@app.route('/game/<game_id>/pa/bid/<private_id>', methods=['POST'])
@bind_game(save=True)
def pa_bid(game, game_id, private_id):
    bid = int(request.form.get("bid_amt"))
    game.act_pa_bid(bid, private_id)
    return redirect(url_for("view", game_id=game_id))

@app.route('/game/<game_id>/<company_id>/start/', methods=['POST'])
@bind_game(save=True)
def sr_buy_president(game, game_id, company_id):
    ipo_price = int(request.form.get('president_price'))
    game.act_sr_buy_president(company_id, ipo_price)
    return redirect(url_for("view", game_id=game_id))

@app.route('/game/<game_id>/<company_id>/buy_ipo/', methods=['POST'])
@bind_game(save=True)
def sr_buy_ipo(game, game_id, company_id):
    game.act_sr_buy_ipo(company_id)
    return redirect(url_for("view", game_id=game_id))

@app.route('/game/<game_id>/<company_id>/buy_market/', methods=['POST'])
@bind_game(save=True)
def sr_buy_market(game, game_id, company_id):
    game.act_sr_buy_market(company_id)
    return redirect(url_for("view", game_id=game_id))

@app.route('/game/<game_id>/<company_id>/sell/', methods=['POST'])
@bind_game(save=True)
def sr_sell(game, game_id, company_id):
    amount = int(request.form.get('qty'))
    game.act_sr_sell(company_id, amount)
    return redirect(url_for("view", game_id=game_id))

@app.route('/game/<game_id>/sr_pass/', methods=['POST'])
@bind_game(save=True)
def sr_pass(game, game_id):
    game.act_sr_pass()
    return redirect(url_for("view", game_id=game_id))

@app.route('/game/<game_id>/sr_done/', methods=['POST'])
@bind_game(save=True)
def sr_done(game, game_id):
    game.act_sr_done()
    return redirect(url_for("view", game_id=game_id))

@app.route('/game/<game_id>/or_clear_route/<route_id>')
@bind_game(save=True)
def or_clear_route(game, game_id, route_id):
    game.act_or_clear_route(route_id)
    return redirect(url_for("view", game_id=game_id))

@app.route('/game/<game_id>/or_pass')
@bind_game(save=True)
def or_pass(game, game_id):
    game.act_or_pass()
    return redirect(url_for("view", game_id=game_id))

@app.route('/game/<game_id>/or_buy_office/<dest_id>')
@bind_game(save=True)
def or_buy_office(game, game_id, dest_id):
    game.act_or_buy_office(dest_id)
    return redirect(url_for("view", game_id=game_id))

@app.route('/game/<game_id>/or_buy_monster/<monster_id>')
@bind_game(save=True)
def or_buy_monster(game, game_id, monster_id):
    game.act_or_buy_monster(monster_id)
    return redirect(url_for("view", game_id=game_id))