import random

names = ['Lachlan', 'Jayde', 'Brett', 'Joshua', 'Nathan', 'David']

def _4p_just_names(game):
    random.shuffle(names)
    game.start_game([names[i] for i in range(4)])

def fake_stock_1(game):
    _4p_just_names(game)
    while game.game_turn_status.value == 0:
        if game.current_player.cash > game.pa_current_private.base_cost:
            game.act_pa_buy()
        else:
            game.act_pa_pass()

def fake_or_1(game):
    fake_stock_1(game)
    game.act_sr_pass()
    game.act_sr_buy_president('ss', 67)
    game.act_sr_buy_president('ett', 73)
    game.act_sr_buy_president('gs', 67)
    for i in ['ss', 'ss', 'ss', 'ss', 'ett', 'ett', 'ett', 'ett', 'gs', 'gs', 'gs', 'gs']:
        while not game.sr_show_buy_ipo(game.companies[i]):
            game.act_sr_pass()
        game.act_sr_buy_ipo(i)
    for i in range(4):
        game.act_sr_pass()

def fake_or_1_a(game):
    fake_stock_1(game)
    game.act_sr_pass()
    game.act_sr_buy_president('gw', 67)
    game.act_sr_buy_president('uu', 73)
    game.act_sr_buy_president('gs', 67)
    for i in ['gw', 'gw', 'gw', 'gw', 'uu', 'uu', 'uu', 'uu', 'gs', 'gs', 'gs', 'gs']:
        while not game.sr_show_buy_ipo(game.companies[i]):
            game.act_sr_pass()
        game.act_sr_buy_ipo(i)
    for i in range(4):
        game.act_sr_pass()

states = {'glhf;': fake_stock_1,
          'ggez;': fake_or_1,
          'ggezr;': fake_or_1_a,
          'newb;': _4p_just_names,
          }