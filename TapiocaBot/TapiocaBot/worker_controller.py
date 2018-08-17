import random
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId


class WorkerController:
    def __init__(self, bot=None, verbose=False):
        self.verbose = verbose
        self.bot = bot

        self.auto_build_worker = False
        self.auto_handle_idle_workers = True

        self.priority = ['MINERAL', 'GAS']

        self.max_workers_on_gas = 9
        self.current_workers_on_gas = 0

        self.maximum_workers = 66

        self.mineral_field_cache = {}
        self.idle_workers = {}

        self.nexus = {}

        self.on_nexus_ready_do = [self.redistribute_workers]
        self.on_mineral_field_depleted_do = [self.redistribute_workers]

        self.mineral_field_count = 0
        self.mineral_field_count_timer = 0
        self.mineral_field_count_cooldown = 10

    async def step(self):
        self.update_worker_count_on_gas()
        await self.build_workers()
        await self.handle_idle_workers()
        await self.on_nexus_ready()
        await self.on_mineral_field_depleted()

    def update_worker_count_on_gas(self):
        self.current_workers_on_gas = 0

        for geyser in self.bot.geysers:
            self.current_workers_on_gas += geyser.assigned_harvesters

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

        new_idle_workers = 0

        for worker in idle_workers:
            if worker.tag not in self.idle_workers.keys():
                self.idle_workers[worker.tag] = {}
                new_idle_workers += 1

            send_to = None

            for priority in self.priority:
                if priority == 'GAS' and self.current_workers_on_gas < self.max_workers_on_gas:
                    for geyser in self.bot.geysers:
                        actual = geyser.assigned_harvesters
                        ideal = geyser.ideal_harvesters
                        missing = ideal - actual

                        if missing > 0 and send_to is None:
                            send_to = geyser
                            break
                else:
                    for _, townhall in owned_expansions.items():
                        actual = townhall.assigned_harvesters
                        ideal = townhall.ideal_harvesters
                        missing = ideal - actual

                        if missing > 0 and send_to is None:
                            mineral = self.get_mineral_for_townhall(townhall)
                            send_to = mineral
                            break

            await self.bot.do(worker.gather(send_to))

        if self.verbose and new_idle_workers > 0:
            print('%8.2f %3d Found %d idle workers' % (self.bot.time, self.bot.supply_used, new_idle_workers))

    async def on_nexus_ready(self):
        for nexus in self.bot.units(UnitTypeId.NEXUS).ready:
            if nexus.tag not in self.nexus.keys():
                self.nexus[nexus.tag] = {}
                for event in self.on_nexus_ready_do:
                    await event()

    async def on_mineral_field_depleted(self):
        if self.bot.time - self.mineral_field_count_timer > self.mineral_field_count_cooldown:
            self.mineral_field_count_timer = self.bot.time
            mineral_field_count = sum([
                self.bot.state.mineral_field.closer_than(10, x).amount
                for x in self.bot.townhalls
            ])

            if mineral_field_count < self.mineral_field_count:
                for event in self.on_mineral_field_depleted_do:
                    await event()

            self.mineral_field_count = mineral_field_count

    def get_mineral_for_townhall(self, townhall):
        townhall_tag = townhall.tag

        if townhall_tag in self.mineral_field_cache.keys():
            mineral = self.mineral_field_cache[townhall_tag]
            if self.bot.units.find_by_tag(mineral.tag) is not None:
                return mineral

        mineral = self.bot.state.mineral_field.closest_to(townhall)
        self.mineral_field_cache[townhall_tag] = mineral

        return mineral

    async def redistribute_workers(self):
        """
        Taken from https://github.com/Dentosal/python-sc2/blob/master/sc2/bot_ai.py
        Distributes workers across all the bases taken.
        WARNING: This is quite slow when there are lots of workers or multiple bases.
        """

        # TODO:
        # OPTIMIZE: Assign idle workers smarter
        # OPTIMIZE: Never use same worker mutltiple times

        owned_expansions = self.bot.owned_expansions
        worker_pool = []
        for idle_worker in self.bot.workers.idle:
            mf = self.bot.state.mineral_field.closest_to(idle_worker)
            await self.bot.do(idle_worker.gather(mf))

        for location, townhall in owned_expansions.items():
            workers = self.bot.workers.closer_than(20, location)
            actual = townhall.assigned_harvesters
            ideal = townhall.ideal_harvesters
            excess = actual - ideal
            if actual > ideal:
                worker_pool.extend(workers.random_group_of(min(excess, len(workers))))
                continue
        for g in self.bot.geysers:
            workers = self.bot.workers.closer_than(5, g)
            actual = g.assigned_harvesters
            ideal = g.ideal_harvesters
            excess = actual - ideal
            if actual > ideal:
                worker_pool.extend(workers.random_group_of(min(excess, len(workers))))
                continue

        for g in self.bot.geysers:
            actual = g.assigned_harvesters
            ideal = g.ideal_harvesters
            deficit = ideal - actual

            for _ in range(0, deficit):
                if worker_pool:
                    w = worker_pool.pop()
                    if len(w.orders) == 1 and w.orders[0].ability.id in [AbilityId.HARVEST_RETURN]:
                        await self.bot.do(w.move(g))
                        await self.bot.do(w.return_resource(queue=True))
                    else:
                        await self.bot.do(w.gather(g))

        for location, townhall in owned_expansions.items():
            actual = townhall.assigned_harvesters
            ideal = townhall.ideal_harvesters

            deficit = ideal - actual
            for _ in range(0, deficit):
                if worker_pool:
                    w = worker_pool.pop()
                    mf = self.bot.state.mineral_field.closest_to(townhall)
                    if len(w.orders) == 1 and w.orders[0].ability.id in [AbilityId.HARVEST_RETURN]:
                        await self.bot.do(w.move(townhall))
                        await self.bot.do(w.return_resource(queue=True))
                        await self.bot.do(w.gather(mf, queue=True))
                    else:
                        await self.bot.do(w.gather(mf))
