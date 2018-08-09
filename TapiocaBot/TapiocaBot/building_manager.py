from sc2.constants import *
import random


class BuildingManager:
    def __init__(self, bot=None, verbose=False):
        self.verbose = verbose
        self.bot = bot

        self.pylons_per_round = 3
        self.start_forge_after = 60 * 5  # seconds
        self.number_of_forges = 2
        self.auto_expand_after = 60 * 6.5
        self.auto_expand_mineral_threshold = 22 # Should be 2.5 ~ 3 fully saturated bases
        self.auto_expand_gas_thresehold = 15
        self.gateways_per_nexus = 2
        self.robotics_facility_per_nexus = 1
        self.want_to_expand = False

    async def step(self):
        await self.step_auto_build_assimilators()
        await self.step_auto_build_gateways()
        await self.step_auto_build_robotics_facility()
        await self.step_auto_build_forge()
        await self.step_auto_build_twilight_council()

    async def step_auto_build_assimilators(self):
        total_workers_on_gas = 0
        for geyser in self.bot.geysers:
            total_workers_on_gas += geyser.assigned_harvesters

        if total_workers_on_gas < self.auto_expand_gas_thresehold and self.bot.units(ASSIMILATOR).amount < self.bot.units(NEXUS).amount * 2:
            await self.build_assimilator()

    async def step_auto_build_gateways(self):
        number_of_gateways = self.bot.units(GATEWAY).amount + self.bot.units(WARPGATE).amount
        pylon = self.get_pylon()

        if pylon is not None and self.bot.can_afford(GATEWAY) and self.bot.units(CYBERNETICSCORE).ready and \
           (number_of_gateways < self.bot.units(NEXUS).amount * self.gateways_per_nexus):
            if self.verbose:
                print('%8.2f %3d Building more Gateways' % (self.bot.time, self.bot.supply_used))
            await self.bot.build(GATEWAY, near=pylon)

    async def step_auto_build_robotics_facility(self):
        pylon = self.get_pylon()

        if pylon is not None and self.bot.can_afford(ROBOTICSFACILITY) and self.bot.units(CYBERNETICSCORE).ready and \
           (self.bot.units(NEXUS).amount > 1) and \
           (self.bot.units(ROBOTICSFACILITY).amount < self.bot.units(NEXUS).amount * self.robotics_facility_per_nexus):
            if self.verbose:
                print('%8.2f %3d Building more Robotics Facility' % (self.bot.time, self.bot.supply_used))
            await self.bot.build(ROBOTICSFACILITY, near=pylon)

    async def step_auto_build_forge(self):
        pylon = self.get_pylon()

        if self.bot.time > self.start_forge_after and self.bot.units(FORGE).amount < self.number_of_forges:
            if self.bot.can_afford(FORGE) and not self.bot.already_pending(FORGE):
                await self.bot.build(FORGE, near=pylon)
                if self.verbose:
                    print('%8.2f %3d Building Forge' % (self.bot.time, self.bot.supply_used))

    async def step_auto_build_twilight_council(self):
        if self.bot.units(FORGE).ready.amount >= 1 and self.bot.units(TWILIGHTCOUNCIL).amount == 0:
            if self.bot.can_afford(TWILIGHTCOUNCIL) and not self.bot.already_pending(TWILIGHTCOUNCIL):
                await self.bot.build(TWILIGHTCOUNCIL, near=pylon)
                if self.verbose:
                    print('%8.2f %3d Building Twilight Council' % (self.bot.time, self.bot.supply_used))

    async def build_nexus(self):
        if not self.can('expand'):
            return

        if not self.bot.already_pending(NEXUS) and self.bot.can_afford(NEXUS):
            await self.bot.expand_now()
            self.want_to_expand = False
            if self.verbose:
                print('%8.2f %3d Expanding' % (self.bot.time, self.bot.supply_used))

    # Finds the pylon with more "space" next to it
    # Where more space == Less units
    # TODO consider "warpable" space
    def pylon_with_less_units(self, distance=4):
        pylons = self.bot.units(PYLON).ready

        good_boy_pylon = None
        units_next_to_good_boy_pylon = float('inf')

        for pylon in pylons:
            units_next_to_candidate_pylon = self.bot.units.closer_than(distance, pylon).amount

            if units_next_to_candidate_pylon < units_next_to_good_boy_pylon:
                good_boy_pylon = pylon
                units_next_to_good_boy_pylon = units_next_to_candidate_pylon

        return good_boy_pylon

    async def build_assimilator(self):
        for nexus in self.bot.units(NEXUS).ready:
            vgs = self.bot.state.vespene_geyser.closer_than(15, nexus)
            for vg in vgs:
                worker = self.bot.select_build_worker(vg.position)
                if worker is None:
                    break

                if not self.bot.units(ASSIMILATOR).closer_than(1.0, vg).exists and self.bot.can_afford(ASSIMILATOR):
                    await self.bot.do(worker.build(ASSIMILATOR, vg))

    async def manage_supply(self):
        for tries in range(5):  # Only tries 5 different placements
            nexus = self.bot.units(NEXUS).ready

            if not nexus:
                return

            nexus = nexus.random

            if self.bot.supply_left < 8 and not self.bot.already_pending(PYLON):
                for _ in range(self.pylons_per_round):
                    if self.bot.can_afford(PYLON):
                        pos = await self.bot.find_placement(PYLON, nexus.position, placement_step=2)
                        mineral_fields = self.bot.state.mineral_field.closer_than(8, nexus).closer_than(4, pos)

                        if mineral_fields:
                            continue
                        else:
                            await self.bot.build(PYLON, near=pos)
                            break

    async def build_pylon(self):
        for tries in range(5):  # Only tries 5 different placements
            nexus = self.bot.units(NEXUS).ready

            if not nexus.exists:
                return

            nexus = nexus.random

            if not self.bot.already_pending(PYLON) and self.bot.can_afford(PYLON):
                pos = await self.bot.find_placement(PYLON, nexus.position, placement_step=2)
                mineral_fields = self.bot.state.mineral_field.closer_than(12, nexus).closer_than(4, pos)

                if mineral_fields:
                    continue
                else:
                    await self.bot.build(PYLON, near=pos)
                    break

    async def expansion_controller(self):
        if self.bot.time > self.auto_expand_after:
            number_of_minerals = sum([self.bot.state.mineral_field.closer_than(10, x).amount for x in self.bot.townhalls])

            if number_of_minerals <= self.auto_expand_mineral_threshold:
                self.want_to_expand = True

    def get_pylon(self):
        pylon = self.bot.units(PYLON).ready
        if pylon.amount > 0:
            return pylon.random
        return None

    def can(self, what):
        if what == 'build_army':
            return not self.want_to_expand

        if what == 'build_structures':
            return not self.want_to_expand

        if what == 'build_assimilator':
            return not self.want_to_expand

        if what == 'expand':
            return self.want_to_expand

        self.console()

    def console(self):
        from IPython.terminal.embed import InteractiveShellEmbed
        ipshell = InteractiveShellEmbed.instance()
        ipshell()
