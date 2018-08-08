from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer
from sc2.unit import Unit
from sc2.units import Units
from sc2.position import Point2, Point3


class TwoGateFastExpand:
    def __init__(self, bot=None, verbose=False):
        self.bot = bot
        self.verbose = verbose
        self.finished = False

        self.chronos_on_nexus = 0
        self.adepts_warped_in = 0
        self.stalkers_warped_in = 0
        self.warpgate_started = False

    async def __call__(self):
        if not self.finished:
            await self.step()

    async def step(self):
        nexus = self.bot.units(NEXUS).ready.first
        nexus_noqueue = self.bot.units(NEXUS).ready.noqueue

        pylon_count = self.bot.units(PYLON).ready.amount
        pylon_pending = self.bot.already_pending(PYLON)

        probe_count = self.bot.units(PROBE).ready.amount
        probe_pending = self.bot.already_pending(PROBE)

        gateway_count = self.bot.units(GATEWAY).amount
        gateway_pending = self.bot.already_pending(GATEWAY)

        cybernetics_count = self.bot.units(CYBERNETICSCORE).amount
        cybernetics_pending = self.bot.already_pending(CYBERNETICSCORE)

        # Chrono
        nexus_abilities = await self.bot.get_available_abilities(nexus)
        if EFFECT_CHRONOBOOSTENERGYCOST in nexus_abilities:
            if not nexus.has_buff(CHRONOBOOSTENERGYCOST):
                if self.chronos_on_nexus < 2:
                    self.chronos_on_nexus += 1
                    await self.bot.do(nexus(EFFECT_CHRONOBOOSTENERGYCOST, nexus))
                else:
                    cybernetics_core = self.bot.units(CYBERNETICSCORE).ready
                    if cybernetics_core.exists:
                        await self.bot.do(nexus(EFFECT_CHRONOBOOSTENERGYCOST, cybernetics_core.first))

        # Probe until 14
        if probe_count < 14 and not probe_pending:
            if self.bot.can_afford(PROBE) and nexus_noqueue.exists:
                await self.bot.do(nexus.train(PROBE))
                if self.verbose:
                    print('%8.2f %3d Building Probe' % (self.bot.time, self.bot.supply_used))

        # 14 Pylon
        if probe_count == 14 and pylon_count == 0 and not pylon_pending:
            if self.bot.can_afford(PYLON):
                await self.bot.building_manager.build_pylon()
                if self.verbose:
                    print('%8.2f %3d Building Pylon' % (self.bot.time, self.bot.supply_used))

        # Probe until 16
        if probe_count < 16 and not probe_pending and self.bot.units(PYLON).amount > 0:
            if self.bot.can_afford(PROBE) and nexus_noqueue.exists:
                await self.bot.do(nexus.train(PROBE))
                if self.verbose:
                    print('%8.2f %3d Building Probe' % (self.bot.time, self.bot.supply_used))

        # 16 Gateway
        if probe_count == 16 and pylon_count >= 1 and gateway_count == 0 and not gateway_pending:
            if self.bot.can_afford(GATEWAY):
                pylon = self.bot.units(PYLON).ready.random
                await self.bot.build(GATEWAY, near=pylon)
                if self.verbose:
                    print('%8.2f %3d Building Gateway' % (self.bot.time, self.bot.supply_used))

        # @100% Gateway -> Cybernetics core
        if self.bot.units(GATEWAY).ready.amount == 1 and not cybernetics_pending and cybernetics_count == 0:
            if self.bot.can_afford(CYBERNETICSCORE):
                pylon = self.bot.units(PYLON).ready.random
                await self.bot.build(CYBERNETICSCORE, near=pylon)
                if self.verbose:
                    print('%8.2f %3d Building Cybernetics Core' % (self.bot.time, self.bot.supply_used))

        # 16 and 17 Gas
        if ((probe_count == 16 and self.bot.units(ASSIMILATOR).amount == 0) or
            (probe_count == 17 and self.bot.units(ASSIMILATOR).amount == 1)) and self.bot.units(GATEWAY).amount > 0:
            if self.bot.can_afford(ASSIMILATOR):
                await self.bot.building_manager.build_assimilator()
                if self.verbose:
                    print('%8.2f %3d Building Assimilator' % (self.bot.time, self.bot.supply_used))

        # 18 Gateway
        if probe_count == 18 and pylon_count >= 1 and gateway_count == 1:
            if self.bot.can_afford(GATEWAY):
                pylon = self.bot.units(PYLON).ready.random
                await self.bot.build(GATEWAY, near=pylon)
                if self.verbose:
                    print('%8.2f %3d Building Gateway' % (self.bot.time, self.bot.supply_used))

        # Probes until 21
        if ((probe_count < 18 and self.bot.units(GATEWAY).amount == 1) or
            (probe_count < 21 and self.bot.units(GATEWAY).amount == 2)) and not probe_pending:
            if self.bot.can_afford(PROBE) and nexus_noqueue.exists:
                await self.bot.do(nexus.train(PROBE))
                if self.verbose:
                    print('%8.2f %3d Building Probe' % (self.bot.time, self.bot.supply_used))

        # 21 Pylon
        if probe_count == 21 and pylon_count == 1 and not pylon_pending:
            if self.bot.can_afford(PYLON):
                await self.bot.building_manager.build_pylon()
                if self.verbose:
                    print('%8.2f %3d Building Pylon' % (self.bot.time, self.bot.supply_used))

        # @100% Cybernetics core -> Research Warpgate
        if self.bot.units(CYBERNETICSCORE).ready.exists and self.bot.can_afford(RESEARCH_WARPGATE) and not self.warpgate_started:
            ccore = self.bot.units(CYBERNETICSCORE).ready.first
            await self.bot.do(ccore(RESEARCH_WARPGATE))
            self.warpgate_started = True
            if self.verbose:
                print('%8.2f %3d Researching Warpgate' % (self.bot.time, self.bot.supply_used))

        # @100% Cybernetics core -> Build 2 adepts
        if self.bot.units(GATEWAY).ready.amount > 0 and self.adepts_warped_in < 2 and self.bot.can_afford(ADEPT) and self.bot.units(ADEPT).amount < 2:
            for gateway in self.bot.units(GATEWAY).ready.noqueue:
                abilities = await self.bot.get_available_abilities(gateway)
                if self.bot.can_afford(AbilityId.TRAIN_ADEPT) and AbilityId.TRAIN_ADEPT in abilities and self.bot.can_afford(ADEPT):
                    await self.bot.do(gateway.train(ADEPT))
                    self.adepts_warped_in += 1
                    if self.verbose:
                        print('%8.2f %3d Warping in an Adept' % (self.bot.time, self.bot.supply_used))
                    break

        # @2 Adepts -> 2 Stalkers
        if self.bot.units(GATEWAY).ready.amount > 0 and self.stalkers_warped_in < 2 and self.adepts_warped_in >= 2 and self.bot.can_afford(STALKER) and self.bot.units(ADEPT).amount >= 2 and self.bot.units(STALKER).amount < 2:
            for gateway in self.bot.units(GATEWAY).ready.noqueue:
                abilities = await self.bot.get_available_abilities(gateway)
                if self.bot.can_afford(AbilityId.GATEWAYTRAIN_STALKER) and AbilityId.GATEWAYTRAIN_STALKER in abilities and self.bot.can_afford(STALKER):
                    await self.bot.do(gateway.train(STALKER))
                    self.stalkers_warped_in += 1
                    if self.verbose:
                        print('%8.2f %3d Warping in an Stalker' % (self.bot.time, self.bot.supply_used))
                    break

        # After the units have been warped in keep making workers
        if self.stalkers_warped_in >= 2 and self.adepts_warped_in >= 2 and self.bot.supply_used < 31 and not probe_pending:
            if self.bot.can_afford(PROBE) and nexus_noqueue.exists:
                await self.bot.do(nexus.train(PROBE))
                if self.verbose:
                    print('%8.2f %3d Building Probe' % (self.bot.time, self.bot.supply_used))

        # 31 nexus
        if self.bot.supply_left == 0 and self.bot.supply_cap == 31 and self.bot.units(NEXUS).amount == 1 and not self.bot.already_pending(NEXUS):
            if self.bot.can_afford(NEXUS):
                await self.bot.expand_now()
                if self.verbose:
                    print('%8.2f %3d Expanding' % (self.bot.time, self.bot.supply_used))

        # 31 pylon
        if self.bot.supply_left == 0 and self.bot.supply_cap == 31 and self.bot.already_pending(NEXUS) and pylon_count == 2 and not pylon_pending:
            natural_nexus = self.bot.units(NEXUS).not_ready
            if natural_nexus.exists and self.bot.can_afford(PYLON):
                await self.bot.build(PYLON, near=natural_nexus.first)  # TODO Improve pylon positioning
                if self.verbose:
                    print('%8.2f %3d Building Pylon' % (self.bot.time, self.bot.supply_used))

        # 31 robo
        if self.bot.units(NEXUS).amount == 2 and pylon_count == 3 and self.bot.units(ROBOTICSFACILITY).amount == 0 and not self.bot.already_pending(ROBOTICSFACILITY):
            if self.bot.can_afford(ROBOTICSFACILITY):
                pylon = self.bot.units(PYLON).ready.random
                await self.bot.build(ROBOTICSFACILITY, near=pylon)
                if self.verbose:
                    print('%8.2f %3d Building Robotics Facility' % (self.bot.time, self.bot.supply_used))

        # 35 twilight council
        if self.bot.supply_used > 35 and self.bot.units(NEXUS).amount == 2 and pylon_count == 3 and self.bot.units(TWILIGHTCOUNCIL).amount == 0 and not self.bot.already_pending(TWILIGHTCOUNCIL):
            if self.bot.can_afford(TWILIGHTCOUNCIL):
                pylon = self.bot.units(PYLON).ready.random
                await self.bot.build(TWILIGHTCOUNCIL, near=pylon)
                if self.verbose:
                    print('%8.2f %3d Building Twilight ' % (self.bot.time, self.bot.supply_used))

        # 37 Pylon
        if self.bot.supply_used >= 37 and self.bot.units(NEXUS).amount == 2 and pylon_count == 3 and not pylon_pending:
            natural_nexus = self.bot.units(NEXUS).ready
            if natural_nexus.exists and self.bot.can_afford(PYLON):
                await self.bot.build(PYLON, near=natural_nexus.first)  # TODO Improve pylon positioning
                if self.verbose:
                    print('%8.2f %3d Building Pylon' % (self.bot.time, self.bot.supply_used))

        # Probes util 37 supply
        if self.bot.supply_used < 37 and not probe_pending:
            if self.bot.can_afford(PROBE) and nexus_noqueue.exists:
                await self.bot.do(nexus.train(PROBE))
                if self.verbose:
                    print('%8.2f %3d Building Probe' % (self.bot.time, self.bot.supply_used))

        # Mark the build as ready
        if self.bot.supply_used == 37 and self.bot.units(NEXUS).amount == 2 and pylon_count == 3 and \
           self.bot.units(TWILIGHTCOUNCIL).amount == 1 and self.bot.units(ROBOTICSFACILITY).amount == 1:
            self.finished = True
