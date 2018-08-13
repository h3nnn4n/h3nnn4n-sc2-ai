import numpy as np
import random
import sys
import sc2
from sc2 import Race, Difficulty

from sc2.player import Bot, Computer
from sc2.unit import Unit
from sc2.units import Units
from sc2.position import Point2, Point3

# TODO:
# This should not be used here since the main class
# should have no logic
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.upgrade_id import UpgradeId
from sc2.ids.effect_id import EffectId

from event_manager import EventManager
from build_order_manager import BuildOrderManager
from robotics_facility_controller import RoboticsFacilitiyController
from gateway_controller import GatewayController
from scouting_controller import ScoutingController
from building_manager import BuildingManager
from upgrades_controller import UpgradesController

from coordinator import Coordinator

use_old_army_manager = False
if use_old_army_manager:
    from army_manager import ArmyManager
else:
    from army_manager2 import ArmyManager


class TapiocaBot(sc2.BotAI):
    def __init__(self, verbose=False, visual_debug=False):
        self.verbose = verbose
        self.visual_debug = visual_debug

        # Control Stuff
        self.researched_warpgate = False
        self.maximum_workers = 66

        # Managers and controllers
        self.army_manager = ArmyManager(bot=self, verbose=self.verbose)
        self.scouting_controller = ScoutingController(bot=self, verbose=self.verbose)
        self.upgrades_controller = UpgradesController(bot=self, verbose=self.verbose)
        self.robotics_facility_controller = RoboticsFacilitiyController(
            bot=self,
            verbose=self.verbose,
            on_idle_build=UnitTypeId.IMMORTAL
        )
        self.gateway_controller = GatewayController(bot=self, verbose=self.verbose, auto_morph_to_warpgate=True)
        self.building_manager = BuildingManager(bot=self, verbose=self.verbose)
        self.event_manager = EventManager()
        self.build_order_manager = BuildOrderManager(
            build_order='two_gate_fast_expand',
            verbose=self.verbose,
            bot=self
        )

        self.coordinator = Coordinator(bot=self)

        self.order_queue = []

    def on_start(self):
        self.army_manager.init()

        self.event_manager.add_event(self.distribute_workers, 10)
        self.event_manager.add_event(self.handle_idle_workers, 0.5)
        self.event_manager.add_event(self.build_order_manager.step, 0.5)
        self.event_manager.add_event(self.army_manager.step, 1.1)
        self.event_manager.add_event(self.coordinator.step, 2)

    async def on_step(self, iteration):
        sys.stdout.flush()

        if iteration == 0:  # Do nothing on the first iteration to avoid
                            # everything being done at the same time
            if self.verbose:
                print('\n------------------------\n')
                print('%8.2f %3d Rise and Shine' % (self.time, self.supply_used))

            await self.chat_send("Cry 'havoc', and let slips the Tapiocas of war!")

            return

        if self.build_order_manager.did_early_game_just_end():
            print('             Enabling more stuff')
            self.event_manager.add_event(self.building_manager.manage_supply, 1)
            self.event_manager.add_event(self.building_manager.expansion_controller, 5)
            self.event_manager.add_event(self.building_manager.build_nexus, 5)
            self.event_manager.add_event(self.build_workers, 2.25)
            # self.event_manager.add_event(self.scouting_controller.step, 10)
            self.event_manager.add_event(self.building_manager.step, 2)
            self.event_manager.add_event(self.upgrades_controller.step, 5)

            # Gateway stuff
            self.event_manager.add_event(self.gateway_controller.step, 1.0)
            self.gateway_controller.add_order((UnitTypeId.STALKER, 2))
            self.gateway_controller.add_order((UnitTypeId.ZEALOT, 1))

            # Robo stuff
            self.event_manager.add_event(self.robotics_facility_controller.step, 1.0)
            self.robotics_facility_controller.add_order(UnitTypeId.OBSERVER)
            self.robotics_facility_controller.add_order(UnitTypeId.IMMORTAL)
            self.robotics_facility_controller.add_order(UnitTypeId.IMMORTAL)
            self.robotics_facility_controller.add_order(UnitTypeId.IMMORTAL)

        events = self.event_manager.get_current_events(self.time)
        for event in events:
            await event()

        await self.debug()

        await self.execute_order_queue()

    async def do(self, action):
        self.order_queue.append(action)

    async def execute_order_queue(self):
        await self._client.actions(self.order_queue, game_data=self._game_data)
        self.order_queue = []

    async def build_workers(self):
        if not self.coordinator.can('build'):
            return

        nexus = self.units(UnitTypeId.NEXUS).ready.noqueue
        n_workers = self.units(UnitTypeId.PROBE).amount

        if nexus and n_workers < self.units(UnitTypeId.NEXUS).amount * 22 and n_workers < self.maximum_workers:
            if self.can_afford(UnitTypeId.PROBE) and self.supply_left >= 1:
                await self.do(nexus.random.train(UnitTypeId.PROBE))

    async def handle_idle_workers(self):
        idle_workers = self.units(UnitTypeId.PROBE).idle

        if idle_workers.exists:
            await self.distribute_workers()

    async def debug(self):
        if not self.visual_debug:
            return

        # Setup and info

        font_size = 18

        total_units = 0
        for unit_type in self.army_manager.units_available_for_attack.keys():
            total_units += self.units(unit_type).idle.amount

        number_of_minerals = sum([self.state.mineral_field.closer_than(10, x).amount for x in self.townhalls])

        # Text

        messages = [
            '        priority: %s ' % self.coordinator.priority,
            '       n_workers: %3d' % self.units(UnitTypeId.PROBE).amount,
            '       n_zealots: %3d' % self.units(UnitTypeId.ZEALOT).amount,
            '      n_stalkers: %3d' % self.units(UnitTypeId.STALKER).amount,
            '     n_immortals: %3d' % self.units(UnitTypeId.IMMORTAL).amount,
            '       idle_army: %3d' % total_units,
            '       army_size: %3d' % self.army_manager.army_size(),
            '     ememy_units: %3d' % self.known_enemy_units.amount,
            'ememy_structures: %3d' % self.known_enemy_structures.amount,
            '   minerals_left: %3d' % number_of_minerals,
        ]

        y = 0
        inc = 0.025

        for message in messages:
            self._client.debug_text_screen(message, pos=(0.001, y), size=font_size)
            y += inc

        # 3D text

        for tag in self.army_manager.soldiers:
            unit = self.units.find_by_tag(tag)
            if unit is not None:
                message = self.army_manager.soldiers[tag]['state']
                self._client.debug_text_world(message, pos=unit.position3d, size=font_size)

        # Spheres

        leader_tag = self.army_manager.leader
        for soldier_tag in self.army_manager.soldiers:
            soldier_unit = self.units.find_by_tag(soldier_tag)

            if soldier_unit is not None:
                if soldier_tag == leader_tag:
                    self._client.debug_sphere_out(soldier_unit, r=1, color=(255, 0, 0))
                else:
                    self._client.debug_sphere_out(soldier_unit, r=1, color=(0, 0, 255))

        # Lines

        if self.army_manager.army_size() > 0:
            leader_tag = self.army_manager.leader
            leader_unit = self.units.find_by_tag(leader_tag)

            for soldier_tag in self.army_manager.soldiers:
                if soldier_tag == leader_tag:
                    continue

                soldier_unit = self.units.find_by_tag(soldier_tag)
                if soldier_unit is not None:
                    leader_tag = self.army_manager.leader
                    leader_unit = self.units.find_by_tag(leader_tag)
                    if leader_unit is not None:
                        self._client.debug_line_out(leader_unit, soldier_unit, color=(0, 255, 255))

        # Attack Lines

        if self.army_manager.army_size() > 0:
            for soldier_tag in self.army_manager.soldiers:
                soldier_unit = self.units.find_by_tag(soldier_tag)

                if soldier_unit is not None and \
                   self.army_manager.soldiers[soldier_tag]['state'] == 'attacking' and \
                   self.army_manager.attack_target is not None:
                    self._client.debug_line_out(
                        soldier_unit,
                        self.army_manager.attack_target,
                        color=(255, 0, 0)
                    )

        # Sens the debug info to the game
        await self._client.send_debug()

    def get_unit_info(self, unit, field="food_required"):
        assert isinstance(unit, (Unit, UnitTypeId))

        if isinstance(unit, Unit):
            unit = unit._type_data._proto
        else:
            unit = self._game_data.units[unit.value]._proto

        if hasattr(unit, field):
            return getattr(unit, field)
        else:
            return None
