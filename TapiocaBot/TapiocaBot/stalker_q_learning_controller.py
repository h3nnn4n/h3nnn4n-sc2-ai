# pylint: disable=E0401

import random
import math
from unit_ai_controller import UnitAiController
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2

'''
    Feature vector [
        in_enemy_range: bool  2 possible values
        distance_to_enemy: [0 .. self_sight_range]  10 possible values
        enemy_health_percentage: [0 .. 100, steps of 10]  11 possible values
        enemy_range: int  about 3 possible values
        enemy_in_range: bool  2 possible values
        enemy_in_sight: bool  2 possible values
        self_health_percentage: [0 .. 100, steps of 10]  11 possible values
        self_shield_percentage: [0 .. 100, steps of 10]  11 possible values
        self_range: int  1 possible value
        self_can_shoot: bool  2 possible values
        self_can_blink: bool  2 possible values
    ]

    Using: [
        in_enemy_range
        enemy_in_range
        enemy_in_sight
        self_can_shoot
        self_can_blink
    ]

    Feature space size = 2 * 2 * 2 * 2 * 2= 32  ;)

    Action vector [
        attack_closest_enemy
        walk_back
        blink_back
        walk_random
    ]

    Rewards: [
        damage_taken
        damage_inflicted
        units_killed
        death
    ]
'''

# TODO: Next step -> rewards


class StalkerQLearningController(UnitAiController):
    def __init__(self, bot=None, verbose=False):
        self.bot = bot
        self.verbose = verbose

        self.feature = []

        self.actions = {
            # 'blink_back': self.action_blink_back,
            'walk_back': self.action_walk_back,
            'attack_closest_enemy': self.action_attack_closest_enemy,
            # 'walk_random': self.action_walk_random,
            'walk_left': self.action_walk_left
        }

        self.alpha = 0.2
        self.gamma = 0.6
        self.epsilon = 0.05

        self.q_table = {}

        self.reward = {}

        self.reward_weights = {
            'enemy_damage': 5.0,
            'damage_taken': -2.5,
            'units_killed': 1000,
            'death': -1000,
            'step': -0.1,
            'idle': -50.0,
        }

        self.unit_type_reward_height = {
            'zergling': 2,
            'roach': 5
        }

        self.step_count = 0
        self.idle_count = 0
        self.previous_state = None
        self.current_state = None
        self.last_action = None
        self.last_reward = 0
        self.killed_value_units = 0
        self.died_last_round = False
        self.total_deaths = 0
        self.total_kills = 0
        self.highest_reward = float('-inf')
        self.most_kills = 0
        self.most_damage_inflicted = 0
        self.damage_inflicted = 0

        self.font_size = 14
        self.visual_debug = True

        self.current_unit_tag = None

        self.reset_reward()

    def reset_reward(self):
        self.reward = {
            'enemy_damage': {},
            'damage_taken': 0,
            'units_killed': 0,
            'step': 0,
            'death': 0,
            'idle': 0
        }

        self.idle_count = 0
        self.step_count = 0

    def before_action_(self, unit_tag, can_blink=False):
        if self.idle_count > 100:
            print('killSwitch triggered: ', unit_tag)
            # await self.bot.debug_controller.debug_destroy_unit(unit_tag)

            self.current_unit_tag = unit_tag
            self.died_last_round = True
            self.reward['death'] += 1

        if self.current_unit_tag is None:
            self.current_unit_tag = unit_tag
        elif self.current_unit_tag != unit_tag:
            self.current_unit_tag = unit_tag
            self.died_last_round = True
            self.reward['death'] += 1
            print('unit died: ', unit_tag)
        elif self.died_last_round:
            self.total_deaths += 1
            self.total_kills = 0
            self.most_kills = max(self.most_kills, self.reward['units_killed'])
            self.highest_reward = max(self.highest_reward, self.last_reward)
            self.most_damage_inflicted = max(self.most_damage_inflicted, 0 + sum(self.reward['enemy_damage'].values()))
            self.died_last_round = False
            print('reset reward %f' % self.last_reward)
            self.reset_reward()

        # self.bot.debug_controller.debug_text_screen('%s' % str(self.previous_state))
        # self.bot.debug_controller.debug_text_screen('%s' % str(self.state))
        # self.bot.debug_controller.debug_text_screen('')
        # self.bot.debug_controller.debug_text_screen('                steps: %8d' % self.step_count)
        # self.bot.debug_controller.debug_text_screen('           steps_idle: %8d' % self.idle_count)
        # self.bot.debug_controller.debug_text_screen('         total_reward: %8.2f' % self.last_reward)
        # self.bot.debug_controller.debug_text_screen('               reward: %8.2f' % (reward - self.last_reward))
        # self.bot.debug_controller.debug_text_screen('               action: %s' % self.last_action)
        # self.bot.debug_controller.debug_text_screen('                 idle: %s' % (
        #     self.bot.units.find_by_tag(unit_tag).is_idle)
        # )
        # self.bot.debug_controller.debug_text_screen('')
        # self.bot.debug_controller.debug_text_screen('         total_deaths: %8d' % self.total_deaths)
        # self.bot.debug_controller.debug_text_screen('          total_kills: %8d' % self.total_kills)
        # self.bot.debug_controller.debug_text_screen('           most_kills: %8d' % self.most_kills)
        # self.bot.debug_controller.debug_text_screen('       highest_reward: %8.2f' % self.highest_reward)
        # self.bot.debug_controller.debug_text_screen('most_damage_inflicted: %8.2f' % self.most_damage_inflicted)
        # self.bot.debug_controller.debug_text_screen('     damage_inflicted: %8.2f' % (
        #     0 + sum(self.reward['enemy_damage'].values()))
        # )

