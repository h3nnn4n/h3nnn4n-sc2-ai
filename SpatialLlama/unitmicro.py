class UnitMicro:
    def __init__(self, tag, unit_type, bot, scouting=False, defending=False):
        self.tag = tag
        self.unit_type = unit_type
        self.target = None
        self.scouting = scouting
        self.defending = defending
        self.attacking = not scouting and not defending
        self.map_center = bot.game_info.map_center
        self.bot = bot

        self.moving_to_regroup = False
        self.regroup_timeout= None
        self.regroup_timer = 0
        self.wait_for_n_units = 0
        self.move_towards_position = None

        self.unit = bot.units.find_by_tag(tag)
        self.ground_range = self.unit.ground_range
        self.air_range = self.unit.air_range
        self.sight_range = self.unit.sight_range
        self.can_attack_air = self.unit.can_attack_air
        self.can_attack_ground = self.unit.can_attack_ground

    def update_target(self):
        return
        target = None

        # Try to attack a close unit
        if self.bot.units.find_by_tag(self.target) is None:
            if self.bot.known_enemy_structures().amount == 0:
                near_units = self.bot.known_enemy_units().closer_than(self.ground_range, self.unit)
                if near_units.exists:
                    target = near_units.closest_to(self.unit)

        # Otherwise tries to attack the closest structure
        if target is None:
            if self.bot.known_enemy_structures().exists:
                target = self.bot.known_enemy_structures().closest_to(self.unit)
                self.target = target

    def get_target(self):
        return self.target

    def alive(self):
        self.unit = self.bot.units.find_by_tag(self.tag)
        return True if self.unit is not None else False

    def move_towards(self, position):
        self.move_towards_position = position

    def finished_regrouping(self):
        near_units = self.bot.units.closer_than(10, self.unit)

        if near_units.amount > self.wait_for_n_units:
            return True

        if self.bot.time - self.regroup_timer > self.regroup_timeout:
            return True

        return False

    async def update(self):
        if self.alive():
            if self.moving_to_regroup:
                if self.finished_regrouping():
                    self.moving_to_regroup = False
                    await self.bot.do(self.unit.attack(self.move_towards_position))
            else:
                self.update_target()
                if self.target is not None:
                    await self.bot.do(self.unit.attack(self.target))

    async def group_at_map_center(self, wait_for_n_units=10, timeout=20):
        self.moving_to_regroup = True

        self.wait_for_n_units = wait_for_n_units
        self.regroup_timeout = timeout
        self.regroup_timer = self.bot.time

        await self.bot.do(self.unit.attack(self.map_center))
