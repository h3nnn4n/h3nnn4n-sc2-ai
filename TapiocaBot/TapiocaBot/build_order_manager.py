# pylint: disable=E0401
# Annoying false positive

from two_gate_fast_expand import TwoGateFastExpand


class BuildOrderManager:
    def __init__(self, build_order=None, bot=None, verbose=False):
        self.current_build_order = build_order
        self.bot = bot
        self.verbose = verbose
        self.finished_early_game = False

        self.build_orders = {
            'two_gate_fast_expand': TwoGateFastExpand(bot=bot, verbose=verbose)
        }

    async def step(self):
        await self.build_orders[self.current_build_order]()

    def did_early_game_just_end(self):
        finished = False
        finished_early_game = self.build_orders[self.current_build_order].finished

        if not self.finished_early_game and finished_early_game:
            if self.verbose:
                print('%8.2f %3d Finished basic Build Order Phase' % (self.bot.time, self.bot.supply_used))
                print('\n------------------------\n')
            finished = True

        self.finished_early_game = finished_early_game

        return finished

    def is_early_game_over(self):
        return self.finished_early_game