########################

    def prepare_first_step(self, unit_tag):
        self.current_state = self.extract_state(unit_tag)
        self.current_reward = self.get_reward(unit_tag, self.current_state)

    def prepare_step(self, unit_tag):
        pass

    def before_action(self, unit_tag):
        action, action_name = self.choose_action(unit_tag, self.current_state)

        self.last_action = action_name

        return action

    def after_action(self, unit_tag):
        self.previous_state = self.current_state
        self.current_state = self.extract_state(unit_tag)

        self.last_reward = self.current_reward
        self.current_reward = self.get_reward(unit_tag, self.current_state)

        self.learn(self.previous_state, self.last_action, self.current_reward - self.last_reward, self.current_state)

        self.debug(unit_tag)

    def end_step(self, unit_tag):
        self.update_units_killed()
        self.step_count += 1
        self.idle_count += 1 if self.bot.units.find_by_tag(unit_tag).is_idle else 0

    def debug(self, unit_tag):
        self.bot.debug_controller.debug_text_screen('%s' % str(self.previous_state))
        self.bot.debug_controller.debug_text_screen('%s' % str(self.current_state))
        self.bot.debug_controller.debug_text_screen('')
        self.bot.debug_controller.debug_text_screen('                steps: %8d' % self.step_count)
        self.bot.debug_controller.debug_text_screen('           steps_idle: %8d' % self.idle_count)
        self.bot.debug_controller.debug_text_screen('         total_reward: %8.2f' % self.current_reward)
        self.bot.debug_controller.debug_text_screen('               reward: %8.2f' % (self.current_reward - self.last_reward))
        self.bot.debug_controller.debug_text_screen('               action: %s' % self.last_action)
        self.bot.debug_controller.debug_text_screen('                 idle: %s' % (
            self.bot.units.find_by_tag(unit_tag).is_idle)
        )
        self.bot.debug_controller.debug_text_screen('')
        self.bot.debug_controller.debug_text_screen('         total_deaths: %8d' % self.total_deaths)
        self.bot.debug_controller.debug_text_screen('          total_kills: %8d' % self.total_kills)
        self.bot.debug_controller.debug_text_screen('           most_kills: %8d' % self.most_kills)
        self.bot.debug_controller.debug_text_screen('       highest_reward: %8.2f' % self.highest_reward)
        self.bot.debug_controller.debug_text_screen('most_damage_inflicted: %8.2f' % self.most_damage_inflicted)
        self.bot.debug_controller.debug_text_screen('     damage_inflicted: %8.2f' % (
            0 + sum(self.reward['enemy_damage'].values()))
        )

