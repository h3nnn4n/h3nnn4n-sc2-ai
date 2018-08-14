class Coordinator:
    def __init__(self, bot=None):
        self.bot = bot
        self.priority = None

        self.expand_timeout = 30
        self.expand_timer = 0

        self.research_priority = None

    def new_priority(self, what, research_priority=None):
        self.priority = what
        self.research_priority = research_priority

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

        if what == 'research':
            return self.priority is None or self.priority == 'research'

    def is_this_the_researcg_priority(self, what):
        return self.research_priority == what

    async def step(self):
        return
