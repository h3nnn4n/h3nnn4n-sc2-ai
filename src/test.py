import random

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer


class MadUpsideDownLlama(sc2.BotAI):
    def __init__(self):
        self.plan = []
        self.verbose = True

    async def on_step(self, iteration):
        if iteration == 0:
            await self.chat_send("(glhf)")

        if iteration % 20 == 0:
            await self.distribute_workers()

        await self.build_workers()
        await self.manage_supply()
        await self.build_vespene()
        await self.build_structures()
        await self.build_army()

    async def build_army(self):
        for gateway in self.units(GATEWAY).ready.noqueue:
            abilities = await self.get_available_abilities(gateway)
            if AbilityId.GATEWAYTRAIN_STALKER in abilities:
                if self.can_afford(STALKER) and self.supply_left > 0:
                    await self.do(gateway.train(STALKER))
            elif AbilityId.GATEWAYTRAIN_ZEALOT in abilities:
                if self.can_afford(ZEALOT) and self.supply_left > 0:
                    await self.do(gateway.train(ZEALOT))

    async def build_structures(self):
        # Only start building main structures if there is
        # at least one pylon
        if not self.units(PYLON).ready.exists:
            return
        else:
            pylon = self.units(PYLON).ready.random

        # Build the first gateway
        if self.can_afford(GATEWAY) and self.units(WARPGATE).amount == 0 and self.units(GATEWAY).amount == 0:
            if self.verbose:
                await self.chat_send('starting first gateway')
            await self.build(GATEWAY, near=pylon)

        # Build the cybernetics core after the first gateway is ready
        if self.can_afford(CYBERNETICSCORE) and self.units(CYBERNETICSCORE).amount == 0 and self.units(GATEWAY).ready:
            if self.verbose:
                await self.chat_send('starting cybernetics')
            await self.build(CYBERNETICSCORE, near=pylon)

        # Build more gateways after the cybernetics core is ready
        if self.can_afford(GATEWAY) and self.units(WARPGATE).amount < 4 and self.units(GATEWAY).amount < 4 and self.units(CYBERNETICSCORE).ready:
            if self.verbose:
                await self.chat_send('building more gateways')
            await self.build(GATEWAY, near=pylon)

    async def build_workers(self):
        nexus = self.units(NEXUS).first

        if self.workers.amount < self.units(NEXUS).amount * 22 and nexus.noqueue:
            if self.can_afford(PROBE):
                await self.do(nexus.train(PROBE))

    async def manage_supply(self):
        nexus = self.units(NEXUS).ready.random

        if self.supply_left < 4 and not self.already_pending(PYLON):
            if self.can_afford(PYLON):
                if random.random() < 0.5:
                    pos = self.start_location.towards(self.game_info.map_center, random.randrange(6, 12))
                    await self.build(PYLON, near=pos)
                else:
                    await self.build(PYLON, near=nexus)

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


def main():
    sc2.run_game(sc2.maps.get("Simple64"), [
        Bot(Race.Protoss, MadUpsideDownLlama()),
        Computer(Race.Protoss, Difficulty.Easy)
    ], realtime=False)

if __name__ == '__main__':
    main()
