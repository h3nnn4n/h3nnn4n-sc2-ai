from patch_path import patch_path
patch_path()
import sys
import sc2
from __init__ import run_ladder_game
from sc2 import Race, Difficulty
from sc2.player import Bot, Computer
from TapiocaBot import TapiocaBot


if __name__ == '__main__':
    bot = Bot(Race.Protoss, TapiocaBot())

    if "--LadderServer" in sys.argv:
        print("Starting ladder game...")
        run_ladder_game(bot)
    else:
        print("Starting local game...")
        sc2.run_game(sc2.maps.get("Abyssal Reef LE"), [
            bot,
            Computer(Race.Protoss, Difficulty.Easy)
        ], realtime=False)