########################

    def get_reward(self, unit_tag, state):
        unit = self.bot.units.find_by_tag(unit_tag)

        self.reward['damage_taken'] = (
            unit.health_max - unit.health +
            unit.shield - unit.shield_max
        )

        self.reward['step'] = self.step_count

        enemy_damage = self.update_damage_inflicted()

        return (
            self.reward['damage_taken'] * self.reward_weights['damage_taken'] +
            enemy_damage * self.reward_weights['enemy_damage'] +
            self.reward['step'] * self.reward_weights['step'] +
            self.reward['units_killed'] * self.reward_weights['units_killed'] +
            self.reward['death'] * self.reward_weights['death'] +
            self.reward['idle'] * self.reward_weights['idle']
        )

    def update_damage_inflicted(self):
        for enemy_unit in self.bot.known_enemy_units:
            self.reward['enemy_damage'][enemy_unit.tag] = (
                (enemy_unit.health_max - enemy_unit.health) +
                (enemy_unit.shield_max - enemy_unit.shield)
            )

        return 0 + sum(self.reward['enemy_damage'].values())

    def extract_state(self, unit_tag, can_blink=False):
        '''
        Feature vector [
            in_enemy_range: bool  2 possible values
            distance_to_enemy: [0 .. self_sight_range]  10 possible values
            enemy_health_percentage: [0 .. 100, steps of 10]  11 possible values
            enemy_range: int  about 3 possible values
            enemy_in_range: bool  2 possible values
            enemy_in_sight: bool  2 possible values
            self_health_percentage: [0 .. 100, steps of 10]  11 possible values
            self_shield_percentage: [0 .. 100, steps of 10]  11 possible values
            self_range: int  1 possible value
            self_can_shoot: bool  2 possible values
            self_can_blink: bool  2 possible values
        ]
        '''

        # TODO: Add booleans to turn on and off the features

        in_enemy_range = False
        distance_to_enemy = 0
        # enemy_health_percentage = 0
        # enemy_range = 0
        enemy_in_range = False
        enemy_in_sight = False
        # self_health_percentage = 0
        # self_shield_percentage = 0
        # self_range = 0
        self_can_shoot = 0
        self_can_blink = 0

        unit = self.bot.units.find_by_tag(unit_tag)
        closest_unit = self.get_closest_enemy_unit(unit_tag)

        if closest_unit is not None:
            distance_to_enemy = (
                unit.position.distance_to(closest_unit) -
                unit.radius / 2 - closest_unit.radius / 2
            )
            # enemy_health_percentage = (
            #     closest_unit.health + closest_unit.shield
            # ) / (
            #     closest_unit.health_max + closest_unit.shield_max
            # )
            # enemy_range = closest_unit.ground_range
            in_enemy_range = distance_to_enemy <= closest_unit.ground_range
            enemy_in_range = distance_to_enemy <= unit.ground_range
            enemy_in_sight = distance_to_enemy <= unit.sight_range

        # self_health_percentage = unit.health_percentage
        # self_shield_percentage = unit.shield_percentage
        # self_range = unit.ground_range
        self_can_shoot = unit.weapon_cooldown == 0
        self_can_blink = can_blink

        state = [
            in_enemy_range,
            enemy_in_range,
            enemy_in_sight,
            self_can_shoot,
            self_can_blink
        ]

        return tuple(state)

    def choose_action(self, unit_tag, state):
        self.check_state_exist(state)

        if random.random() <= self.epsilon:
            result = self.get_random_action(unit_tag)
        else:
            result = self.get_best_action(unit_tag, state)

        return result

    def learn(self, state, action, reward, state_):
        self.check_state_exist(state_)

        max_q = self.q_table[state][
            max(self.q_table[state].keys(), key=(lambda k: self.q_table[state][k]))
        ]

        self.q_table[state][action] += self.alpha * (
            reward +
            self.gamma * max_q -
            self.q_table[state][action]
        )

    def check_state_exist(self, state):
        if state not in self.q_table.keys():
            # enemy_in_sight = state[2]

            self.q_table[state] = {
                key: value for (key, value) in zip(
                    self.actions,
                    [0 for _ in range(len(self.actions))]
                )
            }

            # if not enemy_in_sight:
            #     self.q_table[state].pop('attack_closest_enemy')

    def get_random_action(self, unit_tag):
        action_name = random.choice(list(self.actions.keys()))
        action = self.actions[action_name](unit_tag)

        return action, action_name

    def get_best_action(self, unit_tag, state):
        max_q = self.q_table[state][
            max(self.q_table[state].keys(), key=(lambda k: self.q_table[state][k]))
        ]

        action_name = random.choice(
            [
                action for action, reward in self.q_table[state].items() if reward == max_q
            ]
        )

        action = self.actions[action_name](unit_tag)

        return action, action_name

    def action_walk_back(self, unit_tag):
        unit = self.bot.units.find_by_tag(unit_tag)

        if self.visual_debug:
            self.bot._client.debug_text_world(
                'walk_back',
                pos=unit.position3d,
                size=self.font_size
            )

        closest_unit = self.get_closest_enemy_unit(unit_tag)

        if closest_unit is not None:
            step_back_position = unit.position.towards(
                closest_unit.position,
                -2
            )
            return unit.move(step_back_position)

        return unit.move(unit)  # Idle action

    def action_walk_random(self, unit_tag):
        # Improve random walk
        # a bad one will get the agent stuck and losing lots of reward points
        unit = self.bot.units.find_by_tag(unit_tag)

        if self.visual_debug:
            self.bot._client.debug_text_world(
                'walk_random',
                pos=unit.position3d,
                size=self.font_size
            )

        random_position = unit.position.random_on_distance(10)
        return unit.move(random_position)

        # map_center = self.bot._game_info.map_center
        # map_size = self.bot._game_info.map_size
        # random_position = map_center.random_on_distance(min(map_size))

        # return unit.move(random_position)
    def action_walk_left(self, unit_tag):
        # Improve random walk
        # a bad one will get the agent stuck and losing lots of reward points
        unit = self.bot.units.find_by_tag(unit_tag)

        if self.visual_debug:
            self.bot._client.debug_text_world(
                'walk_left',
                pos=unit.position3d,
                size=self.font_size
            )

        unit_position = unit.position.to2

        left_position = Point2((unit_position.x - 10, unit_position.y))
        return unit.move(left_position)

    def action_blink_back(self, unit_tag):
        unit = self.bot.units.find_by_tag(unit_tag)

        if self.visual_debug:
            self.bot._client.debug_text_world(
                'blink',
                pos=unit.position3d,
                size=self.font_size
            )

        closest_unit = self.get_closest_enemy_unit(unit_tag)

        if closest_unit is not None:
            blink_back_position = unit.position.towards(
                closest_unit.position,
                -8
            )
            return unit(AbilityId.EFFECT_BLINK_STALKER, blink_back_position)

        return unit.move(unit)  # Idle action

    def action_attack_closest_enemy(self, unit_tag):
        unit = self.bot.units.find_by_tag(unit_tag)

        if self.visual_debug:
            self.bot._client.debug_text_world(
                'attack',
                pos=unit.position3d,
                size=self.font_size
            )

        closest_unit = self.get_closest_enemy_unit(unit_tag)

        if closest_unit is not None:
            return unit.attack(closest_unit)

        return unit.move(unit)  # Idle action

    def get_closest_enemy_unit(self, unit_tag):
        unit = self.bot.units.find_by_tag(unit_tag)

        all_enemy_units = self.bot.known_enemy_units.exclude_type(
            self.bot.army_controller.units_to_ignore_attacking)
        enemy_units = all_enemy_units.not_structure

        if enemy_units.exists:
            closest_unit = enemy_units.closest_to(unit)
        elif all_enemy_units.exists:
            closest_unit = all_enemy_units.closest_to(unit)
        else:
            closest_unit = None

        return closest_unit

    def update_units_killed(self):
        if self.bot.state.score.killed_value_units != self.killed_value_units:
            self.killed_value_units = self.bot.state.score.killed_value_units

            self.reward['units_killed'] += 1
            self.total_kills += 1
