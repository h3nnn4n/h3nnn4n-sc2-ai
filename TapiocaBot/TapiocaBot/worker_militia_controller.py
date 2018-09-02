import random
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2


class WorkerMilitiaController:
    def __init__(self, bot=None, verbose=False):
        self.verbose = False  # verbose
        self.bot = bot

        self.threat_proximity = 40
        self.proxy_proximity = 80
        self.militia = {}
        self.nearby_enemy_workers_found = {}
        self.nearby_enemy_units_found = {}
        self.nearby_enemy_structures_found = {}
        self.number_of_units_to_attack_enemy_workers = 2

        self.worker_unit_types = [
            UnitTypeId.DRONE,
            UnitTypeId.PROBE,
            UnitTypeId.SCV
        ]

    async def step(self):
        self.update_threats()
        await self.step_militia_workers()

    async def step_militia_workers(self):
        self.update_militia()
        await self.micro_militia()

    def update_militia(self):
        for enemy_tag, info in self.nearby_enemy_workers_found.items():
            if 'attacking_units' not in info.keys():
                info['attacking_units'] = {}

            to_delete = []
            for unit_tag in info['attacking_units'].keys():
                if self.bot.units.find_by_tag(unit_tag) is None:
                    to_delete.append(unit_tag)

            for unit_tag in to_delete:
                info['attacking_units'].pop(unit_tag)

            militia_lacking = (
                len(info['attacking_units']) -
                self.number_of_units_to_attack_enemy_workers
            )

            for _ in range(militia_lacking):
                new = self.get_workers_for_militia()
                info['attacking_units'][new] = {'target': enemy_tag}

    async def micro_militia(self):
        for enemy_tag, info in self.nearby_enemy_workers_found.items():
            enemy = self.bot.known_enemy_units.find_by_tag(enemy_tag)

            if enemy is None:
                return

            for unit_tag in info['attacking_units']:
                unit = self.bot.units.find_by_tag(unit_tag)
                await self.bot.do(unit.attack(enemy))

    def get_workers_for_militia(self):
        for worker in self.bot.units(UnitTypeId.PROBE).gathering:
            if worker.tag not in self.militia.keys():
                self.militia[worker.tag] = {}
                return worker.tag

    def update_threats(self):
        # nexi = self.bot.units(UnitTypeId.NEXUS)

        nearby_enemy_workers = []
        nearby_enemy_units = []
        nearby_enemy_structures = []

        # for nexus in nexi:
        #     nearby_enemy_workers = self.bot.known_enemy_units.filter(
        #         lambda unit: unit.type_id in self.worker_unit_types
        #     ).closer_than(self.threat_proximity, nexus.position)

        #     nearby_enemy_units = self.bot.known_enemy_units.filter(
        #         lambda unit: unit.type_id not in self.worker_unit_types
        #     ).closer_than(self.threat_proximity, nexus.position)

        #     nearby_enemy_structures = self.bot.known_enemy_structures.closer_than(
        #         self.threat_proximity, nexus.position
        #     )

        nearby_enemy_workers = self.bot.known_enemy_units.filter(
            lambda unit: unit.type_id in self.worker_unit_types
        )

        nearby_enemy_units = self.bot.known_enemy_units.filter(
            lambda unit: unit.type_id not in self.worker_unit_types
        )

        nearby_enemy_structures = self.bot.known_enemy_structures

        for unit in nearby_enemy_workers:
            if unit.tag not in self.nearby_enemy_workers_found:
                self.nearby_enemy_workers_found[unit.tag] = {'position': unit.position}

        for unit in nearby_enemy_units:
            if unit.tag not in self.nearby_enemy_workers_found:
                self.nearby_enemy_workers_found[unit.tag] = {'position': unit.position}

        for unit in nearby_enemy_structures:
            if unit.tag not in self.nearby_enemy_structures_found:
                self.nearby_enemy_structures_found[unit.tag] = {'position': unit.position}
