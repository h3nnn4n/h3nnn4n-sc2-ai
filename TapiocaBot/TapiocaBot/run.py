# pylint: disable=C0301

import sys
import sc2
from ladder import run_ladder_game
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
    '(2)RedshiftLE'
]

races = [
    Race.Protoss,
    Race.Terran,
    Race.Zerg
]

difficulties = [
    Difficulty.VeryEasy,
    Difficulty.Easy,
    Difficulty.Medium,
    Difficulty.MediumHard,
    Difficulty.Hard,
    Difficulty.Harder,
    Difficulty.VeryHard,
    Difficulty.CheatVision,
    Difficulty.CheatMoney,
    Difficulty.CheatInsane
]

selected_map = maps[2]
race = races[2]
difficulty = difficulties[5]


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
            Computer(race, difficulty)
        ], realtime=False)
