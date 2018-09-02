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

        self.worker_unit_types = [
            UnitTypeId.DRONE,
            UnitTypeId.PROBE,
            UnitTypeId.SCV
        ]

        self.target_types = {
            'worker': {
                'units_required': 2,
                'threats': self.nearby_enemy_workers_found
            },
            'unit': {
                'units_required': 4,
                'threats': self.nearby_enemy_units_found
            },
            'structure': {
                'units_required': 6,
                'threats': self.nearby_enemy_structures_found
            }
        }

    async def step(self):
        attack_units = self.bot.units.filter(
            lambda unit: unit.type_id not in self.worker_unit_types
        ).amount

        if attack_units >= 2:
            return

        self.update_threats()
        self.update_militia()
        await self.micro_militia()

    def update_threats(self):
        # nexi = self.bot.units(UnitTypeId.NEXUS)

        # self.nearby_enemy_workers_found.clear()
        # self.nearby_enemy_units_found.clear()
        # self.nearby_enemy_structures_found.clear()

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

        nearby_enemy_units = self.bot.known_enemy_units.not_structure.filter(
            lambda unit: unit.type_id not in self.worker_unit_types
        )

        nearby_enemy_structures = self.bot.known_enemy_structures

        for unit in nearby_enemy_workers:
            if unit.tag not in self.nearby_enemy_workers_found:
                self.nearby_enemy_workers_found[unit.tag] = {
                    'position': unit.position
                }

        for unit in nearby_enemy_units:
            if unit.tag not in self.nearby_enemy_units_found:
                self.nearby_enemy_units_found[unit.tag] = {
                    'position': unit.position
                }

        for unit in nearby_enemy_structures:
            if unit.tag not in self.nearby_enemy_structures_found:
                self.nearby_enemy_structures_found[unit.tag] = {
                    'position': unit.position
                }

    def update_militia(self):
        for _, target_data in self.target_types.items():
            for enemy_tag, info in target_data['threats'].items():
                if 'attacking_units' not in info.keys():
                    info['attacking_units'] = {}

                to_delete = []
                for unit_tag in info['attacking_units'].keys():
                    if self.bot.units.find_by_tag(unit_tag) is None:
                        to_delete.append(unit_tag)

                for unit_tag in to_delete:
                    info['attacking_units'].pop(unit_tag)

                militia_lacking = (
                    target_data['units_required'] - len(info['attacking_units'])
                )

                for _ in range(militia_lacking):
                    new = self.get_workers_for_militia()
                    info['attacking_units'][new] = {'target': enemy_tag}

    async def micro_militia(self):
        to_delete = []

        for target_type, target_data in self.target_types.items():
            for enemy_tag, info in target_data['threats'].items():
                enemy = self.bot.known_enemy_units.find_by_tag(enemy_tag)

                for unit_tag in info['attacking_units']:
                    unit = self.bot.units.find_by_tag(unit_tag)
                    if unit is None:
                        return

                    if enemy is None:
                        to_delete.append((target_type, enemy_tag))

                        if unit_tag is self.militia.keys():
                            self.militia.pop(unit_tag)

                        break

                    await self.bot.do(unit.attack(enemy))

        for target_type, target_tag in to_delete:
            if target_tag in self.target_types[target_type].keys():
                self.target_types[target_type].pop(target_tag)
            else:
                print(target_tag, target_type)

    def get_workers_for_militia(self):
        for worker in self.bot.units(UnitTypeId.PROBE).gathering:
            if worker.tag not in self.militia.keys():
                self.militia[worker.tag] = {}
                return worker.tag
