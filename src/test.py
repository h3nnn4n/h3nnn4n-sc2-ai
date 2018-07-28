import random

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer


class MadUpsideDownLlama(sc2.BotAI):
    def __init__(self):
        self.plan = []

    async def build_workers(self):
        nexus = self.units(NEXUS).first

        if self.workers.amount < self.units(NEXUS).amount*22 and nexus.noqueue:
            if self.can_afford(PROBE):
                await self.do(nexus.train(PROBE))

    async def manage_supply(self):
        nexus = self.units(NEXUS).first

        if self.supply_left < 2 and not self.already_pending(PYLON):
            if self.can_afford(PYLON):
                pos = self.start_location.towards(self.game_info.map_center, random.randrange(8, 15))
                await self.build(PYLON, near=pos)

    async def build_vespene(self):
        if self.workers.amount < 16:
            return

        for nexus in self.units(NEXUS).ready:
            vgs = self.state.vespene_geyser.closer_than(20.0, nexus)
            for vg in vgs:
                if not self.can_afford(ASSIMILATOR):
                    break

                worker = self.select_build_worker(vg.position)
                if worker is None:
                    break

                if not self.units(ASSIMILATOR).closer_than(1.0, vg).exists:
                    await self.do(worker.build(ASSIMILATOR, vg))

    async def on_step(self, iteration):
        if iteration == 0:
            await self.chat_send("(hlhf)")

        await self.distribute_workers()
        await self.build_workers()
        await self.manage_supply()
        await self.build_vespene()


def main():
    sc2.run_game(sc2.maps.get("Simple64"), [
        Bot(Race.Protoss, MadUpsideDownLlama()),
        Computer(Race.Protoss, Difficulty.Easy)
    ], realtime=True)

if __name__ == '__main__':
    main()
