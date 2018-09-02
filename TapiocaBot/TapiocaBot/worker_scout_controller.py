from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2


class WorkerScoutController:
    def __init__(self, bot=None, verbose=False):
        self.verbose = False  # verbose
        self.bot = bot

        self.number_of_near_scouts = 1
        self.number_of_global_scouts = 0
        self.number_of_scouting_workers = (
            self.number_of_near_scouts +
            self.number_of_global_scouts
        )
        self.number_of_near_expansions_to_scout = 5
        self.scouting_workers = {}
        self.scouting_queue = []

        self.worker_unit_types = [
            UnitTypeId.DRONE,
            UnitTypeId.PROBE,
            UnitTypeId.SCV
        ]

    async def step(self):
        await self.step_scouting_workers()

    async def step_scouting_workers(self):
        if self.bot.units.not_structure.filter(
            lambda x: x.type_id not in self.worker_unit_types
        ).amount > 0:
            self.scouting_workers = {}
            return

        self.update_scouting_worker_status()
        await self.get_more_scouting_workers()
        await self.micro_scouting_workers()

    async def micro_scouting_workers(self):
        for unit_tag in self.scouting_workers.keys():
            await self.micro_scouting_worker(unit_tag)

    async def micro_scouting_worker(self, unit_tag):
        unit = self.bot.units.find_by_tag(unit_tag)
        info = self.scouting_workers[unit_tag]

        if unit.is_idle:
            target = self.get_scouting_position(unit_tag)
            info['target'] = target
            await self.bot.do(unit.move(target))
        elif info['new']:
            info['new'] = False
        else:
            if self.bot.known_enemy_units.amount == 0:
                return

            threats = self.bot.known_enemy_units.filter(
                lambda x: x.can_attack_ground and
                x.type_id not in self.worker_unit_types
            )

            if not threats.exists:
                return

            closest_unit = threats.closest_to(unit.position)

            if closest_unit is None:
                return

            distance_to_clostest_unit = unit.position.distance_to(
                closest_unit.position
            ) - unit.radius - closest_unit.radius

            if distance_to_clostest_unit < closest_unit.ground_range + 1.0:
                step_back_position = unit.position.towards(
                    closest_unit.position,
                    -1
                )
                await self.bot.do(unit.move(step_back_position))
            else:
                await self.bot.do(unit.move(info['target']))

    def get_scouting_position(self, unit_tag):
        info = self.scouting_workers[unit_tag]
        unit = self.bot.units.find_by_tag(unit_tag)

        if info['mode'] == 'global':
            if len(self.scouting_queue) == 0:
                self.scouting_queue = list(self.bot.expansion_locations.keys())

            target = unit.position.closest(self.scouting_queue)
            self.scouting_queue.pop(self.scouting_queue.index(target))
        elif info['mode'] == 'near':
            if 'scouting_queue' not in info:
                info['scouting_queue'] = []

            if len(info['scouting_queue']) == 0:
                info['scouting_queue'] = list(
                    self.bot.expansion_locations.keys()
                )

                nexi = self.bot.units(UnitTypeId.NEXUS).ready

                ignore = []

                for nexus in nexi:
                    for target in info['scouting_queue']:
                        if nexus.position.distance_to(Point2(target)) <= 5:
                            ignore.append(target)

                for target in ignore:
                    info['scouting_queue'].pop(info['scouting_queue'].index(
                        target)
                    )

                info['scouting_queue'].sort(key=lambda x: self.bot.start_location.distance_to(Point2(x)))
                info['scouting_queue'] = info['scouting_queue'][:self.number_of_near_expansions_to_scout]

            target = unit.position.closest(info['scouting_queue'])
            info['scouting_queue'].pop(info['scouting_queue'].index(target))

        return target

    def update_scouting_worker_status(self):
        dead_scouts = []

        for unit_tag in self.scouting_workers.keys():
            if self.bot.units.find_by_tag(unit_tag) is None:
                dead_scouts.append(unit_tag)

        for unit_tag in dead_scouts:
            self.scouting_workers.pop(unit_tag)

    async def get_more_scouting_workers(self):
        if len(self.scouting_workers) < self.number_of_scouting_workers:
            number_of_global_scouts = len(
                list(
                    filter(
                        lambda x: x['mode'] == 'global',
                        self.scouting_workers.values()
                    )
                )
            )
            number_of_near_scouts = len(
                list(
                    filter(
                        lambda x: x['mode'] == 'near',
                        self.scouting_workers.values()
                    )
                )
            )

            probes = self.bot.units(UnitTypeId.PROBE)

            if probes.exists:
                new_scouting_probe = probes.first

                if number_of_near_scouts < self.number_of_near_scouts:
                    self.scouting_workers[new_scouting_probe.tag] = {
                        'mode': 'near',
                        'new': True
                    }
                elif number_of_global_scouts < self.number_of_global_scouts:
                    self.scouting_workers[new_scouting_probe.tag] = {
                        'mode': 'global',
                        'new': True
                    }
                else:
                    self.scouting_workers[new_scouting_probe.tag] = {
                        'mode': 'global',
                        'new': True
                    }

                await self.bot.do(new_scouting_probe.stop())
