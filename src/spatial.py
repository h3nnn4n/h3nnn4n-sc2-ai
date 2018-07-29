import random

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer


class SpatialLlama(sc2.BotAI):
    def __init__(self):
        self.verbose = True
        self.expanded = False
        self.researched_warpgate = False

    async def on_step(self, iteration):
        if iteration == 0:
            print('%f Rise and shine' % (self.time))
            return

        if iteration % 37 == 0:
            await self.distribute_workers()
            await self.manage_upgrades()

        if iteration % 7 == 0:
            await self.build_workers()

        if iteration % 23 == 0:
            await self.manage_supply()

        if iteration % 31 == 0:
            await self.build_vespene()

        if iteration % 11 == 0:
            await self.build_structures()

        if iteration % 13 == 0:
            await self.build_army()

        if iteration % 41 == 0:
            await self.defend()
            #await self.attack()

    async def defend(self):
        # Attacks units that get too close to a nexus or a pylon

        for pylon in self.units(PYLON):
            threats = self.known_enemy_units.closer_than(20, pylon.position)
            if threats.exists:
                print('%6.2f found %d threats' % (self.time, threats.amount))
                await self.target_enemy_unit(threats.first)
                break

        for nexus in self.units(NEXUS):
            threats = self.known_enemy_units.closer_than(20, nexus.position)
            if threats.exists:
                print('%6.2f found %d threats' % (self.time, threats.amount))
                await self.target_enemy_unit(threats.first)
                break

    async def target_enemy_unit(self, target):
        # sends all idle units to attack an enemy unit

        zealots = self.units(ZEALOT).idle
        stalkers = self.units(STALKER).idle
        total_units = zealots.amount + stalkers.amount

        # Only sends 1 unit to attack a worker
        is_worker = target.type_id in [PROBE, SCV, DRONE]

        print('%6.2f defending with %d units' % (self.time, total_units))

        for unit_group in [zealots, stalkers]:
            for unit in unit_group:
                if is_worker:
                    await self.do(unit.attack(target))
                    print('------ target is a probe, sending a single unit')
                    return
                else:
                    await self.do(unit.attack(target.position))

    async def attack(self):
        # Attack towards enemy spawn position

        zealots = self.units(ZEALOT).idle
        stalkers = self.units(STALKER).idle
        total_units = zealots.amount + stalkers.amount

        if total_units > 15:
            print('%6.2f Attacking with %d units' % (self.time, total_units))

            for unit_group in [zealots, stalkers]:
                for unit in unit_group:
                    await self.do(unit.attack(self.select_target(self.state)))

    async def build_army(self):

        # Iterates over all gateways
        for gateway in self.units(GATEWAY).ready.noqueue:
            abilities = await self.get_available_abilities(gateway)

            # Checks if the gateway can morph into a warpgate
            if AbilityId.MORPH_WARPGATE in abilities and self.can_afford(AbilityId.MORPH_WARPGATE):
                await self.do(gateway(MORPH_WARPGATE))

            # Else, tries to build a stalker
            elif AbilityId.GATEWAYTRAIN_STALKER in abilities:
                if self.can_afford(STALKER) and self.supply_left > 2:
                    await self.do(gateway.train(STALKER))

            # Else, tries to build a zealot
            elif AbilityId.GATEWAYTRAIN_ZEALOT in abilities:
                if self.can_afford(ZEALOT) and self.supply_left > 2:
                    await self.do(gateway.train(ZEALOT))

        # Iterates over all warpgates and warp in stalkers
        for warpgate in self.units(WARPGATE).ready:
            abilities = await self.get_available_abilities(warpgate)
            if AbilityId.WARPGATETRAIN_ZEALOT in abilities:
                if self.can_afford(STALKER) and self.supply_left > 2:
                    pylon = self.units(PYLON).ready.random  # TODO: Smartly select a pylon. Closest to the enemy base?
                    pos = pylon.position.to2.random_on_distance(4)
                    placement = await self.find_placement(AbilityId.WARPGATETRAIN_STALKER, pos, placement_step=1)

                    if placement is None:
                        print("%6.2f can't place" % (self.time))
                        return

                    await self.do(warpgate.warp_in(STALKER, placement))

    async def build_structures(self):
        # Only start building main structures if there is
        # at least one pylon
        if not self.units(PYLON).ready.exists:
            return
        else:
            pylon = self.units(PYLON).ready.random

        number_of_gateways = self.units(WARPGATE).amount + self.units(GATEWAY).amount

        # Build the first gateway
        if self.can_afford(GATEWAY) and number_of_gateways == 0:
            if self.verbose:
                print('%6.2f starting first gateway' % (self.time))
            await self.build(GATEWAY, near=pylon)

        # Build the cybernetics core after the first gateway is ready
        if self.can_afford(CYBERNETICSCORE) and self.units(CYBERNETICSCORE).amount == 0 and self.units(GATEWAY).ready:
            if self.verbose:
                print('%6.2f starting first gateway' % (self.time))
            await self.build(CYBERNETICSCORE, near=pylon)

        # Build more gateways after the cybernetics core is ready
        if self.can_afford(GATEWAY) and number_of_gateways < 4 and self.units(CYBERNETICSCORE).ready:
            if self.verbose:
                print('%6.2f starting more gateways' % (self.time))
            await self.build(GATEWAY, near=pylon)

        # If there are at least 3 gateways then expand
        if number_of_gateways >= 3:
            if self.units(NEXUS).amount < 2 and not self.already_pending(NEXUS) and self.can_afford(NEXUS):
                if self.verbose:
                    print('%6.2f expanding' % (self.time))

                await self.expand_now()
                #location = await self.get_next_expansion()
                #await self.build(NEXUS, near=location)

                self.expanded = True

    async def manage_upgrades(self):
        if self.units(CYBERNETICSCORE).ready.exists and self.can_afford(RESEARCH_WARPGATE) and not self.researched_warpgate:
            ccore = self.units(CYBERNETICSCORE).ready.first
            await self.do(ccore(RESEARCH_WARPGATE))
            self.researched_warpgate = True

    async def build_workers(self):
        nexus = self.units(NEXUS).ready
        nexus = nexus.noqueue

        if nexus and self.workers.amount < self.units(NEXUS).amount * 22:
            if self.can_afford(PROBE):
                await self.do(nexus.random.train(PROBE))

    async def manage_supply(self):
        nexus = self.units(NEXUS).ready

        if not nexus:
            return

        nexus = nexus.random

        if self.supply_left < 8 and not self.already_pending(PYLON):
            if self.can_afford(PYLON):
                for tries in range(5):  # Only tries 5 different placements
                    pos = await self.find_placement(PYLON, nexus.position, placement_step=2)
                    mineral_fields = self.state.mineral_field.closer_than(8, nexus).closer_than(4, pos)

                    if mineral_fields:
                        continue
                    else:
                        await self.build(PYLON, near=pos)
                        break

    async def build_vespene(self):
        if self.workers.amount < 16:
            return

        for nexus in self.units(NEXUS).ready:
            vgs = self.state.vespene_geyser.closer_than(20.0, nexus)
            for vg in vgs:
                if not self.can_afford(ASSIMILATOR):
                    break

                worker = self.select_build_worker(vg.position)
                if worker is None:
                    break

                if not self.units(ASSIMILATOR).closer_than(1.0, vg).exists:
                    await self.do(worker.build(ASSIMILATOR, vg))

    def select_target(self, state):
        if self.known_enemy_structures.exists:
            return random.choice(self.known_enemy_structures)

        return self.enemy_start_locations[0]


def main():
    sc2.run_game(sc2.maps.get("Abyssal Reef LE"), [
        Bot(Race.Protoss, SpatialLlama()),
        Computer(Race.Protoss, Difficulty.Medium)
    ], realtime=False)

if __name__ == '__main__':
    main()
