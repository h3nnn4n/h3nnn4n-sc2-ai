import random

from sc2.constants import ZEALOT, STALKER, NEXUS, GATEWAY, CYBERNETICSCORE, PYLON, PROBE


class Order:
    def __init__(self, wait_for={}, build={}, until={}):
        self.wait_for = wait_for
        self.build = build
        self.until = until

        self.completed = False


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

    async def add(self, order):
        if self.bot and self.verbose:
            if order.wait_for:
                await self.bot.chat_send('add %s when %s' % (order.build, order.wait_for))
            elif order.until:
                await self.bot.chat_send('add %s when %s' % (order.build, order.until))
        self.build_order.append(order)

    async def do_next_action(self):
        bot = self.bot

        for order in self.build_order:
            if order.completed:
                continue

            wait_for = order.wait_for
            build = order.build
            until = order.until

            wait_for_satisfied = True
            until_satisfied = True

            for unit_type, units in wait_for.items():
                for unit, count in units:
                    amount = bot.units(unit).ready.amount
                    if amount != count:
                        wait_for_satisfied = False
                        break

            for unit_type, units in until.items():
                for unit, count in units:
                    if bot.units(unit).ready.amount > count:
                        until_satisfied = False
                        break

            if wait_for_satisfied and until_satisfied:
                await self.bot.chat_send('doing %s' % (order.build))
                await self.build(build)

    async def build(self, to_build):
        bot = self.bot

        for unit_type, todo in to_build.items():
            if unit_type == 'unit':
                for to_build, count in todo:
                    where = self.build_at[to_build]
                    for c in range(count):
                        possible_places = bot.units(where).ready.noqueue
                        if possible_places:
                            await bot.do(possible_places.random.train(to_build))
            elif unit_type == 'structure':
                for to_build, count in todo:
                    if bot.can_afford(to_build):
                        if to_build == PYLON:
                            if random.random() < 0.5:
                                pos = bot.start_location.towards(bot.game_info.map_center, random.randrange(6, 12))
                                await bot.build(PYLON, near=pos)
                            else:
                                await bot.build(PYLON, near=bot.units(NEXUS).ready.random)
                        else:
                            pylon = bot.units(PYLON).ready.random
                            await bot.build(to_build, near=pylon)
                            to_build.completed = True
            elif unit_type == 'upgrade':
                pass
