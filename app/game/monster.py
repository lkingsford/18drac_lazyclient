from enum import Enum

class SpecialRules(Enum):
    spread = "Sp"
    nurse = "Nu"
    claw = "Cl"
    fang = "Fg"
    swearwolf = "Sw"
    non_blocking = "Nb"
    groustfrat = "Gf"
    no_token = "Nt"
    draculas_castle_as_token = "Dm"
    infinite_distance = "Id"
    duke_lupin = "Dl"

class Monster:
    def __init__(self, game, id, name, phase, cost, expires, movement, special_rules, trade_cost):
        self.game = game
        self.id = id
        self.name = name
        self.phase = phase
        self.cost = cost
        self.expires = expires
        self.movement = movement
        self.special_rules = set(special_rules)
        self.trade_cost = trade_cost
        self.owner = None
        self.in_market = False

    def get_move_display(self):
        if self.movement == 0:
            return ""

        if self.movement == 1:
            return "Starting town only"

        result = str(self.movement)

        if SpecialRules.spread in self.special_rules:
            result += " spread"

        if SpecialRules.infinite_distance in self.special_rules:
            return " inf."

        return result

    def get_special_rules(self):
        rules = []
        if SpecialRules.nurse in self.special_rules:
            rules.append("Only purchasable by Blundell's Transfusions. Run up to X nurses in a town where X is the amount of connections.")
        if SpecialRules.claw in self.special_rules:
            rules.append("Claw. Can not purchase Fang.")
        if SpecialRules.fang in self.special_rules:
            rules.append("Fang. Can not purchase Claw.")
        if SpecialRules.swearwolf in self.special_rules:
            rules.append("Does not count again monster limit. Killed if Claw purchased")
        if SpecialRules.non_blocking in self.special_rules:
            rules.append("Not blocked by full cities")
        if SpecialRules.groustfrat in self.special_rules:
            rules.append("Functions as 3xSkeleton")
        if SpecialRules.draculas_castle_as_token in self.special_rules:
            rules.append("Can use Dracula's Moving Castle as a token")
        if SpecialRules.no_token in self.special_rules:
            rules.append("Does not require a token on the run")
        if SpecialRules.duke_lupin in self.special_rules:
            rules.append("Can run to all adjacent cities from all tokens. Does not block route from other monster.")
        return rules

    def get_trades(self):
        # Todo: Get monster display name
        return ", ".join([f"{next(iter([j.name for j in self.game.monsters if j.id == i[0]]))} ({i[1]} pts)" for i in self.trade_cost])

    def get_state(self):
        if self.owner == None and self.in_market == False:
            return ""
        else:
            return {"owner": self.owner.id if self.owner else None, "in_market": self.in_market}

    def load_state(self, state):
        self.owner = self.game.companies[state["owner"]] if state["owner"] else None
        self.in_market = state["in_market"]