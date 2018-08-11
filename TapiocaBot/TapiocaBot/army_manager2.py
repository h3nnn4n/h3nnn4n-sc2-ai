import random
from sc2.constants import *


class ArmyManager:
    def __init__(self, bot=None, verbose=False):
        self.bot = bot
        self.verbose = verbose

        self.auto_recuit = True
        self.minimum_army_size = 20
        self.attack_trigger_radius = 10
        self.stop_radius = 5
        self.units_available_for_attack = {
            ZEALOT: 'ZEALOT',
            ADEPT: 'ADEPT',
            SENTRY: 'SENTRY',
            STALKER: 'STALKER',
            IMMORTAL: 'IMMORTAL',
        }

        self.distance_timer = 0.675 # Time between distance checks
        self.timer__ = 0

        self.leader = None
        self.soldiers = {}
        self.attacking = False
        self.attack_target = None
        self.first_attack = True

    def init(self):
        self.map_center = self.bot.game_info.map_center

    async def step(self):
        self.auto_recuiter()
        await self.update_soldier()
        self.update_leader()

    def auto_recuiter(self):
        if not self.auto_recuit:
            return

        for unit_type in self.units_available_for_attack.keys():
            for unit in self.bot.units(unit_type).idle:
                if unit.tag not in self.soldiers:
                    self.add(unit.tag, {'state': 'new'})
                    if self.verbose:
                        print('   ->  Found new unit')

    def add(self, unit_tag, options={}):
        self.soldiers[unit_tag] = options

        if self.leader is None:
            self.leader = unit_tag

    def update_leader(self):
        if self.army_size() > 0:
            if self.leader not in self.soldiers:
                self.leader = next(iter(self.soldiers))

                if self.verbose:
                    print('%6.2f leader died, found new one' % (self.bot.time))
        else:
            self.leader = None

    def army_size(self):
        return len(self.soldiers)

    async def update_soldier(self):
        tags_to_delete = []

        leader_tag, leader_unit = self.get_updated_leader()

        send_attack = self.can_attack()

        for soldier_tag in self.soldiers:
            soldier_unit = self.bot.units.find_by_tag(soldier_tag)

            if soldier_unit is None:
                tags_to_delete.append(soldier_tag)
            else:
                info = self.soldiers[soldier_tag]

                if info['state'] == 'new':
                    await self.move_to_center(soldier_tag)
                elif info['state'] == 'moving_to_center':
                    await self.moving_to_center(soldier_tag)
                elif info['state'] == 'waiting_at_center':
                    if send_attack:
                        await self.send_attack(soldier_tag)
                elif info['state'] == 'attacking':
                    await self.micro_unit(soldier_tag)

        for tag in tags_to_delete:
            self.soldiers.pop(tag)

    def get_updated_leader(self):
        tag = self.leader
        unit = self.bot.units.find_by_tag(tag)

        return tag, unit

    def can_attack(self):
        if self.bot.time - self.timer__ >= self.distance_timer:
            timer__ = self.bot.time
            if self.bot.units.closer_than(self.attack_trigger_radius, self.map_center).amount >= self.minimum_army_size:
                return True

        return False

    async def move_to_center(self, unit_tag):
        unit = self.bot.units.find_by_tag(unit_tag)

        leader_tag, leader_unit = self.get_updated_leader()

        await self.bot.do(unit.attack(self.map_center))
        self.soldiers[unit_tag]['state'] = 'moving_to_center'
        self.soldiers[unit_tag]['distance_to_center_timer'] = self.bot.time

    async def moving_to_center(self, unit_tag):
        unit = self.bot.units.find_by_tag(unit_tag)

        if self.bot.time - self.soldiers[unit_tag]['distance_to_center_timer'] >= self.distance_timer:
            self.soldiers[unit_tag]['distance_to_center_timer'] = self.bot.time

            if unit.distance_to(self.map_center) < self.stop_radius:
                self.soldiers[unit_tag]['state'] = 'waiting_at_center'
                self.soldiers[unit_tag]['waiting_at_center_timer'] = self.bot.time
            else:
                await self.bot.do(unit.attack(self.map_center))

    async def send_attack(self, unit_tag):
        unit = self.bot.units.find_by_tag(unit_tag)

        if self.attack_target is None:
            self.attack_target = self.get_something_to_attack()

        await self.bot.do(unit.attack(self.attack_target))

        self.soldiers[unit_tag]['state'] = 'attacking'

    async def micro_unit(self, unit_tag):
        unit = self.bot.units.find_by_tag(unit_tag)
        if unit.is_idle:
            self.attack_target = self.get_something_to_attack()
            await self.bot.do(unit.attack(self.attack_target.position))

    def get_something_to_attack(self):
        if self.bot.known_enemy_units.amount > 0:
            return self.bot.known_enemy_units.random

        if self.bot.known_enemy_structures.amount > 0:
            return self.bot.known_enemy_structures.random

        if self.first_attack:
            self.first_attack = False
            return self.bot.enemy_start_locations[0]

        return random.sample(list(self.bot.expansion_locations), k=1)[0]
