import random

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer
from sc2.position import Point2

import sys


class UnitMicro:
    def __init__(self, tag, unit_type, bot, scouting=False, defending=False):
        self.tag = tag
        self.unit_type = unit_type
        self.current_target = None
        self.scouting = scouting
        self.defending = defending
        self.attacking = not scouting and not defending
        self.bot = bot

        self.unit = bot.units.find_by_tag(tag)
        self.ground_range = self.unit.ground_range
        self.air_range = self.unit.air_range
        self.sight_range = self.unit.sight_range
        self.can_attack_air = self.unit.can_attack_air
        self.can_attack_ground = self.unit.can_attack_ground

    async def update(self):
        self.unit = self.bot.units.find_by_tag(self.tag)
        if not self.unit is not None:
            return

        near_ground_units = self.bot.known_enemy_units().closer_than(self.ground_range, self.unit)
        near_air_units = self.bot.known_enemy_units().closer_than(self.air_range, self.unit)
        near_structures = self.bot.known_enemy_structures().closer_than(self.ground_range, self.unit)

        target = None

        if near_air_units.exists:
            target = near_air_units.closest_to(self.unit)
        elif near_ground_units.exists:
            target = near_ground_units.closest_to(self.unit)
        elif near_structures.exists:
            target = near_structures.closest_to(self.unit)

        if target is None:
            return

        await self.bot.do(self.unit.attack(target))


