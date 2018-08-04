from unitmicro import UnitMicro


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

    def init(self):
        self.map_center = self.bot.game_info.map_center

    def add(self, unit_tag):
        self.soldiers[unit_tag] = self.bot.units.find_by_tag(unit_tag)
        if self.leader is None:
            self.leader = unit_tag

    def update_soldier_status(self):
        tags_to_delete = []

        for soldier_tag in self.soldiers:
            soldier_unit = self.bot.units.find_by_tag(soldier)

            if soldier_unit is None:
                tags_to_delete.append(soldier_tag)
            else:
                self.soldiers[soldier_tag] = self.bot.get_unit_info(soldier_unit, field='all')

        for tag in tags_to_delete:
            self.soldiers.pop(tag)

    def get_leader(self):
        self.update_soldier_status()

        if self.leader not in self.soldiers:         # If leader died then
            self.leader = next(iter(self.soldiers))  # this picks the "first" unit as a leader

    def finished_regrouping(self):
        if not self.waiting_for_group:
            return False

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
                          (self.bot.time, self.group_timeout, self.near_units.amount, self.group_wait_for_n_units))
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

        await self.bot.do_actions(actions)
