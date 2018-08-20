import random
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId

'''
    Feature vector [
        distance_to_enemy: [0 .. self_sight_range]  10 possible values
        enemy_health_percentage: [0 .. 100, steps of 10]  11 possible values
        enemy_range: int  about 3 possible values
        self_health_percentage: [0 .. 100, steps of 10]  11 possible values
        self_shield_percentage: [0 .. 100, steps of 10]  11 possible values
        self_range: int  1 possible value
        self_on_cooldown: bool  2 possible values
        self_blink_on_cooldown: bool  2 possible values
    ]

    Feature space sice = 10 * 11 * 3 * 11 * 11 * 1 * 2 * 2 = 159720

    Action vector [
        attack(enemy)
        walk_back
        blink_back
    ]
'''


class StalkerQLearningController:
    def __init__(self, bot=None, verbose=False):
        self.bot = bot
        self.verbose = verbose

        self.feature = []

        self.actions = {
        }

        self.alpha = 0.01
        self.gamma = 0.9
        self.epsilon = 0.9

        self.q_table = {}

        self.reward = {}

    def step(self, unit_tag):
        state = self.extract_state(unit_tag)
        action = self.choose_action(state)

        return action

    def extract_state(self, unit_tag):
        state = []

        return state

    def choose_action(self, state):
        self.check_state_exist(state)

        if random.random() < self.epsilon:
            pass
        else:
            pass

        return []

    def learn(self, s, a, r, s_):
        pass

    def check_state_exist(self, state):
        if state not in self.q_table.keys():
            self.q_table[state] = zip(
                self.actions,
                [0 for _ in range(len(self.actions))]
            )
