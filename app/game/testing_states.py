import random

names = ['Lachlan', 'Jayde', 'Brett', 'Joshua', 'Nathan', 'David']

def fake_stock_1(game):
    random.shuffle(names)
    game.start_game([names[i] for i in range(4)])
    while game.game_turn_status.value == 0:
        if game.current_player.cash > game.pa_current_private.base_cost:
            game.act_pa_buy()
        else:
            game.act_pa_pass()

def fake_or_1(game):
    fake_stock_1(game)
    game.act_sr_pass()
    game.act_sr_buy_president('ss', 100)
    game.act_sr_buy_president('ett', 100)
    game.act_sr_buy_president('gs', 67)
    for i in ['ss', 'ss', 'ss', 'ss', 'ett', 'ett', 'ett', 'ett', 'gs', 'gs', 'gs', 'gs']:
        if game.sr_show_buy_ipo(game.companies[i]):
            game.act_sr_buy_ipo(i)
        else:
            game.act_sr_pass()
    for i in range(4):
        game.act_sr_pass()

states = {'glhf;': fake_stock_1,
          'ggez;': fake_or_1,
          }