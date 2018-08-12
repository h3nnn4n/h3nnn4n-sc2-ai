import random
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId


class GatewayController:
    def __init__(self, bot=None, verbose=False, auto_pick=False,
                 can_idle=False, auto_morph_to_warpgate=False):
        self.verbose = verbose
        self.bot = bot
        self.auto_pick = True
        self.can_idle = can_idle

        self.auto_morph_to_warpgate = auto_morph_to_warpgate

        self.unit_priority = {}

    async def step(self):
        await self.morph_gateways_into_warpgates()

        if self.bot.supply_left >= 2:
            await self.step_gateways()
            await self.step_warpgates()

    async def step_gateways(self):
        if not self.bot.coordinator.can('build_gateway_units'):
            return

        gateways = self.bot.units(UnitTypeId.GATEWAY).ready.noqueue

        for gateway in gateways:
            next_unit = self.get_next_unit()

            if next_unit is None:
                return

            if self.bot.can_afford(next_unit):
                await self.bot.do(gateway.train(next_unit))
                if self.verbose:
                    print('%8.2f %3d Building %s' % (
                        self.bot.time, self.bot.supply_used, next_unit))

    async def step_warpgates(self):
        if not self.bot.coordinator.can('build_gateway_units'):
            return

        for warpgate in self.bot.units(UnitTypeId.WARPGATE).ready:
            abilities = await self.bot.get_available_abilities(warpgate)
            if AbilityId.WARPGATETRAIN_ZEALOT in abilities:
                next_unit = self.get_next_unit()
                if next_unit is not None and self.bot.can_afford(next_unit) and self.bot.supply_left > 2:
                    # Smartly find a good pylon boy to warp in units next to it
                    pylon = self.bot.building_manager.pylon_with_less_units()
                    pos = pylon.position.to2.random_on_distance(4)
                    placement = await self.bot.find_placement(AbilityId.WARPGATETRAIN_STALKER, pos, placement_step=1)

                    if placement:
                        await self.bot.do(warpgate.warp_in(next_unit, placement))
                        return True
                    else:
                        # otherwise just brute force it
                        for _ in range(10):  # FIXME I dont think this should ever need to run
                            pylon = self.bot.units(UnitTypeId.PYLON).ready.random
                            pos = pylon.position.to2
                            placement = await self.bot.find_placement(AbilityId.WARPGATETRAIN_STALKER, pos, placement_step=1)

                            if placement is None:
                                if self.verbose:
                                    print("%6.2f can't place" % (self.bot.time))
                                return False

                            await self.bot.do(warpgate.warp_in(next_unit, placement))
                            return True
        return False

    def add_order(self, command):
        unit, priority = command
        self.unit_priority[unit] = priority

    def get_next_unit(self):
        unit_types = self.unit_priority.keys()
        unit_ratio = {}
        unit_priority_ratio = {}
        total_units = 0
        priority_divident = 0

        for unit_type in unit_types:
            unit_ratio[unit_type] = self.bot.units(unit_type).amount
            unit_priority_ratio[unit_type] = self.unit_priority[unit_type]
            total_units += unit_ratio[unit_type]
            priority_divident += self.unit_priority[unit_type]

        if total_units > 0 and priority_divident > 0:
            for unit_type in unit_types:
                unit_ratio[unit_type] /= total_units
                unit_priority_ratio[unit_type] /= priority_divident

            for unit_type in unit_types:
                if unit_ratio[unit_type] < unit_priority_ratio[unit_type]:
                    return unit_type

        return random.sample(unit_types, k=1)[0]

    async def morph_gateways_into_warpgates(self):
        if self.auto_morph_to_warpgate:
            for gateway in self.bot.units(UnitTypeId.GATEWAY).ready:
                abilities = await self.bot.get_available_abilities(gateway)
                if AbilityId.MORPH_WARPGATE in abilities and self.bot.can_afford(AbilityId.MORPH_WARPGATE):
                    await self.bot.do(gateway(AbilityId.MORPH_WARPGATE))
