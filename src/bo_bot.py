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
                    requires=unit_count_less_than(PROBE, 22, include_pending=True),
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
                Order(  # Build 2 assimilators
                    requires=all_of(unit_count(CYBERNETICSCORE, 1, include_pending=True)),
                    build=ASSIMILATOR
                ),
                Order(  # Build 3 more gateways
                    requires=all_of(unit_count(CYBERNETICSCORE, 1, include_pending=True), unit_count_less_than(GATEWAY, 4, include_pending=True)),
                    build=GATEWAY
                ),
                Order(  # Build 3 more pylons
                    requires=all_of(unit_count(CYBERNETICSCORE, 1, include_pending=True), unit_count_less_than(PYLON, 3, include_pending=True)),
                    build=PYLON
                ),
                Order(  # Build 8 stalkers when the cybernetics core is ready
                    requires=all_of(unit_count(CYBERNETICSCORE, 1), unit_count_less_than(STALKER, 8)),
                    build=STALKER,
                    build_at=GATEWAY
                ),
            ]

        if iteration % 25 == 0:
            for order in self.orders:
                if order.can_build(self):
                    if self.can_afford(order.build):
                        await order.execute(self)
                    else:
                        pass

        if iteration % 50 == 0:
            await self.distribute_workers()

        if iteration % 50 == 0:
            await self.attack(iteration)

    async def attack(self, iteration):
        zealots = self.units(ZEALOT).idle
        stalkers = self.units(STALKER).idle
        total_units = zealots.amount + stalkers.amount

        if total_units >= 8:
            await self.chat_send('%f Attacking with %d units' % (self.time, total_units))

            for unit_group in [zealots, stalkers]:
                for unit in unit_group:
                    await self.do(unit.attack(self.select_target(self.state)))

    def select_target(self, state):
        if self.known_enemy_structures.exists:
            return random.choice(self.known_enemy_structures)

        return self.enemy_start_locations[0]


def main():
    sc2.run_game(sc2.maps.get("Abyssal Reef LE"), [
        Bot(Race.Protoss, MadUpsideDownLlama_bo()),
        Computer(Race.Protoss, Difficulty.Medium)
    ], realtime=False, step_time_limit=2.0)

if __name__ == '__main__':
    main()
