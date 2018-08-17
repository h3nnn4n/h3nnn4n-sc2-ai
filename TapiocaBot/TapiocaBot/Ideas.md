TODO:
 - Harass controller for early 2 adepts + 2 stalkers
 - Harass controller for glaive adepts
 - Warp Prism controller
 - Harass with the warp prism
 - Improve timings. Bot is falling about 20 ~ 30 secs behind in the opening
 - Improve pylon and buildings placement
 - Code a controller for sentries and make it use guardian shield and force fields
 - Write a base controller and make all other inherit from it
 - Improve Expand logic
 - Harass
 - Harass
 - Harass
 - Implement focus fire (for broodlords specially)
 - Move all stategy logic to the coordinator (or a new class)
 - Make the buildings_controller auto expand based on the need of minerals or gas
 - Make the buildings_controller take gas only if needed (consider mineral gas ratio)
 - Add support to prioritize researches (some or all) to the coordinator
 - Logic for observer
 - Improve defense
 - React to cheese
 - Early probe scout
 - Blink back Stalkers
 - Add scouting back (this time in the army manager) (Do we even need it?)
 - Make the code more generic (to allow reuse for other races)
 - Oracle harass
 
FIXME
 - Fix the double expand bug
 - Maybe improve the worker controller? It is already faster than distribute_worker alone
 - Worker_controller is not working as expected (misplaces workers sometimes)
 - Sometimes units go all over the map when attacking (and die after getting picked off in small groups)
 - Sometimes no units are built (seems like a bug after robo prioritization)
 - Not expanding (Or taking forever)

WIP:
 - Buildings controllers should have no strategic logic inside

DONE:
 - Have no (or as little as possible) logic on TapiocaBot.py, everything should be in its own controller
 - Use standard names (controller vs manager)
 - Improve Worker control (instead of using distribute_workers)
 - Worker production has delays
 - Too many workers going to the geyser
 - 2 Gate fast expand
 - Pick up from the basic build order
 - Fix Expand Now breaking the game
 - Research Zealog Legs and Blink
