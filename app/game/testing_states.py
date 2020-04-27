import random

names = ['Lachlan', 'Jayde', 'Brett', 'Joshua', 'Nathan', 'David']

def fake_stock_1(game):
    random.shuffle(names)
    game.start_game([names[i] for i in range(4)])
    while game.game_turn_status.value == 0:
        game.act_pa_buy()

states = {'glhf;': fake_stock_1}