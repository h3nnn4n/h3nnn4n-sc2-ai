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

        self.leader = None
        self.soldiers = {}
        self.attacking = False

        self.actions_for_next_step = []

    def init(self):
        self.map_center = self.bot.game_info.map_center

    async def step(self):
        actions = []

        self.update_soldier_status()
        self.update_leader()
        self.auto_recuiter()

        self.actions_for_next_step.extend(actions)
        await self.bot.do_actions(self.actions_for_next_step)
        self.actions_for_next_step = []

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

    def update_soldier_status(self):
        tags_to_delete = []

        leader_tag = self.leader
        leader_unit = self.bot.units.find_by_tag(leader_tag)

        for soldier_tag in self.soldiers:
            soldier_unit = self.bot.units.find_by_tag(soldier_tag)

            if soldier_unit is None:
                tags_to_delete.append(soldier_tag)
            else:
                info = self.soldiers[soldier_tag]

                if info['state'] == 'new' and leader_tag != soldier_tag:
                    self.actions_for_next_step.append(soldier_unit.move(leader_unit.position))
                    self.soldiers[soldier_tag]['state'] = 'waiting'

        for tag in tags_to_delete:
            self.soldiers.pop(tag)
