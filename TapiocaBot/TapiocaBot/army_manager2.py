from sc2.constants import *


class ArmyManager:
    def __init__(self, bot=None, verbose=False):
        self.bot = bot
        self.verbose = verbose

        self.auto_recuit = True
        self.minimum_army_size = 15
        self.units_available_for_attack = {
            ZEALOT: 'ZEALOT',
            ADEPT: 'ADEPT',
            SENTRY: 'SENTRY',
            STALKER: 'STALKER',
            IMMORTAL: 'IMMORTAL',
        }

        self.distance_timer = 0.675 # Time between distance checks

        self.leader = None
        self.soldiers = {}
        self.attacking = False

    def init(self):
        self.map_center = self.bot.game_info.map_center

    async def step(self):
        self.auto_recuiter()
        self.update_soldier()
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

    def update_soldier(self):
        tags_to_delete = []

        leader_tag, leader_unit = self.get_updated_leader()

        for soldier_tag in self.soldiers:
            soldier_unit = self.bot.units.find_by_tag(soldier_tag)

            if soldier_unit is None:
                tags_to_delete.append(soldier_tag)
            else:
                info = self.soldiers[soldier_tag]

                if info['state'] == 'new':
                    self.move_to_center(soldier_tag)
                elif info['state'] == 'moving_to_center':
                    self.waiting_at_center(soldier_tag)
                elif info['state'] == 'waiting_at_center':
                    pass

        for tag in tags_to_delete:
            self.soldiers.pop(tag)

    def get_updated_leader(self):
        tag = self.leader
        unit = self.bot.units.find_by_tag(tag)

        return tag, unit

    def move_to_center(self, unit_tag):
        unit = self.bot.units.find_by_tag(unit_tag)

        leader_tag, leader_unit = self.get_updated_leader()

        self.bot.do(unit.move(self.map_center))
        self.soldiers[unit_tag]['state'] = 'moving_to_center'
        self.soldiers[unit_tag]['distance_to_center_timer'] = self.bot.time

    def waiting_at_center(self, unit_tag):
        unit = self.bot.units.find_by_tag(unit_tag)

        if self.bot.time - self.soldiers[unit_tag]['distance_to_center_timer'] >= self.distance_timer:
            self.soldiers[unit_tag]['distance_to_center_timer'] = self.bot.time

            if unit.distance_to(self.map_center) < 3:
                self.soldiers[unit_tag]['state'] = 'waiting_at_center'
