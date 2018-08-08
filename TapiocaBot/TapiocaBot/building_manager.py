from sc2.constants import *
import random


class BuildingManager:
    def __init__(self, bot=None, verbose=False):
        self.verbose = verbose
        self.bot = bot

        self.auto_expand_after = 60 * 6.5
        self.auto_expand_mineral_threshold = 22 # Should be 2.5 ~ 3 fully saturated bases
        self.auto_expand_gas_thresehold = 15
        self.gateways_per_nexus = 2
        self.want_to_expand = False

    async def step(self):
        await self.step_auto_build_assimilators()

    async def step_auto_build_assimilators(self):
        total_workers_on_gas = 0
        for geyser in self.bot.geysers:
            total_workers_on_gas += geyser.assigned_harvesters

        if total_workers_on_gas < self.auto_expand_gas_thresehold and self.bot.units(ASSIMILATOR).amount < self.bot.units(NEXUS).amount * 2:
            await self.build_assimilator()

    async def build_structures(self):
        if not self.can('build_structures'):
            return

        # Only start building main structures if there is
        # at least one pylon
        if not self.units(PYLON).ready.exists:
            return
        else:
            pylon = self.units(PYLON).ready.random

        # Build 2 forges
        if self.time > self.start_forge_after and self.units(FORGE).amount < 2:
            if self.can_afford(FORGE) and not self.already_pending(FORGE):
                if self.verbose:
                    print('%6.2f building forge' % (self.time))
                await self.build(FORGE, near=pylon)

        # Build twilight council
        if self.units(FORGE).ready.amount >= 2 and self.units(TWILIGHTCOUNCIL).amount == 0:
            if self.can_afford(TWILIGHTCOUNCIL) and not self.already_pending(TWILIGHTCOUNCIL):
                if self.verbose:
                    print('%6.2f building twilight council' % (self.time))
                await self.build(TWILIGHTCOUNCIL, near=pylon)

    async def build_nexus(self):
        if not self.can('expand'):
            return

        if not self.bot.already_pending(NEXUS) and self.bot.can_afford(NEXUS):
            if self.verbose:
                print('%6.2f expanding' % (self.bot.time))

            await self.bot.expand_now()
            self.want_to_expand = False

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
