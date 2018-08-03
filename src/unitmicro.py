class UnitMicro:
    def __init__(self, tag, unit_type, bot, scouting=False, defending=False):
        self.tag = tag
        self.unit_type = unit_type
        self.target = None
        self.scouting = scouting
        self.defending = defending
        self.attacking = not scouting and not defending
        self.bot = bot

        self.unit = bot.units.find_by_tag(tag)
        self.ground_range = self.unit.ground_range
        self.air_range = self.unit.air_range
        self.sight_range = self.unit.sight_range
        self.can_attack_air = self.unit.can_attack_air
        self.can_attack_ground = self.unit.can_attack_ground

    def update_target(self):
        if self.bot.units.find_by_tag(self.target) is None:
            target = None

            if self.bot.known_enemy_structures().amount == 0:
                near_units = self.bot.known_enemy_units().closer_than(self.ground_range, self.unit)
                if near_units.exists:
                    target = near_units.closest_to(self.unit)

            if self.bot.known_enemy_units().amount > 0:
                near_structures = self.bot.known_enemy_structures().closer_than(self.ground_range, self.unit)
                if near_structures.exists:
                    target = near_structures.closest_to(self.unit)

            self.target = target

    def get_target(self):
        return self.target

    def alive(self):
        self.unit = self.bot.units.find_by_tag(self.tag)
        return True if self.unit is not None else False

    async def update(self):
        if self.alive():
            self.update_target()

            if self.target is not None:
                await self.bot.do(self.unit.attack(self.target))
