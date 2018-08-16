from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId


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
        nexus = self.bot.units(UnitTypeId.NEXUS).ready.first
        nexus_count = self.bot.units(UnitTypeId.NEXUS).amount
        nexus_pending = self.bot.already_pending(UnitTypeId.NEXUS)
        nexus_noqueue = self.bot.units(UnitTypeId.NEXUS).ready.noqueue

        pylons = self.bot.units(UnitTypeId.PYLON)
        pylon_count = pylons.ready.amount
        pylon_pending = self.bot.already_pending(UnitTypeId.PYLON)

        probe_count = self.bot.units(UnitTypeId.PROBE).ready.amount
        probe_pending = self.bot.already_pending(UnitTypeId.PROBE)

        gateways = self.bot.units(UnitTypeId.GATEWAY)
        gateway_count = gateways.amount
        gateway_pending = self.bot.already_pending(UnitTypeId.GATEWAY)

        cybernetics = self.bot.units(UnitTypeId.CYBERNETICSCORE)
        cybernetics_count = cybernetics.amount
        cybernetics_pending = self.bot.already_pending(UnitTypeId.CYBERNETICSCORE)

        robo_count = self.bot.units(UnitTypeId.ROBOTICSFACILITY).amount
        robo_pending = self.bot.already_pending(UnitTypeId.ROBOTICSFACILITY)

        twilight_count = self.bot.units(UnitTypeId.TWILIGHTCOUNCIL).amount
        twilight_pending = self.bot.already_pending(UnitTypeId.TWILIGHTCOUNCIL)

        # Chrono
        nexus_abilities = await self.bot.get_available_abilities(nexus)
        if AbilityId.EFFECT_CHRONOBOOSTENERGYCOST in nexus_abilities:
            if not nexus.has_buff(BuffId.CHRONOBOOSTENERGYCOST):
                if self.chronos_on_nexus < 2:
                    self.chronos_on_nexus += 1
                    await self.bot.do(nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, nexus))
                else:
                    cybernetics_core = self.bot.units(UnitTypeId.CYBERNETICSCORE).ready
                    if cybernetics_core.exists:
                        await self.bot.do(nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, cybernetics_core.first))

        # Probe until 14
        if probe_count < 14 and not probe_pending:
            if self.bot.can_afford(UnitTypeId.PROBE) and nexus_noqueue.exists:
                await self.bot.do(nexus.train(UnitTypeId.PROBE))
                if self.verbose:
                    print('%8.2f %3d Building Probe' % (self.bot.time, self.bot.supply_used))

        # 14 Pylon
        if probe_count == 14 and pylon_count == 0 and not pylon_pending:
            if self.bot.can_afford(UnitTypeId.PYLON):
                await self.bot.building_controller.build_pylon()
                if self.verbose:
                    print('%8.2f %3d Building Pylon' % (self.bot.time, self.bot.supply_used))

        # Probe until 16
        if probe_count < 16 and not probe_pending and pylon_count > 0:
            if self.bot.can_afford(UnitTypeId.PROBE) and nexus_noqueue.exists:
                await self.bot.do(nexus.train(UnitTypeId.PROBE))
                if self.verbose:
                    print('%8.2f %3d Building Probe' % (self.bot.time, self.bot.supply_used))

        # 16 Gateway
        if probe_count == 16 and pylon_count >= 1 and gateway_count == 0 and not gateway_pending:
            if self.bot.can_afford(UnitTypeId.GATEWAY):
                pylon = self.bot.units(UnitTypeId.PYLON).ready.random
                await self.bot.build(UnitTypeId.GATEWAY, near=pylon)
                if self.verbose:
                    print('%8.2f %3d Building Gateway' % (self.bot.time, self.bot.supply_used))

        # @100% Gateway -> Cybernetics core
        if gateways.ready.amount == 1 and not cybernetics_pending and cybernetics_count == 0:
            if self.bot.can_afford(UnitTypeId.CYBERNETICSCORE):
                pylon = self.bot.units(UnitTypeId.PYLON).ready.random
                await self.bot.build(UnitTypeId.CYBERNETICSCORE, near=pylon)
                if self.verbose:
                    print('%8.2f %3d Building Cybernetics Core' % (self.bot.time, self.bot.supply_used))

        # 16 and 17 Gas
        if ((probe_count == 16 and self.bot.units(UnitTypeId.ASSIMILATOR).amount == 0) or
           (probe_count == 17 and self.bot.units(UnitTypeId.ASSIMILATOR).amount == 1)) and gateway_count > 0:
            if self.bot.can_afford(UnitTypeId.ASSIMILATOR):
                await self.bot.building_controller.build_assimilator()
                if self.verbose:
                    print('%8.2f %3d Building Assimilator' % (self.bot.time, self.bot.supply_used))

        # 18 Gateway
        if probe_count == 18 and pylon_count >= 1 and gateway_count == 1:
            if self.bot.can_afford(UnitTypeId.GATEWAY):
                pylon = self.bot.units(UnitTypeId.PYLON).ready.random
                await self.bot.build(UnitTypeId.GATEWAY, near=pylon)
                if self.verbose:
                    print('%8.2f %3d Building Gateway' % (self.bot.time, self.bot.supply_used))

        # Probes until 21
        if ((probe_count < 18 and gateway_count == 1) or
           (probe_count < 21 and gateway_count == 2)) and not probe_pending:
            if self.bot.can_afford(UnitTypeId.PROBE) and nexus_noqueue.exists:
                await self.bot.do(nexus.train(UnitTypeId.PROBE))
                if self.verbose:
                    print('%8.2f %3d Building Probe' % (self.bot.time, self.bot.supply_used))

        # 21 Pylon
        if probe_count == 21 and pylon_count == 1 and not pylon_pending:
            if self.bot.can_afford(UnitTypeId.PYLON):
                await self.bot.building_controller.build_pylon()
                if self.verbose:
                    print('%8.2f %3d Building Pylon' % (self.bot.time, self.bot.supply_used))

        # @100% Cybernetics core -> Research Warpgate
        if cybernetics.ready.amount >= 1 and not self.warpgate_started and \
           self.bot.can_afford(AbilityId.RESEARCH_WARPGATE):
            ccore = self.bot.units(UnitTypeId.CYBERNETICSCORE).ready.first
            await self.bot.do(ccore(AbilityId.RESEARCH_WARPGATE))
            self.warpgate_started = True
            if self.verbose:
                print('%8.2f %3d Researching Warpgate' % (self.bot.time, self.bot.supply_used))

        # @100% Cybernetics core -> Build 2 adepts
        if gateways.ready.amount > 0 and self.adepts_warped_in < 2 and \
           self.bot.can_afford(UnitTypeId.ADEPT) and \
           self.bot.units(UnitTypeId.ADEPT).amount < 2:
            for gateway in self.bot.units(UnitTypeId.GATEWAY).ready.noqueue:
                abilities = await self.bot.get_available_abilities(gateway)
                if self.bot.can_afford(AbilityId.TRAIN_ADEPT) and \
                   AbilityId.TRAIN_ADEPT in abilities and \
                   self.bot.can_afford(UnitTypeId.ADEPT):
                    await self.bot.do(gateway.train(UnitTypeId.ADEPT))
                    self.adepts_warped_in += 1
                    if self.verbose:
                        print('%8.2f %3d Warping in an Adept' % (self.bot.time, self.bot.supply_used))
                    break

        # @2 Adepts -> 2 Stalkers
        if self.bot.units(UnitTypeId.GATEWAY).ready.amount > 0 and \
           self.stalkers_warped_in < 2 and self.adepts_warped_in >= 2 and \
           self.bot.can_afford(UnitTypeId.STALKER) and \
           self.bot.units(UnitTypeId.ADEPT).amount >= 2 and \
           self.bot.units(UnitTypeId.STALKER).amount < 2:
            for gateway in self.bot.units(UnitTypeId.GATEWAY).ready.noqueue:
                abilities = await self.bot.get_available_abilities(gateway)
                if self.bot.can_afford(AbilityId.GATEWAYTRAIN_STALKER) and \
                   AbilityId.GATEWAYTRAIN_STALKER in abilities and \
                   self.bot.can_afford(UnitTypeId.STALKER):
                    await self.bot.do(gateway.train(UnitTypeId.STALKER))
                    self.stalkers_warped_in += 1
                    if self.verbose:
                        print('%8.2f %3d Warping in an Stalker' % (self.bot.time, self.bot.supply_used))
                    break

        # After the units have been warped in keep making workers
        if self.stalkers_warped_in >= 2 and self.adepts_warped_in >= 2 and \
           self.bot.supply_used < 31 and not probe_pending:
            if self.bot.can_afford(UnitTypeId.PROBE) and nexus_noqueue.exists:
                await self.bot.do(nexus.train(UnitTypeId.PROBE))
                if self.verbose:
                    print('%8.2f %3d Building Probe' % (self.bot.time, self.bot.supply_used))

        # 31 nexus
        if self.bot.supply_left == 0 and self.bot.supply_cap == 31 and nexus_count == 1 and \
           not self.bot.already_pending(UnitTypeId.NEXUS):
            if self.bot.can_afford(UnitTypeId.NEXUS):
                await self.bot.expand_now()
                if self.verbose:
                    print('%8.2f %3d Expanding' % (self.bot.time, self.bot.supply_used))

        # 31 pylon
        if self.bot.supply_left == 0 and self.bot.supply_cap == 31 and \
           nexus_pending and pylon_count == 2 and not pylon_pending:
            natural_nexus = self.bot.units(UnitTypeId.NEXUS).not_ready
            if natural_nexus.exists and self.bot.can_afford(UnitTypeId.PYLON):
                await self.bot.build(UnitTypeId.PYLON, near=natural_nexus.first)  # TODO Improve pylon positioning
                if self.verbose:
                    print('%8.2f %3d Building Pylon' % (self.bot.time, self.bot.supply_used))

        # 31 robo
        if nexus_count == 2 and pylon_count == 3 and robo_count == 0 and not robo_pending:
            if self.bot.can_afford(UnitTypeId.ROBOTICSFACILITY):
                pylon = self.bot.units(UnitTypeId.PYLON).ready.random
                await self.bot.build(UnitTypeId.ROBOTICSFACILITY, near=pylon)
                if self.verbose:
                    print('%8.2f %3d Building Robotics Facility' % (self.bot.time, self.bot.supply_used))

        # 35 twilight council
        if self.bot.supply_used > 35 and nexus_count == 2 and pylon_count == 3 and \
           twilight_count == 0 and not twilight_pending:
            if self.bot.can_afford(UnitTypeId.TWILIGHTCOUNCIL):
                pylon = self.bot.units(UnitTypeId.PYLON).ready.random
                await self.bot.build(UnitTypeId.TWILIGHTCOUNCIL, near=pylon)
                if self.verbose:
                    print('%8.2f %3d Building Twilight ' % (self.bot.time, self.bot.supply_used))

        # 37 Pylon
        if self.bot.supply_used >= 37 and nexus_count == 2 and pylon_count == 3 and not pylon_pending:
            natural_nexus = self.bot.units(UnitTypeId.NEXUS).ready
            if natural_nexus.exists and self.bot.can_afford(UnitTypeId.PYLON):
                await self.bot.build(UnitTypeId.PYLON, near=natural_nexus.first)  # TODO Improve pylon positioning
                if self.verbose:
                    print('%8.2f %3d Building Pylon' % (self.bot.time, self.bot.supply_used))

        # Probes util 37 supply
        if self.bot.supply_used < 37 and not probe_pending:
            if self.bot.can_afford(UnitTypeId.PROBE) and nexus_noqueue.exists:
                await self.bot.do(nexus.train(UnitTypeId.PROBE))
                if self.verbose:
                    print('%8.2f %3d Building Probe' % (self.bot.time, self.bot.supply_used))

        # Mark the build as ready
        if self.bot.supply_used == 37 and nexus_count == 2 and pylon_count == 3 and \
           twilight_count == 1 and robo_count == 1:
            self.finished = True
