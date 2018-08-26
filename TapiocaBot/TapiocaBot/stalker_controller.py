import random
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId

from stalker_q_learning_controller import StalkerQLearningController


class StalkerController:
    def __init__(self, bot=None, verbose=False, unit_controller='hardcoded'):
        self.bot = bot
        self.verbose = verbose
        self.unit_controller = unit_controller
        self.controller_map = {
            'hardcoded': self.hardcoded,
            'q_learning': self.q_learning,
        }

        self.stalker_q_learning_controller = StalkerQLearningController(bot=self.bot, verbose=self.verbose)

    async def control(self, unit_tag):
        return await self.controller_map[self.unit_controller](unit_tag)

    async def hardcoded(self, unit_tag):
        # self.bot._client.game_step = 2
        visual_debug = False
        font_size = 14

        unit = self.bot.units.find_by_tag(unit_tag)

        if self.bot.known_enemy_units.exclude_type(self.bot.army_controller.units_to_ignore_attacking).amount == 0:
            if unit.is_idle:
                self.attack_target = self.bot.army_controller.get_something_to_attack()
                await self.bot.do(unit.attack(self.attack_target.position))
            return

        all_enemy_units = self.bot.known_enemy_units.exclude_type(self.bot.army_controller.units_to_ignore_attacking)
        enemy_units = all_enemy_units.not_structure

        if enemy_units.exists:
            closest_unit = enemy_units.closest_to(unit)
        else:
            closest_unit = all_enemy_units.closest_to(unit)

        distance_to_closest_unit = unit.distance_to(closest_unit) - unit.radius / 2 - closest_unit.radius / 2 + 0.1

        step_back_position = unit.position.towards(closest_unit.position, -2)

        our_range = unit.ground_range + unit.radius
        enemy_range = closest_unit.ground_range + closest_unit.radius

        if visual_debug:
            self.bot._client.debug_sphere_out(unit, r=our_range, color=(0, 255, 255))
            self.bot._client.debug_sphere_out(closest_unit, r=enemy_range, color=(255, 0, 0))
            self.bot._client.debug_line_out(unit, closest_unit, color=(127, 127, 255))
            self.bot._client.debug_line_out(unit, step_back_position, color=(127, 0, 255))

        if unit.is_idle:
            self.attack_target = self.bot.army_controller.get_something_to_attack()
            await self.bot.do(unit.attack(self.attack_target.position))

            if visual_debug:
                self.bot._client.debug_text_world('cant see', pos=unit.position3d, size=font_size)
            return

        if our_range > enemy_range:  # Stalker outrange target
            if our_range < distance_to_closest_unit:  # But we are not in range
                if visual_debug:
                    self.bot._client.debug_text_world('too far', pos=unit.position3d, size=font_size)
                if unit.weapon_cooldown > 0:  # If weapon is on cool down we right click the unit
                    await self.bot.do(unit.attack(closest_unit))
                else:  # Else we right click the unit too
                    await self.bot.do(unit.attack(closest_unit))
            elif enemy_range + 0.1 < distance_to_closest_unit:  # They are in our range but we arent in theirs
                if closest_unit.is_structure:  # Get closer to structures
                    if visual_debug:
                        self.bot._client.debug_text_world('atk structure', pos=unit.position3d, size=font_size)
                    if unit.weapon_cooldown > 0 and distance_to_closest_unit > closest_unit.radius + 1:
                        advance_position = unit.position.towards(closest_unit.position, distance=1)
                        await self.bot.do(unit.move(advance_position))
                    else:
                        await self.bot.do(unit.attack(closest_unit))
                else:
                    if our_range - distance_to_closest_unit > 0.75:
                        step_back_position = unit.position.towards(closest_unit.position, -2)
                        if visual_debug:
                            self.bot._client.debug_text_world('closeish', pos=unit.position3d, size=font_size)
                        await self.bot.do(unit.move(step_back_position))
                    else:
                        if visual_debug:
                            self.bot._client.debug_text_world('ideal', pos=unit.position3d, size=font_size)
                        await self.bot.do(unit.attack(closest_unit))
            else:  # We are in their range but we can out range them
                # if unit.weapon_cooldown == 0:  # shoot first
                #     await self.bot.do(unit.attack(closest_unit))
                # else:
                #     distance = enemy_range - distance_to_closest_unit
                #     step_back_position = unit.position.towards(closest_unit.position, -distance)

                #     await self.bot.do(unit.move(step_back_position))
                # distance = enemy_range - distance_to_closest_unit

                abilities = await self.bot.get_available_abilities(unit)

                if unit.shield_percentage < 0.1 and AbilityId.EFFECT_BLINK_STALKER in abilities:
                    blink_back_position = unit.position.towards(closest_unit.position, -8)
                    await self.bot.do(unit(AbilityId.EFFECT_BLINK_STALKER, blink_back_position))
                else:
                    step_back_position = unit.position.towards(closest_unit.position, -1)
                    await self.bot.do(unit.move(step_back_position))

                if visual_debug:
                    self.bot._client.debug_text_world('too close', pos=unit.position3d, size=font_size)
        else:  # we either have the same range or we have less range
            abilities = await self.bot.get_available_abilities(unit)

            if unit.shield_percentage < 0.1 and AbilityId.EFFECT_BLINK_STALKER in abilities:
                blink_back_position = unit.position.towards(closest_unit.position, -8)
                await self.bot.do(unit(AbilityId.EFFECT_BLINK_STALKER, blink_back_position))
            else:
                if enemy_range >= distance_to_closest_unit:
                    if unit.shield_percentage < 0.1 and AbilityId.EFFECT_BLINK_STALKER in abilities:
                        blink_back_position = unit.position.towards(closest_unit.position, -8)
                        await self.bot.do(unit(AbilityId.EFFECT_BLINK_STALKER, blink_back_position))
                        if visual_debug:
                            self.bot._client.debug_text_world('blink', pos=unit.position3d, size=font_size)
                    else:
                        if unit.weapon_cooldown == 0:
                            await self.bot.do(unit.attack(closest_unit))
                            if visual_debug:
                                self.bot._client.debug_text_world('YOLO', pos=unit.position3d, size=font_size)
                        else:
                            step_back_position = unit.position.towards(closest_unit.position, -1)
                            await self.bot.do(unit.move(step_back_position))
                            if visual_debug:
                                self.bot._client.debug_text_world('back', pos=unit.position3d, size=font_size)

    async def q_learning(self, unit_tag):
        # unit = self.bot.units.find_by_tag(unit_tag)
        # abilities = await self.bot.get_available_abilities(unit)
        # can_blink = AbilityId.EFFECT_BLINK_STALKER in abilities

        # await self.bot._client.move_camera(unit.position)  # FIXME
        # ValueError: Protocol message RequestAction has no "action" field.

        action = self.stalker_q_learning_controller.step(unit_tag)

        await self.bot.do(action)
