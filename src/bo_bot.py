import random

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer

from build_order import BuildOrder, Order


class MadUpsideDownLlama_bo(sc2.BotAI):
    def __init__(self):
        self.verbose = True

    async def on_step(self, iteration):
        if iteration == 0:
            await self.chat_send("(glhf)")

            self.build_order = BuildOrder(bot=self, verbose=self.verbose)

            await self.build_order.add(Order(  # Build probes to fully saturate
                build={'unit': [(PROBE, 1)]},
                until={'unit': [(PROBE, 22)]}))

            await self.build_order.add(Order(  # Build first pylon
                wait_for={'unit': [(PROBE, 12)]},
                build={'structure': [(PYLON, 1)]}))

            await self.build_order.add(Order(   # Build first gateway
                wait_for={'structure': [(PYLON, 1)], 'unit': [(PROBE, 16)]},
                build={'structure': [(GATEWAY, 1)]}))

            #await self.build_order.add(Order(   # Build Cybernetics core
                #wait_for={'structure': [(GATEWAY, 1)]},
                #build={'structure': [(CYBERNETICSCORE)]}))

        if iteration % 50 == 0:
            await self.chat_send("running bo logic")
            await self.build_order.do_next_action()


def main():
    sc2.run_game(sc2.maps.get("Abyssal Reef LE"), [
        Bot(Race.Protoss, MadUpsideDownLlama_bo()),
        Computer(Race.Protoss, Difficulty.Medium)
    ], realtime=True)

if __name__ == '__main__':
    main()
