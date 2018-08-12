import random
from sc2.ids.unit_typeid import UnitTypeId


class BuildingManager:
    def __init__(self, bot=None, verbose=False):
        self.verbose = verbose
        self.bot = bot

        self.pylons_per_round = 3
        self.start_forge_after = 60 * 5  # seconds
        self.number_of_forges = 2
        self.auto_expand_after = 60 * 6.5
        self.auto_expand_mineral_threshold = 22  # Should be 2.5 ~ 3 fully saturated bases
        self.auto_expand_gas_thresehold = 15
        self.gateways_per_nexus = 2
        self.robotics_facility_per_nexus = 1

    async def step(self):
        await self.step_auto_build_assimilators()
        await self.step_auto_build_gateways()
        await self.step_auto_build_robotics_facility()
        await self.step_auto_build_forge()
        await self.step_auto_build_twilight_council()

    async def step_auto_build_assimilators(self):
        if not self.bot.coordinator.can('build'):
            return

        total_workers_on_gas = 0
        for geyser in self.bot.geysers:
            total_workers_on_gas += geyser.assigned_harvesters

        number_of_assimilators = self.bot.units(UnitTypeId.ASSIMILATOR).amount
        number_of_nexus = self.bot.units(UnitTypeId.NEXUS).amount

        if total_workers_on_gas < self.auto_expand_gas_thresehold and \
           number_of_assimilators < number_of_nexus * 2:
            await self.build_assimilator()

    async def step_auto_build_gateways(self):
        if not self.bot.coordinator.can('build'):
            return

        number_of_gateways = self.bot.units(UnitTypeId.GATEWAY).amount + \
            self.bot.units(UnitTypeId.WARPGATE).amount
        pylon = self.get_pylon()

        if pylon is None:
            return

        if self.bot.can_afford(UnitTypeId.GATEWAY) and self.bot.units(UnitTypeId.CYBERNETICSCORE).ready and \
           (number_of_gateways < self.bot.units(UnitTypeId.NEXUS).amount * self.gateways_per_nexus):
            if self.verbose:
                print('%8.2f %3d Building more Gateways' % (self.bot.time, self.bot.supply_used))
            await self.bot.build(UnitTypeId.GATEWAY, near=pylon)

    async def step_auto_build_robotics_facility(self):
        if not self.bot.coordinator.can('build'):
            return

        pylon = self.get_pylon()

        if pylon is None:
            return

        number_of_nexus = self.bot.units(UnitTypeId.NEXUS).amount
        number_of_robos = self.bot.units(UnitTypeId.ROBOTICSFACILITY).amount

        if self.bot.can_afford(UnitTypeId.ROBOTICSFACILITY) and self.bot.units(UnitTypeId.CYBERNETICSCORE).ready and \
           (self.bot.units(UnitTypeId.NEXUS).amount > 1) and \
           (number_of_robos < number_of_nexus * self.robotics_facility_per_nexus):
            if self.verbose:
                print('%8.2f %3d Building more Robotics Facility' % (self.bot.time, self.bot.supply_used))
            await self.bot.build(UnitTypeId.ROBOTICSFACILITY, near=pylon)

    async def step_auto_build_forge(self):
        if not self.bot.coordinator.can('build'):
            return

        pylon = self.get_pylon()

        if pylon is None:
            return

        number_of_forges = self.bot.units(UnitTypeId.FORGE).amount

        if self.bot.time > self.start_forge_after and number_of_forges < self.number_of_forges:
            if self.bot.can_afford(UnitTypeId.FORGE) and not self.bot.already_pending(UnitTypeId.FORGE):
                await self.bot.build(UnitTypeId.FORGE, near=pylon)
                if self.verbose:
                    print('%8.2f %3d Building Forge' % (self.bot.time, self.bot.supply_used))

    async def step_auto_build_twilight_council(self):
        if not self.bot.coordinator.can('build'):
            return

        pylon = self.get_pylon()

        if pylon is None:
            return

        number_of_forges = self.bot.units(UnitTypeId.FORGE).ready.amount
        number_of_twilights = self.bot.units(UnitTypeId.TWILIGHTCOUNCIL).amount

        if number_of_forges >= 1 and number_of_twilights == 0:
            if self.bot.can_afford(UnitTypeId.TWILIGHTCOUNCIL) and \
               not self.bot.already_pending(UnitTypeId.TWILIGHTCOUNCIL):
                await self.bot.build(UnitTypeId.TWILIGHTCOUNCIL, near=pylon)
                if self.verbose:
                    print('%8.2f %3d Building Twilight Council' % (self.bot.time, self.bot.supply_used))

    async def build_nexus(self):
        if not self.bot.coordinator.can('expand'):
            return

        if not self.bot.already_pending(UnitTypeId.NEXUS) and self.bot.can_afford(UnitTypeId.NEXUS):
            await self.bot.expand_now()
            self.bot.coordinator.new_priority(None)
            if self.verbose:
                print('%8.2f %3d Expanding' % (self.bot.time, self.bot.supply_used))

    # Finds the pylon with more "space" next to it
    # Where more space == Less units
    # TODO consider "warpable" space
    def pylon_with_less_units(self, distance=4):
        pylons = self.bot.units(UnitTypeId.PYLON).ready

        good_boy_pylon = None
        units_next_to_good_boy_pylon = float('inf')

        for pylon in pylons:
            units_next_to_candidate_pylon = self.bot.units.closer_than(distance, pylon).amount

            if units_next_to_candidate_pylon < units_next_to_good_boy_pylon:
                good_boy_pylon = pylon
                units_next_to_good_boy_pylon = units_next_to_candidate_pylon

        return good_boy_pylon

    async def build_assimilator(self):
        for nexus in self.bot.units(UnitTypeId.NEXUS).ready:
            vgs = self.bot.state.vespene_geyser.closer_than(15, nexus)
            for vg in vgs:
                worker = self.bot.select_build_worker(vg.position)
                if worker is None:
                    break

                if not self.bot.units(UnitTypeId.ASSIMILATOR).closer_than(1.0, vg).exists and \
                   self.bot.can_afford(UnitTypeId.ASSIMILATOR):
                    await self.bot.do(worker.build(UnitTypeId.ASSIMILATOR, vg))

    async def manage_supply(self):
        for _ in range(5):  # Only tries 5 different placements
            nexus = self.bot.units(UnitTypeId.NEXUS).ready

            if not nexus:
                return

            nexus = nexus.random

            if self.bot.supply_left < 8 and not self.bot.already_pending(UnitTypeId.PYLON):
                for _ in range(self.pylons_per_round):
                    if self.bot.can_afford(UnitTypeId.PYLON):
                        pos = await self.bot.find_placement(UnitTypeId.PYLON, nexus.position, placement_step=2)
                        mineral_fields = self.bot.state.mineral_field.closer_than(8, nexus).closer_than(4, pos)

                        if mineral_fields:
                            continue
                        else:
                            await self.bot.build(UnitTypeId.PYLON, near=pos)
                            break

    async def build_pylon(self):
        for _ in range(5):  # Only tries 5 different placements
            nexus = self.bot.units(UnitTypeId.NEXUS).ready

            if not nexus.exists:
                return

            nexus = nexus.random

            if not self.bot.already_pending(UnitTypeId.PYLON) and self.bot.can_afford(UnitTypeId.PYLON):
                pos = await self.bot.find_placement(UnitTypeId.PYLON, nexus.position, placement_step=2)
                mineral_fields = self.bot.state.mineral_field.closer_than(12, nexus).closer_than(4, pos)

                if mineral_fields:
                    continue
                else:
                    await self.bot.build(UnitTypeId.PYLON, near=pos)
                    break

    async def expansion_controller(self):
        if self.bot.time > self.auto_expand_after:
            number_of_minerals = sum([
                self.bot.state.mineral_field.closer_than(10, x).amount
                for x in self.bot.townhalls
            ])

            if number_of_minerals <= self.auto_expand_mineral_threshold:
                print('%8.2f %3d WANT TO EXPAND' % (self.bot.time, self.bot.supply_used))
                self.bot.coordinator.new_priority('expand')

    def get_pylon(self):
        pylon = self.bot.units(UnitTypeId.PYLON).ready
        if pylon.amount > 0:
            return pylon.random
        return None
