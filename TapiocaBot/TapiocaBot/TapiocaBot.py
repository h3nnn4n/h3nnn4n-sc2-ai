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
        # self._client.game_step = 2

    async def on_step(self, iteration):
        if self.verbose:
            sys.stdout.flush()

        await self.army_controller.step()
        await self.execute_order_queue()

        await self.debug_controller.send()

    async def do(self, action):
        self.order_queue.append(action)

    async def execute_order_queue(self):
        await self._client.actions(self.order_queue, game_data=self._game_data)
        self.order_queue = []