class SpatialLlama(sc2.BotAI):
    def __init__(self):
        self.verbose = True
        self.expanded = False
        self.researched_warpgate = False
        self.threat_proximity = 20

        self.attacking_units = set()
        self.attack_target = None
        self.units_available_for_attack = {ZEALOT: 'ZEALOT', STALKER: 'STALKER'}

        self.defending_units = set()
        self.defending_from = set()

        self.scouting_units = set()
        self.number_of_scouting_units = 2
        self.scout_interval = 30  # Seconds
        self.scout_timer = 0
        self.map_size = None

        self.start_forge_after = 240  # seconds - 4min
        self.forge_research_priority = ['ground_weapons', 'shield']

        self.upgrades = {
            'ground_weapons': [
                FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL1,
                FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL2,
                FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL3],
            'ground_armor': [
                FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1,
                FORGERESEARCH_PROTOSSGROUNDARMORLEVEL2,
                FORGERESEARCH_PROTOSSGROUNDARMORLEVEL3],
            'shield' : [
                FORGERESEARCH_PROTOSSSHIELDSLEVEL1,
                FORGERESEARCH_PROTOSSSHIELDSLEVEL2,
                FORGERESEARCH_PROTOSSSHIELDSLEVEL3]
            }

        self.upgrade_names = {
                FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL1: 'GROUND WEAPONS 1',
                FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL2: 'GROUND WEAPONS 2',
                FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL3: 'GROUND WEAPONS 2',
                FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1: 'GROUND ARMOR 2',
                FORGERESEARCH_PROTOSSGROUNDARMORLEVEL2: 'GROUND ARMOR 2',
                FORGERESEARCH_PROTOSSGROUNDARMORLEVEL3: 'GROUND ARMOR 2',
                FORGERESEARCH_PROTOSSSHIELDSLEVEL1: 'SHIELDS 1',
                FORGERESEARCH_PROTOSSSHIELDSLEVEL2: 'SHIELDS 2',
                FORGERESEARCH_PROTOSSSHIELDSLEVEL3: 'SHIELDS 3'
            }

    def on_start(self):
        print('%6.2f Rise and shine' % (0))
        self.map_size = self.game_info.map_size

    async def on_step(self, iteration):
        sys.stdout.flush()

        if iteration == 0:  # Do nothing on the first iteration to avoid
            return          # everything being done at the same time

        if iteration % 121 == 0:
            await self.distribute_workers()

        if iteration % 37 == 0:
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

        if iteration % 17 == 0:
            await self.scout_controller()
            await self.micro_controller()

        if iteration % 41 == 0:
            await self.defend()
            await self.attack()

    async def micro_controller(self):
        for unit in self.attacking_units:
            await unit.update()

    async def scout_controller(self):
        current_time = self.time
        if current_time - self.scout_timer > self.scout_interval:
            self.scout_timer = self.time

            n_scouting_units_assigned = len(self.scouting_units)
            missing_scouting_units = self.number_of_scouting_units - n_scouting_units_assigned

            # Uses the previous assigned scouting units to keep scouting
            for scouting_unit_tag in list(self.scouting_units):
                unit = self.units.find_by_tag(scouting_unit_tag)

                if unit.exists:
                    target = random.sample(list(self.expansion_locations), k=1)[0]
                    await self.do(unit.attack(target))
                else:
                    # If a scouting unit isnt found then it is (most likely) dead
                    # and we need another to replace it
                    self.scouting_units.remove(unit)
                    missing_scouting_units += 1

            if missing_scouting_units > 0:
                idle_stalkers = self.units(STALKER).idle

                if idle_stalkers.exists:
                    print('%6.2f Scouting' % (self.time))

                    # If there is no unit assigned to scouting
                    # the the idle unit furthest from the base
                    for i in range(missing_scouting_units):
                        stalker = idle_stalkers.furthest_to(self.units(NEXUS).first)

                        if stalker:
                            target = random.sample(list(self.expansion_locations), k=1)[0]
                            await self.do(stalker.attack(target))
                            self.scouting_units

                        idle_stalkers = self.units(STALKER).idle
                        if not idle_stalkers.exists:
                            break
                else:
                    pass
                    #print('     - no units to scout')

    async def defend(self):
        # Attacks units that get too close to a nexus or a pylon

        for pylon in self.units(PYLON):
            threats = self.known_enemy_units.closer_than(self.threat_proximity, pylon.position)
            if threats.exists:
                print('%6.2f found %d threats' % (self.time, threats.amount))
                await self.target_enemy_unit(threats.first)
                break

        for nexus in self.units(NEXUS):
            threats = self.known_enemy_units.closer_than(self.threat_proximity, nexus.position)
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
                    print('     - target is a probe, sending a single unit')
                    return
                else:
                    await self.do(unit.attack(target.position))

    async def attack(self):
        # Attack towards enemy spawn position

        total_units = 0
        for unit_type in self.units_available_for_attack.keys():
            total_units += self.units(unit_type).amount

        if total_units > 15:
            print('%6.2f Attacking with %d units' % (self.time, total_units))

            for unit_type in self.units_available_for_attack.keys():
                for unit in self.units(unit_type):
                    self.attacking_units.add(UnitMicro(unit.tag, unit_type, self))
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
                    # Smartly find a good pylon boy to warp in units next to it
                    pylon = self.pylon_with_less_units()
                    pos = pylon.position.to2.random_on_distance(4)
                    placement = await self.find_placement(AbilityId.WARPGATETRAIN_STALKER, pos, placement_step=1)

                    if placement:
                        await self.do(warpgate.warp_in(STALKER, placement))
                    else:
                        # otherwise just brute force it
                        for _ in range(10):  # TODO tweak this
                            pylon = self.units(PYLON).ready.random
                            pos = pylon.position.to2.random_on_distance(4)
                            placement = await self.find_placement(AbilityId.WARPGATETRAIN_STALKER, pos, placement_step=1)

                            if placement is None:
                                print("%6.2f can't place" % (self.time))
                                return

                            await self.do(warpgate.warp_in(STALKER, placement))
                            continue

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

        # Build 2 forges
        if self.time > self.start_forge_after and self.units(FORGE).amount < 2:
            if self.can_afford(FORGE) and not self.already_pending(FORGE):
                if self.verbose:
                    print('%6.2f building forge' % (self.time))
                await self.build(FORGE, near=pylon)

    async def manage_upgrades(self):
        await self.manage_cyberbetics_upgrades()
        await self.manage_forge_upgrades()

    async def manage_cyberbetics_upgrades(self):
        if self.units(CYBERNETICSCORE).ready.exists and self.can_afford(RESEARCH_WARPGATE) and not self.researched_warpgate:
            ccore = self.units(CYBERNETICSCORE).ready.first
            await self.do(ccore(RESEARCH_WARPGATE))
            self.researched_warpgate = True

            if self.verbose:
                print('%6.2f researching warpgate' % (self.time))

    async def manage_forge_upgrades(self):
        for forge in self.units(FORGE).ready.noqueue:
            abilities = await self.get_available_abilities(forge)

            for upgrade_type in self.forge_research_priority:
                for upgrade in self.upgrades[upgrade_type]:
                    sys.stdout.flush()
                    if upgrade in abilities and self.can_afford(upgrade):
                        if self.verbose:
                            print('%6.2f researching %s' % (self.time, self.upgrade_names[upgrade]))

                        await self.do(forge(upgrade))
                        break

    async def build_workers(self):
        nexus = self.units(NEXUS).ready
        nexus = nexus.noqueue

        if nexus and self.workers.amount < self.units(NEXUS).amount * 22:
            if self.can_afford(PROBE):
                await self.do(nexus.random.train(PROBE))

    async def manage_supply(self):
        for tries in range(5):  # Only tries 5 different placements
            nexus = self.units(NEXUS).ready

            if not nexus:
                return

            nexus = nexus.random

            if self.supply_left < 8 and not self.already_pending(PYLON):
                if self.can_afford(PYLON):
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
            vgs = self.state.vespene_geyser.closer_than(20, nexus)
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

    # Finds the pylon with more "space" next to it
    # Where more space == Less units
    # TODO consider "warpable" space
    def pylon_with_less_units(self, distance=4):
        pylons = self.units(PYLON).ready

        good_boy_pylon = None
        units_next_to_good_boy_pylon = float('inf')

        for pylon in pylons:
            units_next_to_candidate_pylon = self.units.closer_than(distance, pylon).amount

            if units_next_to_candidate_pylon < units_next_to_good_boy_pylon:
                good_boy_pylon = pylon
                units_next_to_good_boy_pylon = units_next_to_candidate_pylon

        return good_boy_pylon


def main():
    sc2.run_game(sc2.maps.get("Abyssal Reef LE"), [
        Bot(Race.Protoss, SpatialLlama()),
        Computer(Race.Protoss, Difficulty.Medium)
    ], realtime=False)

if __name__ == '__main__':
    main()
