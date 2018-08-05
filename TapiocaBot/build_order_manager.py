from two_gate_fast_expand import TwoGateFastExpand


class BuildOrderManager:
    def __init__(self, build_order=None, bot=None, verbose=False):
        self.current_build_order = build_order
        self.bot = bot
        self.verbose = verbose

        self.build_orders = {
            'two_gate_fast_expand': TwoGateFastExpand(bot=bot, verbose=verbose)
        }

    async def step(self):
        await self.build_orders[self.current_build_order]()
