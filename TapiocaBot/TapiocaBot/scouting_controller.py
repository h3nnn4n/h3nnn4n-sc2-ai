import random
from sc2.ids.unit_typeid import UnitTypeId


class ScoutingController:
    def __init__(self, bot=None, verbose=False):
        self.bot = bot
        self.verbose = verbose

        self.scouting_units = set()
        self.number_of_scouting_units = 3
        self.scout_interval = 30  # Seconds
        self.scout_timer = 0

    async def step(self):
        current_time = self.bot.time
        if current_time - self.scout_timer > self.scout_interval:
            self.scout_timer = self.bot.time

            n_scouting_units_assigned = len(self.scouting_units)
            missing_scouting_units = self.number_of_scouting_units - n_scouting_units_assigned

            # Uses the previous assigned scouting units to keep scouting
            for scouting_unit_tag in list(self.scouting_units):
                unit = self.bot.units.find_by_tag(scouting_unit_tag)

                if unit is not None:
                    target = random.sample(list(self.bot.expansion_locations), k=1)[0]
                    await self.bot.do(unit.attack(target))
                else:
                    # If a scouting unit isnt found then it is (most likely) dead
                    # and we need another to replace it
                    self.scouting_units.remove(unit)
                    missing_scouting_units += 1

            if missing_scouting_units > 0:
                idle_stalkers = self.bot.units(UnitTypeId.STALKER).idle

                if idle_stalkers.exists:
                    if self.verbose:
                        print('%6.2f Scouting' % (self.bot.time))

                    # If there is no unit assigned to scouting
                    # the the idle unit furthest from the base
                    for _ in range(missing_scouting_units):
                        if self.bot.units(UnitTypeId.NEXUS).amount > 0:
                            stalker = idle_stalkers.furthest_to(self.bot.units(UnitTypeId.NEXUS).first)
                        else:
                            stalker = idle_stalkers.random

                        if stalker:
                            target = random.sample(list(self.bot.expansion_locations), k=1)[0]
                            await self.bot.do(stalker.attack(target))
                            self.scouting_units

                        idle_stalkers = self.bot.units(UnitTypeId.STALKER).idle
                        if not idle_stalkers.exists:
                            break
                else:
                    pass
