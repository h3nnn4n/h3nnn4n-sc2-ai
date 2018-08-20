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
        attack_closest_enemy
        walk_back
        blink_back
        walk_random
    ]
'''

# TODO: Next step -> rewards


class StalkerQLearningController:
    def __init__(self, bot=None, verbose=False):
        self.bot = bot
        self.verbose = verbose

        self.feature = []

        self.actions = {
            'blink_back': self.action_blink_back,
            'walk_back': self.action_walk_back,
            'attack_closest_enemy': self.action_attack_closest_enemy,
            'walk_random': self.action_walk_random
        }

        self.alpha = 0.01
        self.gamma = 0.9
        self.epsilon = 1.0

        self.q_table = {}

        self.reward = {}

        self.font_size = 14
        self.visual_debug = True

    def step(self, unit_tag, can_blink=False):
        state = self.extract_state(unit_tag, can_blink=can_blink)
        action = self.choose_action(state, unit_tag)

        return action

    def extract_state(self, unit_tag, can_blink=False):
        state = []

        return tuple(state)

    def choose_action(self, state, unit_tag):
        self.check_state_exist(state)

        if random.random() <= self.epsilon:
            action = self.get_random_action(unit_tag)
        else:
            action = None

        return action

    def learn(self, s, a, r, s_):
        pass

    def check_state_exist(self, state):
        if state not in self.q_table.keys():
            self.q_table[state] = zip(
                self.actions,
                [0 for _ in range(len(self.actions))]
            )

    def get_random_action(self, unit_tag):
        action = random.choice(list(self.actions.values()))(unit_tag)

        return action

    def action_walk_back(self, unit_tag):
        unit = self.bot.units.find_by_tag(unit_tag)

        if self.visual_debug:
            self.bot._client.debug_text_world('walk_back', pos=unit.position3d, size=self.font_size)

        closest_unit = self.get_closest_enemy_unit(unit_tag)

        if closest_unit is not None:
            step_back_position = unit.position.towards(closest_unit.position, -2)
            return unit.move(step_back_position)

        return unit.move(unit)  # Idle action

    def action_walk_random(self, unit_tag):
        unit = self.bot.units.find_by_tag(unit_tag)

        if self.visual_debug:
            self.bot._client.debug_text_world('walk_random', pos=unit.position3d, size=self.font_size)

        random_position = unit.position.random_on_distance(10)
        return unit.move(random_position)

        # map_center = self.bot._game_info.map_center
        # map_size = self.bot._game_info.map_size
        # random_position = map_center.random_on_distance(min(map_size))

        # return unit.move(random_position)

    def action_blink_back(self, unit_tag):
        unit = self.bot.units.find_by_tag(unit_tag)

        if self.visual_debug:
            self.bot._client.debug_text_world('blink', pos=unit.position3d, size=self.font_size)

        closest_unit = self.get_closest_enemy_unit(unit_tag)

        if closest_unit is not None:
            blink_back_position = unit.position.towards(closest_unit.position, -8)
            return unit(AbilityId.EFFECT_BLINK_STALKER, blink_back_position)

        return unit.move(unit)  # Idle action

    def action_attack_closest_enemy(self, unit_tag):
        unit = self.bot.units.find_by_tag(unit_tag)

        if self.visual_debug:
            self.bot._client.debug_text_world('attack', pos=unit.position3d, size=self.font_size)

        closest_unit = self.get_closest_enemy_unit(unit_tag)

        if closest_unit is not None:
            return unit.attack(closest_unit)

        return unit.move(unit)  # Idle action

    def get_closest_enemy_unit(self, unit_tag):
        unit = self.bot.units.find_by_tag(unit_tag)

        all_enemy_units = self.bot.known_enemy_units.exclude_type(self.bot.army_controller.units_to_ignore_attacking)
        enemy_units = all_enemy_units.not_structure

        if enemy_units.exists:
            closest_unit = enemy_units.closest_to(unit)
        elif all_enemy_units.exists:
            closest_unit = all_enemy_units.closest_to(unit)
        else:
            closest_unit = None

        return closest_unit
