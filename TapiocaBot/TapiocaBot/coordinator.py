from sc2.ids.unit_typeid import UnitTypeId


class Coordinator:
    def __init__(self, bot=None, verbose=False):
        self.bot = bot
        self.verbose = verbose

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

    def is_this_the_research_priority(self, what):
        return self.research_priority == what

    def on_start(self):
        pass

    async def step(self):
        self.check_if_early_game_ended()

    def check_if_early_game_ended(self):
        if self.bot.build_order_controller.did_early_game_just_end():
            if self.verbose:
                print('             Early game finished')
                print('             Enabling more stuff')

            self.bot.event_manager.add_event(self.bot.building_controller.manage_supply, 1)
            self.bot.event_manager.add_event(self.bot.building_controller.expansion_controller, 5)
            self.bot.event_manager.add_event(self.bot.building_controller.build_nexus, 5)
            # self.event_manager.add_event(self.scouting_controller.step, 10)
            self.bot.event_manager.add_event(self.bot.building_controller.step, 2)
            self.bot.event_manager.add_event(self.bot.upgrades_controller.step, 5)

            # Gateway stuff
            self.bot.event_manager.add_event(self.bot.gateway_controller.step, 1.0)
            self.bot.gateway_controller.add_order((UnitTypeId.STALKER, 2))
            self.bot.gateway_controller.add_order((UnitTypeId.ZEALOT, 1))

            # Robo stuff
            self.bot.event_manager.add_event(self.bot.robotics_facility_controller.step, 1.0)

            self.bot.robotics_facility_controller.on_idle_build = UnitTypeId.IMMORTAL
