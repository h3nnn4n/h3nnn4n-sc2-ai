import random

from sc2.constants import ZEALOT, STALKER, NEXUS, GATEWAY, CYBERNETICSCORE, PYLON, PROBE, ASSIMILATOR


class Order:
    def __init__(self, bot=None, requires=None, build=None, build_at=None):
        self.bot = bot
        self.requires = requires
        self.build = build
        self.build_at = build_at

    def can_build(self, bot):
        bot = self.bot if self.bot is not None else bot

        return self.requires(bot)

    async def execute(self, bot):
        bot = self.bot if self.bot is not None else bot
        unit = self.build
        if not bot.can_afford(unit):
            return

        if self.build_at is not None:
            build_at = bot.units(self.build_at).ready.noqueue

            if build_at:
                await bot.do(build_at.random.train(unit))
        else:
            if unit == PYLON:
                nexus = bot.units(NEXUS).ready.random
                pos = bot.start_location.towards(bot.game_info.map_center, random.randrange(6, 16))
                await bot.build(PYLON, near=pos)
            elif unit == ASSIMILATOR:
                for nexus in bot.units(NEXUS).ready:
                    vgs = bot.state.vespene_geyser.closer_than(20.0, nexus)
                    for vg in vgs:
                        if not bot.can_afford(ASSIMILATOR):
                            break

                        worker = bot.select_build_worker(vg.position)
                        if worker is None:
                            break

                        if not bot.units(ASSIMILATOR).closer_than(1.0, vg).exists:
                            await bot.do(worker.build(ASSIMILATOR, vg))
                            break
            else:
                pylon = bot.units(PYLON).ready
                if pylon:
                    await bot.build(unit, near=pylon.random)


class BuildOrder:
    def __init__(self, bot=None, verbose=False):
        self.units = [ZEALOT, STALKER]
        self.buildings = [NEXUS, PYLON, GATEWAY, CYBERNETICSCORE]
        self.upgrades = []

        self.build_order = []

        self.bot = bot
        self.verbose = verbose

        self.build_at = {}

        self.build_at[PROBE] = NEXUS

    def add(self, order):
        self.build_order.append(order)

    async def do_next_action(self):
        bot = self.bot
        pass

    async def build(self, to_build):
        bot = self.bot
        pass
