import random

from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId


class UpgradesController:
    def __init__(self, bot=None, verbose=False):
        self.verbose = verbose
        self.bot = bot

        self.forge_research_priority = ['ground_weapons', 'shield']

        self.upgrades = {
            'ground_weapons': [
                AbilityId.FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL1,
                AbilityId.FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL2,
                AbilityId.FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL3],
            'ground_armor': [
                AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1,
                AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL2,
                AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL3],
            'shield': [
                AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL1,
                AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL2,
                AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL3]
        }

        self.upgrade_names = {
            AbilityId.FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL1: 'GROUND WEAPONS 1',
            AbilityId.FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL2: 'GROUND WEAPONS 2',
            AbilityId.FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL3: 'GROUND WEAPONS 2',
            AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1: 'GROUND ARMOR 2',
            AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL2: 'GROUND ARMOR 2',
            AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL3: 'GROUND ARMOR 2',
            AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL1: 'SHIELDS 1',
            AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL2: 'SHIELDS 2',
            AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL3: 'SHIELDS 3'
        }

    async def step(self):
        await self.manage_cyberbetics_upgrades()
        await self.manage_forge_upgrades()

    async def manage_cyberbetics_upgrades(self):
        if self.bot.units(UnitTypeId.CYBERNETICSCORE).ready.exists and self.bot.can_afford(AbilityId.RESEARCH_WARPGATE) and not self.bot.researched_warpgate:
            ccore = self.bot.units(UnitTypeId.CYBERNETICSCORE).ready.first
            await self.bot.do(ccore(AbilityId.RESEARCH_WARPGATE))
            self.bot.researched_warpgate = True

            if self.verbose:
                print('%8.2f %3d Researching warpgate' % (self.bot.time, self.bot.supply_used))

    async def manage_forge_upgrades(self):
        for forge in self.bot.units(UnitTypeId.FORGE).ready.noqueue:
            abilities = await self.bot.get_available_abilities(forge)

            for upgrade_type in self.forge_research_priority:
                for upgrade in self.upgrades[upgrade_type]:
                    if upgrade in abilities and self.bot.can_afford(upgrade):
                        if self.verbose:
                            print('%8.2f %3d Researching %s' % (self.bot.time, self.bot.supply_used, self.upgrade_names[upgrade]))

                        await self.bot.do(forge(upgrade))
                        break
