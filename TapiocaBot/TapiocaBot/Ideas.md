# TODO

- Use a cluster analysis for build orders
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
- Add scouting back (this time in the army manager) (Do we even need it?)
- Make the code more generic (to allow reuse for other races)
- Oracle harass
- Allow 3gate stalker all in to expand and go on with the game if the presure wont break in
- Scout for proxy pylons
- Scout for Dark Templas and adapt
- Send 2 probes to attack enemy workers that get too close to our pylons/nexus
- Versus terran find a way to deal with the tanks
- Versus zerg (hjax specially) find a way to deal with mass lings
- Improve retreat code
- Avoid microing back into static defense range
- Add a failsafe to the worker scouting logic so it doesnt kill all the workers while trying to scout
- Micro scouting workers to keep they alive for as long as possible

## FIXME

- Fix the double expand bug
- Maybe improve the worker controller? It is already faster than distribute_worker alone
- Worker_controller is not working as expected (misplaces workers sometimes)
- Sometimes units go all over the map when attacking (and die after getting picked off in small groups)
- Sometimes no units are built (seems like a bug after robo prioritization)
- Not expanding (Or taking forever)
- Fix one forge taking 2 upgrades while one is idle
- Fix expanding blocking other things when it could not
- Consider distance and range for stalker micro (i.e ravager can attack even if ling in the front cant)
- Move stalkers out of the way then others are trying to blink back
- Improve stalker army control
- Enable stalker micro as soon as it is warped in

### WIP

- Q Learning for stalker micro
- Q Learning should learn how to kill without dying and not how to flee

- Avoid static defense
- Probe micro
- React to early cheese. Attack proxy structures with probes + Attack scouting workers

- Buildings controllers should have no strategic logic inside

#### DONE

- Fix debugger controller
- Early Scout with probes
- Stalker micro
- Ignore zergs eggs as targets
- Fix twilight council sometimes (or all) not being built when 3gate blink stalker all in
- Add a blinkstalker all in
- Blink back Stalkers
- Have no (or as little as possible) logic on TapiocaBot.py, everything should be in its own controller
- Use standard names (controller vs manager)
- Improve Worker control (instead of using distribute_workers)
- Worker production has delays
- Too many workers going to the geyser
- 2 Gate fast expand
- Pick up from the basic build order
- Fix Expand Now breaking the game
- Research Zealog Legs and Blink

#### RIP

- Unit tests for q_learning core functions
