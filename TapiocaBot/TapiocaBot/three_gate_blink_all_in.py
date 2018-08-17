from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId

'''
  14	  0:16	  Pylon
  15	  0:34	  Gateway
  16	  0:43	  Assimilator
  17	  0:52	  Assimilator
  19	  1:08	  Gateway
  20	  1:23	  Cybernetics Core
  21	  1:32	  Pylon
  23	  1:59	  Warp Gate, Adept x2
  28	  2:11	  Pylon
  28	  2:15	  Twilight Council
  28	  2:29	  Stalker x2
  32	  2:57	  Nexus
  32	  3:07	  Blink (Chrono Boost)
  32	  3:15	  Stalker
  34	  3:21	  Stalker
  36	  3:32	  Gateway
  36	  3:48	  Pylon
  36	  4:03	  Stalker x2
  40	  4:18	  Pylon
  40	  4:29	  Stalker x3
  46	  4:54	  Stalker
'''


class ThreeGateBlinkAllIn:
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
        if self.bot.units(UnitTypeId.NEXUS).amount == 0:
            return

        nexus = self.bot.units(UnitTypeId.NEXUS).ready.first
        nexus_count = self.bot.units(UnitTypeId.NEXUS).amount
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

        twilight_count = self.bot.units(UnitTypeId.TWILIGHTCOUNCIL).amount
        twilight_pending = self.bot.already_pending(UnitTypeId.TWILIGHTCOUNCIL)

        gateway_warpgate_count = (
            self.bot.units(UnitTypeId.GATEWAY).amount +
            self.bot.units(UnitTypeId.WARPGATE).amount
        )

        # Chrono
        nexus_abilities = await self.bot.get_available_abilities(nexus)
        if AbilityId.EFFECT_CHRONOBOOSTENERGYCOST in nexus_abilities:
            if not nexus.has_buff(BuffId.CHRONOBOOSTENERGYCOST):
                cybernetics_core = self.bot.units(UnitTypeId.CYBERNETICSCORE).ready
                if cybernetics_core.exists:
                    await self.bot.do(nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, cybernetics_core.first))

        # Probe until 15
        if probe_count < 15 and not probe_pending:
            if self.bot.can_afford(UnitTypeId.PROBE) and nexus_noqueue.exists:
                await self.bot.do(nexus.train(UnitTypeId.PROBE))
                if self.verbose:
                    print('%8.2f %3d Building Probe' % (self.bot.time, self.bot.supply_used))

        # 15 Pylon
        if probe_count == 15 and pylon_count == 0 and not pylon_pending:
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

        # 15 Gateway
        if probe_count == 15 and pylon_count >= 1 and gateway_count == 0 and not gateway_pending:
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

        # 19 Gateway
        if probe_count == 19 and pylon_count >= 1 and gateway_count == 1 and not gateway_pending:
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
           self.bot.can_afford(UnitTypeId.STALKER):
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

        # twilight council when possible
        if self.bot.supply_used > 21 and nexus_count == 1 and pylon_count == 2 and \
           self.stalkers_warped_in >= 2 and self.adepts_warped_in >= 2 and \
           twilight_count == 0 and not twilight_pending and gateway_warpgate_count >= 2:
            if self.bot.can_afford(UnitTypeId.TWILIGHTCOUNCIL):
                pylon = self.bot.units(UnitTypeId.PYLON).ready.random
                await self.bot.build(UnitTypeId.TWILIGHTCOUNCIL, near=pylon)
                self.finished = True
                if self.verbose:
                    print('%8.2f %3d Building Twilight ' % (self.bot.time, self.bot.supply_used))

        # # Mark the build as ready
        # if self.bot.units(UnitTypeId.TWILIGHTCOUNCIL).amount >= 0 and \
        #    gateway_warpgate_count >= 2 and pylon_count >= 2:
        #     self.finished = True
