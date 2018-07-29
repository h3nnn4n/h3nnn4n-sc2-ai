import random

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer

from build_order import BuildOrder, Order

from conditions import *


class MadUpsideDownLlama_bo(sc2.BotAI):
    def __init__(self):
        self.verbose = True

    async def on_step(self, iteration):
        if iteration == 0:
            await self.chat_send("(glhf)")

            self.orders = [
                Order(  # Build probes to fully saturate
                    requires=unit_count_less_than(PROBE, 18, include_pending=True),
                    build=PROBE,
                    build_at=NEXUS
                ),
                Order(  # Build first pylon
                    requires=unit_count_less_than(PYLON, 1, include_pending=True),
                    build=PYLON
                ),
                Order(  # Build first gateway
                    requires=all_of(unit_count_less_than(GATEWAY, 1, include_pending=True), unit_count(PYLON, 1)),
                    build=GATEWAY
                ),
                Order(  # Build cybernetics core
                    requires=all_of(unit_count_less_than(CYBERNETICSCORE, 1, include_pending=True), unit_count_at_least(GATEWAY, 1, include_pending=True)),
                    build=CYBERNETICSCORE
                ),
                Order(  # Build 3 more gateways
                    requires=all_of(unit_count(CYBERNETICSCORE, 1, include_pending=True), unit_count_less_than(GATEWAY, 4, include_pending=True)),
                    build=GATEWAY
                ),
                Order(  # Build 3 more pylons
                    requires=all_of(unit_count(CYBERNETICSCORE, 1, include_pending=True), unit_count_less_than(PYLON, 3, include_pending=True)),
                    build=PYLON
                ),
            ]

        if iteration % 25 == 0:
            for order in self.orders:
                if order.can_build(self):
                    if self.can_afford(order.build):
                        await self.chat_send("can build and afford")
                        await order.execute(self)
                    else:
                        pass


def main():
    sc2.run_game(sc2.maps.get("Abyssal Reef LE"), [
        Bot(Race.Protoss, MadUpsideDownLlama_bo()),
        Computer(Race.Protoss, Difficulty.Medium)
    ], realtime=False, step_time_limit=2.0)

if __name__ == '__main__':
    main()
