import sys
import sc2
from __init__ import run_ladder_game
from sc2 import Race, Difficulty
from sc2.player import Bot, Computer
from TapiocaBot import TapiocaBot


maps = [
    '(2)16-BitLE',
    '(2)CatalystLE',
    '(2)LostandFoundLE',
    '(4)DarknessSanctuaryLE',
    '(2)AcidPlantLE',
    '(2)DreamcatcherLE',
    '(2)RedshiftLE',
    'AbyssalReefLE',
    'AbiogenesisLE',
    'BackwaterLE',
    'CatalystLE',
    'NeonVioletSquareLE',
    'AcidPlantLE',
    'BlackpinkLE',
    'EastwatchLE',
]

selected_map = maps[2]


if __name__ == '__main__':
    if "--LadderServer" in sys.argv:
        bot = Bot(Race.Protoss, TapiocaBot())
        print("Starting ladder game...")
        run_ladder_game(bot)
    else:
        print("Starting local game...")
        bot = Bot(Race.Protoss, TapiocaBot(verbose=True, visual_debug=True))
        sc2.run_game(sc2.maps.get(selected_map), [
            bot,
            Computer(Race.Protoss, Difficulty.VeryHard)
        ], realtime=False)
