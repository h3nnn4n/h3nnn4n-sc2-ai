from sc2.ids.unit_typeid import UnitTypeId


class Coordinator:
    def __init__(self, bot=None, verbose=False, build_order=None):
        self.bot = bot
        self.verbose = verbose
        self.build_order = build_order

        self.priority = None

        self.expand_timeout = 30
        self.expand_timer = 0

        self.prioritize_robo_units = True

        self.research_priority = None

        self.strategy = 'three_gate_blink_stalker_all_in'

        self.bot.build_order_controller.current_build_order = build_order

        self.strategy_map = {
            'three_gate_blink_stalker_all_in': self.three_gate_blink_stalker_all_in,
            'two_gate_fe_into_zealot_immortal': self.two_gate_fe_into_zealot_immortal
        }

    def new_priority(self, what, research_priority=None):
        self.priority = what
        self.research_priority = research_priority

        if what == 'expand':
            self.expand_timer = self.bot.time

    def can(self, what):
        no_priority = self.priority is None
        if what == 'expand':
            return self.priority == 'expand'

        if what == 'build':
            return no_priority

        if what == 'build_gateway_units':
            robo_idle = self.bot.units(UnitTypeId.ROBOTICSFACILITY).ready.noqueue.amount > 0

            '''
                i p =
                0 0 1
                0 1 1
                1 0 1
                1 1 0
            '''

            return no_priority and (not robo_idle or not self.prioritize_robo_units)

        if what == 'build_robotics_facility_units':
            return no_priority

        if what == 'research':
            return no_priority or self.priority == 'research'

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

            self.strategy_map[self.strategy]()

    def two_gate_fe_into_zealot_immortal(self):
        self.bot.event_manager.add_event(self.bot.building_controller.manage_supply, 1)
        self.bot.event_manager.add_event(self.bot.building_controller.expansion_controller, 5)
        self.bot.event_manager.add_event(self.bot.building_controller.build_nexus, 5)
        # self.event_manager.add_event(self.scouting_controller.step, 10)
        self.bot.event_manager.add_event(self.bot.building_controller.step, 2)
        self.bot.event_manager.add_event(self.bot.upgrades_controller.step, 5)

        # Gateway stuff
        self.bot.event_manager.add_event(self.bot.gateway_controller.step, 1.0)
        self.bot.gateway_controller.add_order((UnitTypeId.ZEALOT, 2))

        # Robo stuff
        self.bot.event_manager.add_event(self.bot.robotics_facility_controller.step, 1.0)

        self.bot.robotics_facility_controller.on_idle_build = UnitTypeId.IMMORTAL

    def three_gate_blink_stalker_all_in(self):
        self.bot.event_manager.add_event(self.bot.building_controller.manage_supply, 1)
        self.bot.event_manager.add_event(self.bot.building_controller.step_auto_build_gateways, 2)
        self.bot.building_controller.gateways_per_nexus = 3

        self.bot.event_manager.add_event(self.bot.gateway_controller.step, 1)
        self.bot.gateway_controller.add_order((UnitTypeId.STALKER, 1))

        self.bot.event_manager.add_event(self.bot.upgrades_controller.step, 1)
        self.bot.upgrades_controller.enable_twilight = True
        self.bot.upgrades_controller.twilight_council_research_priority.append('blink')

        self.bot.army_controller.minimum_army_size = 1  # 10
        self.bot.army_controller.units_available_for_attack = {
            UnitTypeId.STALKER: 'STALKER'
        }
