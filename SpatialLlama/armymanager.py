from unitmicro import UnitMicro
from random import sample


class ArmyManager:
    def __init__(self, bot=None):
        self.bot = bot
        self.verbose = True

        self.soldiers = {}
        self.leader = None

        self.map_center = None

        self.group_wait_for_n_units = 0
        self.group_timeout = 0
        self.group_timer = 0
        self.move_towards_position = None
        self.move_towards_on_next_step = False
        self.waiting_for_group = False
        self.group_timeout_counting = False
        self.radius_for_regroup = 10

        self.actions_for_next_step = []

    def init(self):
        self.map_center = self.bot.game_info.map_center

    def add(self, unit_tag, options={}):
        self.soldiers[unit_tag] = options

        if self.leader is None:
            self.leader = unit_tag

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
                if 'reinforcement' in self.soldiers[soldier_tag].keys() and leader_unit is not None:
                    self.actions_for_next_step.append(soldier_unit.attack(leader_unit.position))
                    self.soldiers[soldier_tag].pop('reinforcement')

                if soldier_unit.is_idle:
                    leader_tag = self.leader
                    leader_unit = self.bot.units.find_by_tag(leader_tag)

                    if leader_unit is None:
                        continue

                    if soldier_tag != leader_tag:
                        self.actions_for_next_step.append(soldier_unit.attack(leader_unit.position))
                    else:
                        self.actions_for_next_step.append(soldier_unit.attack(self.get_something_to_attack()))

        for tag in tags_to_delete:
            self.soldiers.pop(tag)

    def get_something_to_attack(self):
        if self.bot.known_enemy_units.amount > 0:
            return self.bot.known_enemy_units.random

        if self.bot.known_enemy_structures.amount > 0:
            return self.bot.known_enemy_structures.random

        return sample(list(self.bot.expansion_locations), k=1)[0]

    def update_leader(self):
        self.update_soldier_status()

        if self.army_size() > 0:
            if self.leader not in self.soldiers:
                self.leader = next(iter(self.soldiers))

                if self.verbose:
                    print('%6.2f leader died, found new one' % (self.bot.time))
        else:
            self.leader = None

    def finished_regrouping(self):
        if not self.waiting_for_group:
            return False

        self.update_leader()

        leader_unit = self.bot.units.find_by_tag(self.leader)
        if leader_unit is not None and leader_unit.distance_to(self.map_center) < self.radius_for_regroup:
            if not self.group_timeout_counting:
                self.group_timeout_counting = True
                self.group_timer = self.bot.time

            near_units = self.bot.units.closer_than(self.radius_for_regroup, leader_unit)

            if near_units.amount >= self.group_wait_for_n_units:
                self.waiting_for_group = False
                return True

            if self.bot.time - self.group_timer > self.group_timeout:
                if self.verbose:
                    print('%6.2f grouping timeout of %d secs triggered with %d units present, expected %d' %
                          (self.bot.time, self.group_timeout, near_units.amount, self.group_wait_for_n_units))
                self.waiting_for_group = False
                return True

        return False

    async def group_at_map_center(self, wait_for_n_units=0, timeout=0, move_towards_position=None):
        self.group_wait_for_n_units = wait_for_n_units
        self.group_timeout = timeout
        self.move_towards_position = move_towards_position
        self.move_towards_on_next_step = True
        self.waiting_for_group = True
        self.group_timeout_counting = False

    async def step(self):
        self.update_soldier_status()
        self.update_leader()

        actions = []

        if self.move_towards_on_next_step:
            if self.verbose:
                print('%6.2f moving towards map_center' % (self.bot.time))

            self.move_towards_on_next_step = False
            if self.move_towards_position is not None:
                for soldier in self.soldiers:
                    soldier_unit = self.bot.units.find_by_tag(soldier)
                    if soldier_unit is not None:
                        actions.append(soldier_unit.attack(self.map_center))
        elif self.finished_regrouping():
            if self.verbose:
                print('%6.2f moving towards attack location' % (self.bot.time))

            for soldier in self.soldiers:
                soldier_unit = self.bot.units.find_by_tag(soldier)
                if soldier_unit is not None:
                    actions.append(soldier_unit.attack(self.map_center))
                actions.append(soldier_unit.attack(self.move_towards_position))

        self.actions_for_next_step.extend(actions)

        await self.bot.do_actions(self.actions_for_next_step)

        self.actions_for_next_step = []
