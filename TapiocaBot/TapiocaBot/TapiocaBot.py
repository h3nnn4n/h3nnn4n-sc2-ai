import numpy as np
import random
import sys
import sc2
from math import ceil
from sc2 import Race, Difficulty

from sc2.player import Bot, Computer
from sc2.unit import Unit
from sc2.units import Units
from sc2.position import Point2, Point3

from sc2.ids.unit_typeid import UnitTypeId  # Used for debugging

from event_manager import EventManager
from build_order_controller import BuildOrderController
from robotics_facility_controller import RoboticsFacilitiyController
from gateway_controller import GatewayController
from scouting_controller import ScoutingController
from building_controller import BuildingController
from upgrades_controller import UpgradesController
from worker_controller import WorkerController
from army_controller import ArmyController

from coordinator import Coordinator
from debug_controller import DebugController


class TapiocaBot(sc2.BotAI):
    def __init__(self, verbose=False, visual_debug=False):
        self.verbose = verbose
        self.visual_debug = visual_debug

        self.debug_controller = DebugController(bot=self, verbose=self.verbose)
        self.army_controller = ArmyController(bot=self, verbose=self.verbose)
        self.order_queue = []

    def on_start(self):
        self.army_controller.init()

    async def on_step(self, iteration):
        sys.stdout.flush()

        await self.army_controller.step()
        await self.execute_order_queue()
        await self._client.send_debug()

        await self.debug_controller.send()
        await self.debug()

    async def do(self, action):
        self.order_queue.append(action)

    async def execute_order_queue(self):
        await self._client.actions(self.order_queue, game_data=self._game_data)
        self.order_queue = []

    async def debug(self):
        if not self.visual_debug:
            return

        # Setup and info

        font_size = 14

        total_units = 0
        for unit_type in self.army_controller.units_available_for_attack.keys():
            total_units += self.units(unit_type).idle.amount

        # Text

        messages = [
            '      n_stalkers: %3d' % self.units(UnitTypeId.STALKER).amount,
            '     ememy_units: %3d' % self.known_enemy_units.amount,
            'ememy_structures: %3d' % self.known_enemy_structures.amount,
        ]

        y = 0
        inc = 0.018

        for message in messages:
            self._client.debug_text_screen(message, pos=(0.001, y), size=font_size)
            y += inc

        # 3D text

        debug_army_state = True

        if debug_army_state:
            for tag in self.army_controller.soldiers:
                unit = self.units.find_by_tag(tag)
                if unit is not None:
                    message = self.army_controller.soldiers[tag]['state']
                    self._client.debug_text_world(message, pos=unit.position3d, size=font_size)

        # Spheres

        debug_army_groups = True

        if debug_army_groups:
            leader_tag = self.army_controller.leader
            for soldier_tag in self.army_controller.soldiers:
                soldier_unit = self.units.find_by_tag(soldier_tag)

                if soldier_unit is not None:
                    if soldier_tag == leader_tag:
                        self._client.debug_sphere_out(soldier_unit, r=1, color=(255, 0, 0))
                    else:
                        self._client.debug_sphere_out(soldier_unit, r=1, color=(0, 0, 255))

        # Lines

        if debug_army_groups:
            if self.army_controller.army_size() > 0:
                leader_tag = self.army_controller.leader
                leader_unit = self.units.find_by_tag(leader_tag)

                for soldier_tag in self.army_controller.soldiers:
                    if soldier_tag == leader_tag:
                        continue

                    soldier_unit = self.units.find_by_tag(soldier_tag)
                    if soldier_unit is not None:
                        leader_tag = self.army_controller.leader
                        leader_unit = self.units.find_by_tag(leader_tag)
                        if leader_unit is not None:
                            self._client.debug_line_out(leader_unit, soldier_unit, color=(0, 255, 255))

        # Attack Lines
        debug_army_attack = True

        if debug_army_attack:
            if self.army_controller.army_size() > 0:
                for soldier_tag in self.army_controller.soldiers:
                    soldier_unit = self.units.find_by_tag(soldier_tag)

                    if soldier_unit is not None and \
                       self.army_controller.soldiers[soldier_tag]['state'] == 'attacking' and \
                       self.army_controller.attack_target is not None:
                        self._client.debug_line_out(
                            soldier_unit,
                            self.army_controller.attack_target,
                            color=(255, 127, 0)
                        )

        # Sens the debug info to the game
        await self._client.send_debug()
