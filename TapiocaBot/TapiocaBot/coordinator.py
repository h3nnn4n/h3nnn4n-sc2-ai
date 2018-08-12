class Coordinator:
    def __init__(self, bot=None):
        self.bot = bot
        self.priority = None

        self.expand_timeout = 30
        self.expand_timer = 0

    def new_priority(self, what):
        self.priority = what

        if what == 'expand':
            self.expand_timer = self.bot.time

    def can(self, what):
        if what == 'expand':
            return self.priority == 'expand'

        if what == 'build':
            return self.priority is None

        if what == 'build_gateway_units':
            return self.priority is None

        if what == 'build_robotics_facility_units':
            return self.priority is None

    async def step(self):
        return
