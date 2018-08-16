import random
from sc2.ids.unit_typeid import UnitTypeId


class WorkerController:
    def __init__(self, bot=None, verbose=False):
        self.verbose = verbose
        self.bot = bot

        self.auto_build_worker = False
        self.auto_handle_idle_workers = True

        self.priority = ['GAS', 'MINERAL']

        self.maximum_workers = 66

        self.mineral_field_cache = {}

    async def step(self):
        await self.build_workers()
        await self.handle_idle_workers()

    async def build_workers(self):
        if not self.auto_build_worker and not self.bot.coordinator.can('build'):
            return

        nexus = self.bot.units(UnitTypeId.NEXUS).ready.noqueue
        n_workers = self.bot.units(UnitTypeId.PROBE).amount

        if nexus and n_workers < self.bot.units(UnitTypeId.NEXUS).amount * 22 and \
           n_workers < self.maximum_workers:
            if self.bot.can_afford(UnitTypeId.PROBE) and self.bot.supply_left >= 1:
                await self.bot.do(nexus.random.train(UnitTypeId.PROBE))

    async def handle_idle_workers(self):
        if not self.auto_handle_idle_workers:
            return

        idle_workers = self.bot.units(UnitTypeId.PROBE).idle

        if idle_workers.amount == 0 or self.bot.units(UnitTypeId.NEXUS).amount == 0:
            return

        owned_expansions = self.bot.owned_expansions

        if self.verbose:
            print('%8.2f %3d Found %d idle workers' % (self.bot.time, self.bot.supply_used, idle_workers.amount))

        for worker in idle_workers:
            for priority in self.priority:
                if priority == 'GAS':
                    for geyser in self.bot.geysers:
                        actual = geyser.assigned_harvesters
                        ideal = geyser.ideal_harvesters
                        missing = ideal - actual

                        if missing > 0:
                            await self.bot.do(worker.gather(geyser))
                else:
                    for _, townhall in owned_expansions.items():
                        actual = townhall.assigned_harvesters
                        ideal = townhall.ideal_harvesters
                        missing = ideal - actual

                        if missing > 0:
                            mineral = self.get_mineral_for_townhall(townhall)
                            await self.bot.do(worker.gather(mineral))

    def get_mineral_for_townhall(self, townhall):
        townhall_tag = townhall.tag

        if townhall_tag in self.mineral_field_cache.keys():
            mineral = self.mineral_field_cache[townhall_tag]
            if self.bot.units.find_by_tag(mineral.tag) is not None:
                return mineral

        mineral = self.bot.state.mineral_field.closest_to(townhall)
        self.mineral_field_cache[townhall_tag] = mineral

        return mineral
