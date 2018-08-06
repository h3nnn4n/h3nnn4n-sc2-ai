from sc2.constants import ROBOTICSFACILITY
from collections import deque


class RoboticsFacilitiyController:
    def __init__(self, bot=None, verbose=False, auto_pick=False,
                 can_idle=False, on_idle_build=None):
        self.verbose = verbose
        self.bot = bot
        self.auto_pick = True
        self.can_idle = can_idle
        self.on_idle_build = on_idle_build

        self.pending = deque()

    async def step(self):
        robos = self.bot.units(ROBOTICSFACILITY).ready.noqueue

        for robo in robos:
            next_unit = self.get_next_unit()

            if next_unit is None:
                return

            if self.bot.can_afford(next_unit):
                await self.bot.do(robo.train(next_unit))
                self.queue_step()
                if self.verbose:
                    print('%8.2f %3d Building %s' % (
                        self.bot.time, self.bot.supply_used, next_unit))

    def add_order(self, unit):
        self.pending.append(unit)

    def get_next_unit(self):
        if len(self.pending) == 0:
            if self.can_idle:
                return self.on_idle_build
            else:
                return None
        else:
            return self.pending[0]

    def queue_step(self):
        self.pending.popleft()