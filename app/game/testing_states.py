import random

names = ['Lachlan', 'Jayde', 'Brett', 'Joshua', 'Nathan', 'David']

def fake_stock_1(game):
    game.start_game([random.choice(names) for i in range(4)])
    while game.game_turn_status.value == 0:
        game.act_pa_buy()

states = {'gghf;': fake_stock_1}