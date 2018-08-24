class UnitAiController:
    def __init__(self, bot=None, verbose=False):
        self.bot = bot
        self.verbose = verbose

        self.first_iteration = True

    async def step(self, unit_tag):
        if not hasattr(self, '_first_iteration_passed'):
            self.prepare_first_step(unit_tag)
            self._first_iteration_passed = False
            print('prepare first step')
        else:
            self.after_action(unit_tag)
            self.end_step(unit_tag)

        self.prepare_step(unit_tag)
        return self.before_action(unit_tag)

    def prepare_step(self, unit_tag):
        pass

    def before_action(self, unit_tag):
        pass

    def after_action(self, unit_tag):
        pass

    def end_step(self, unit_tag):
        pass

    def prepare_first_step(self, unit_tag):
        pass
