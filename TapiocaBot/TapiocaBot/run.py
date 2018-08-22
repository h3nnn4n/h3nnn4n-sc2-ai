# pylint: disable=C0301,E1102

from patch_path import patch_path  # Use local version
patch_path()
import sys
import sc2
from sc2 import Race, Difficulty
from sc2.player import Bot, Computer
from TapiocaBot import TapiocaBot
from ladder import run_ladder_game
from random import sample


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

selected_map = 'StalkerVsRoaches Narrow'
race = Race.Zerg
difficulty = Difficulty.VeryHard


if __name__ == '__main__':
    if "--LadderServer" in sys.argv:
        tapioca = TapiocaBot()
        bot = Bot(Race.Protoss, tapioca)
        print("Starting ladder game...")
        run_ladder_game(bot)
    else:
        print("Starting local game...")
        tapioca = TapiocaBot(verbose=True, visual_debug=True)
        bot = Bot(Race.Protoss, tapioca)
        sc2.run_game(sc2.maps.get(selected_map), [
            bot,
            Computer(race, difficulty)
        ], realtime=False)
