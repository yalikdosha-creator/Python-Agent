#!/usr/bin/env python3
"""Campaign builder: defines all 60 stages + reference solutions, verifies each
solution against the live sandbox via /api/run, then emits the server LEVELS
block and the client JS levels array. One new Python skill every 5 stages:
  Ch1 (1-5)   Movement      agent.step / agent.collect
  Ch2 (6-10)  Turning       agent.turn
  Ch3 (11-15) Loops         for / range        [HQ requirement: a loop]
  Ch4 (16-20) If & sensors  if / wall_ahead    [HQ requirement: an if check]
  Ch5 (21-25) Keys & doors  agent.interact     [locked doors force it]
  Ch6 (26-30) Cameras       disable_camera     [camera gates force it]
  Ch7 (31-35) Functions     def                [HQ requirement: a def]
  Ch8 (36-40) Variables     n = 3 / n = n + 1  [HQ requirement: a variable]
  Ch9 (41-45) While loops   while condition:   [HQ requirement: a while loop]
  Ch10 (46-50) Logic        and / or / not     [HQ requirement: combined conditions]
  Ch11 (51-55) Lists        [..] / zip         [HQ requirement: a list]
  Ch12 (56-60) Arguments    def hop(n):        [HQ requirement: function arguments]
"""
import json, re, sys, urllib.request

def L(id, title, short, tag, desc, objective, note, cols, rows, start, exit,
      walls=(), doors=(), cameras=(), items=(), solution="", require=None):
    return dict(id=id, title=title, short=short, tag=tag, desc=desc,
                objective=objective, note=note, cols=cols, rows=rows,
                start=list(start), exit=list(exit),
                walls=[list(w) for w in walls],
                doors=[dict(d) for d in doors],
                cameras=[dict(c) for c in cameras],
                items=[dict(i) for i in items],
                solution=solution, require=require)

LEVELS = [
 # ---------- Chapter 1: Movement (1-5) ----------
 L(1,'First Steps','Step & collect','MOVEMENT',
   'Your first field op. A data case sits ahead in the corridor — walk to it, pick it up, and reach extraction.',
   'Collect the intel, then step onto EX.',
   'Skill 1 of 12 — MOVEMENT: agent.step(n) walks forward n tiles; agent.collect() picks up an item. Count the tiles between agent and the case before you choose the number.',
   8,5,(1,2),(6,2),items=[dict(type='intel',x=3,y=2,label='Intel case')],
   solution='agent.step(2)\nagent.collect()\nagent.step(3)'),
 L(2,'Longer Route','Count your steps','MOVEMENT',
   'Same corridor, longer walk. Count the tiles carefully — one step command can cover many tiles.',
   'Reach the intel, collect it, and continue to the exit.',
   'Practice: agent.step(n) takes any number of tiles. Count before you code: from the agent to the case, then from the case to EX.',
   10,5,(1,2),(8,2),items=[dict(type='intel',x=5,y=2,label='Intel case')],
   solution='agent.step(4)\nagent.collect()\nagent.step(3)'),
 L(3,'Twin Pickup','Two cases','MOVEMENT',
   'Two intel cases were dropped in the same corridor. Grab both on your way to extraction.',
   'Collect both intel cases, then reach EX.',
   'Practice: stop on each case and run agent.collect() — one collect per case. Count the gap between the two cases separately.',
   11,5,(1,2),(9,2),items=[dict(type='intel',x=3,y=2,label='Intel case'),dict(type='intel',x=7,y=2,label='Intel case')],
   solution='agent.step(2)\nagent.collect()\nagent.step(4)\nagent.collect()\nagent.step(2)'),
 L(4,'The Long Hall','Big numbers','MOVEMENT',
   'The longest hall in the training wing. A single agent.step() can carry you across most of it.',
   'Collect the intel and reach extraction.',
   'Practice: bigger numbers in agent.step(n) mean fewer commands. Efficiency already matters for the action star.',
   12,5,(1,2),(10,2),items=[dict(type='intel',x=6,y=2,label='Intel case')],
   solution='agent.step(5)\nagent.collect()\nagent.step(4)'),
 L(5,'Movement Mastery','Final drill','MOVEMENT',
   'Movement exam: two cases, one long corridor, and a tight action budget. Show HQ you have mastered walking and collecting.',
   'Collect both intel cases and extract with actions to spare.',
   'Mastery drill: movement only. Count every gap once, write the three walks and two collects, and you are done. From Stage 6 you will learn to turn.',
   13,5,(1,2),(11,2),items=[dict(type='intel',x=4,y=2,label='Intel case'),dict(type='intel',x=10,y=2,label='Intel case')],
   solution='agent.step(3)\nagent.collect()\nagent.step(6)\nagent.collect()\nagent.step(1)'),

 # ---------- Chapter 2: Turning (6-10) ----------
 L(6,'First Turn','Turn & face','TURNING',
   'The exit is around a corner. Walking straight is no longer enough — it is time to learn turning.',
   'Collect the package, turn toward the exit, and extract.',
   'Skill 2 of 12 — TURNING: agent.turn("left") and agent.turn("right") rotate the agent 90 degrees in place. Turn first, then step — the arrow shows where the agent will walk.',
   8,7,(1,4),(6,2),items=[dict(type='intel',x=3,y=4,label='Intel case')],
   solution='agent.step(2)\nagent.collect()\nagent.turn("left")\nagent.step(2)\nagent.turn("right")\nagent.step(3)'),
 L(7,'Two Corners','Double turn','TURNING',
   'Two corners guard this route. Plan both turns before the agent takes a single step.',
   'Collect the intel and walk the L-route to EX.',
   'Practice: each corner is one turn plus one walk. Right turns go clockwise, left turns counter-clockwise — watch the arrow.',
   9,6,(1,1),(2,3),items=[dict(type='intel',x=6,y=1,label='Intel case')],
   solution='agent.step(5)\nagent.collect()\nagent.turn("right")\nagent.step(2)\nagent.turn("right")\nagent.step(4)'),
 L(8,'The Square','Full loop','TURNING',
   'Walk the perimeter of a square and come home. Three right turns bring you back to where you started — with the intel.',
   'Collect the intel and return to the start tile, which is also EX.',
   'Practice: four sides, three turns. The extraction point is the tile you started on, so the route is a closed loop.',
   8,6,(1,1),(1,4),items=[dict(type='intel',x=6,y=1,label='Intel case')],
   solution='agent.step(5)\nagent.collect()\nagent.turn("right")\nagent.step(3)\nagent.turn("right")\nagent.step(5)\nagent.turn("right")\nagent.step(3)'),
 L(9,'Zigzag Stairs','Climb the steps','TURNING',
   'A staircase route to the roof exit. Alternate turns build the zigzag — no loops yet, just clean turning.',
   'Zigzag up to the intel and extract.',
   'Practice: the pattern is step-step, turn left, step, turn right — repeated by hand. In Chapter 3 you will automate exactly this pattern.',
   10,7,(1,5),(8,2),items=[dict(type='intel',x=7,y=2,label='Intel case')],
   solution='agent.step(2)\nagent.turn("left")\nagent.step(1)\nagent.turn("right")\nagent.step(2)\nagent.turn("left")\nagent.step(1)\nagent.turn("right")\nagent.step(2)\nagent.turn("left")\nagent.step(1)\nagent.collect()\nagent.turn("right")\nagent.step(1)'),
 L(10,'Turning Mastery','Six-corner op','TURNING',
   'Turning exam: two cases on a winding route. Every tile of this one is earned with turns.',
   'Collect both intel cases and extract.',
   'Mastery drill: turning. Trace the whole route on the map first — write down each walk and each turn before coding. From Stage 11 you will learn loops.',
   11,6,(1,3),(9,3),items=[dict(type='intel',x=3,y=1,label='Intel case'),dict(type='intel',x=7,y=3,label='Intel case')],
   solution='agent.step(2)\nagent.turn("left")\nagent.step(2)\nagent.collect()\nagent.turn("right")\nagent.step(4)\nagent.turn("right")\nagent.step(2)\nagent.collect()\nagent.turn("left")\nagent.step(2)'),

 # ---------- Chapter 3: Loops (11-15) — HQ requires a loop ----------
 L(11,'Chain Pickup','First loop','LOOPS',
   'Three cases, evenly spaced. Writing every step by hand works — but HQ will not accept it: this op must run a loop.',
   'Use a for loop to collect all three cases, then extract.',
   'Skill 3 of 12 — LOOPS: for i in range(n): repeats the indented commands n times. HQ REQUIREMENT: your program must contain a for loop — hand-walked code is rejected here.',
   11,5,(1,2),(9,2),items=[dict(type='intel',x=3,y=2,label='Intel case'),dict(type='intel',x=5,y=2,label='Intel case'),dict(type='intel',x=7,y=2,label='Intel case')],
   solution='for i in range(3):\n    agent.step(2)\n    agent.collect()\nagent.step(2)',
   require='loop'),
 L(12,'Staircase Loop','Looped zigzag','LOOPS',
   'The zigzag from Stage 9, longer. This time the repeating pattern belongs inside a loop — HQ requires one.',
   'Use one loop to climb the stairs to EX.',
   'Practice: put the whole repeating pattern — steps and turns — inside one for loop. The indented block runs once per count of range(3).',
   10,7,(1,5),(8,2),items=[],
   solution='for i in range(3):\n    agent.step(2)\n    agent.turn("left")\n    agent.step(1)\n    agent.turn("right")\nagent.step(1)',
   require='loop'),
 L(13,'Supply Chain','Pickup line','LOOPS',
   'A supply line runs down the corridor with a case every two tiles, then climbs a tower to the roof exit.',
   'Loop along the pickup line, turn, and loop up the tower.',
   'Practice: agent.step(n) cannot help here — there is a case every two tiles, so the pattern is step(2), collect, repeated. One loop per straight run.',
   9,7,(1,5),(7,1),items=[dict(type='intel',x=3,y=5,label='Intel case'),dict(type='intel',x=5,y=5,label='Intel case'),dict(type='intel',x=7,y=5,label='Intel case')],
   solution='for i in range(3):\n    agent.step(2)\n    agent.collect()\nagent.turn("left")\nfor i in range(4):\n    agent.step(1)',
   require='loop'),
 L(14,'Guard Patrol','Square patrol','LOOPS',
   'Patrol the perimeter of the compound, collecting intel at every corner, and return to base. One loop does the whole rounds.',
   'Use a loop to patrol all four sides and extract where you started.',
   'Practice: the same three commands repeat on every side of the square — step, collect, turn right. Perfect loop material.',
   6,6,(1,1),(1,1),items=[dict(type='intel',x=4,y=1,label='Intel case'),dict(type='intel',x=4,y=4,label='Intel case'),dict(type='intel',x=1,y=4,label='Intel case')],
   solution='for i in range(4):\n    agent.step(3)\n    agent.collect()\n    agent.turn("right")',
   require='loop'),
 L(15,'Loop Mastery','Supply run','LOOPS',
   'Loop exam: a supply line climbs the ridge with a case waiting at every switchback.',
   'One loop collects every case on the climb. Extract at the top.',
   'Mastery drill: loops. The climb repeats the same five commands four times — write them once, indented, under range(4). From Stage 16 your agent learns to make decisions with if.',
   12,8,(1,6),(10,2),items=[dict(type='intel',x=3,y=6,label='Intel case'),dict(type='intel',x=5,y=5,label='Intel case'),dict(type='intel',x=7,y=4,label='Intel case'),dict(type='intel',x=9,y=3,label='Intel case')],
   solution='for i in range(4):\n    agent.step(2)\n    agent.collect()\n    agent.turn("left")\n    agent.step(1)\n    agent.turn("right")\nagent.step(1)',
   require='loop'),

 # ---------- Chapter 4: If & sensors (16-20) — HQ requires an if check ----------
 L(16,'Check the Wall','First if','DECISIONS',
   'Two walls block this corridor at different points. Instead of memorizing detours, let the agent check ahead and decide.',
   'Loop down the corridor and use if + agent.wall_ahead() to detour each wall.',
   'Skill 4 of 12 — DECISIONS: if runs the indented commands only when its condition is true. agent.wall_ahead() reports whether the next tile is blocked. HQ REQUIREMENT: your program must contain an if check.',
   13,7,(1,3),(11,3),walls=[(4,3),(8,3)],items=[dict(type='intel',x=10,y=3,label='Intel case')],
   solution='for i in range(2):\n    agent.step(2)\n    if agent.wall_ahead():\n        agent.turn("left")\n        agent.step(1)\n        agent.turn("right")\n        agent.step(2)\n        agent.turn("right")\n        agent.step(1)\n        agent.turn("left")\nagent.step(1)\nagent.collect()\nagent.step(1)',
   require='if'),
 L(17,'Fork Logic','if / else','DECISIONS',
   'A wall may block the lane ahead — or it may not. Write both plans and let the agent pick the right one at runtime.',
   'Check the lane with if / else and take whichever side is clear.',
   'Practice: else holds the plan for when the condition is false. Only one branch ever runs — but a good agent writes both.',
   10,6,(1,2),(8,4),walls=[(4,2)],items=[dict(type='intel',x=7,y=4,label='Intel case')],
   solution='agent.step(2)\nif agent.wall_ahead():\n    agent.turn("right")\n    agent.step(2)\n    agent.turn("left")\nelse:\n    agent.step(2)\nagent.step(4)\nagent.collect()\nagent.step(1)',
   require='if'),
 L(18,'Sensor Sweep','Loop + if','DECISIONS',
   'Two walls hide in one corridor. The loop does the walking; the if reacts to whatever it finds.',
   'Combine one loop and an if check to sweep past both walls.',
   'Practice: loops and decisions work together — the loop walks a fixed number of tiles, the if handles the surprise. The same if serves both walls.',
   12,6,(1,3),(10,3),walls=[(4,3),(7,3)],items=[dict(type='intel',x=9,y=3,label='Intel case')],
   solution='agent.step(1)\nfor i in range(2):\n    agent.step(1)\n    if agent.wall_ahead():\n        agent.turn("left")\n        agent.step(1)\n        agent.turn("right")\n        agent.step(2)\n        agent.turn("right")\n        agent.step(1)\n        agent.turn("left")\nagent.step(1)\nagent.collect()\nagent.step(1)',
   require='if'),
 L(19,'Double Detour','Two checks','DECISIONS',
   'Two walls, two intel cases, two decisions. Not every mission fits a loop — sometimes you check, detour, and collect by hand.',
   'Use two separate if checks to weave past both walls and grab both cases.',
   'Practice: reuse the detour pattern — check, go over, come back down. This route is irregular, so two hand-written if checks beat one loop.',
   13,6,(1,3),(11,3),walls=[(4,3),(8,3)],items=[dict(type='intel',x=6,y=3,label='Intel case'),dict(type='intel',x=10,y=3,label='Intel case')],
   solution='agent.step(2)\nif agent.wall_ahead():\n    agent.turn("left")\n    agent.step(1)\n    agent.turn("right")\n    agent.step(2)\n    agent.turn("right")\n    agent.step(1)\n    agent.turn("left")\nagent.step(1)\nagent.collect()\nagent.step(1)\nif agent.wall_ahead():\n    agent.turn("left")\n    agent.step(1)\n    agent.turn("right")\n    agent.step(2)\n    agent.turn("right")\n    agent.step(1)\n    agent.turn("left")\nagent.step(1)\nagent.collect()\nagent.step(1)',
   require='if'),
 L(20,'If Mastery','The gauntlet','DECISIONS',
   'Decision exam: three walls guard the gauntlet. One loop with an if inside clears all three.',
   'Loop down the corridor and detour every wall you detect.',
   'Mastery drill: if checks. One loop, one if, three walls — the same two lines of thinking handle every obstacle. From Stage 21 locked doors join the campaign.',
   14,6,(1,4),(12,4),walls=[(3,4),(6,4),(9,4)],items=[dict(type='intel',x=11,y=4,label='Intel case')],
   solution='for i in range(3):\n    agent.step(1)\n    if agent.wall_ahead():\n        agent.turn("left")\n        agent.step(1)\n        agent.turn("right")\n        agent.step(2)\n        agent.turn("right")\n        agent.step(1)\n        agent.turn("left")\nagent.step(1)\nagent.collect()\nagent.step(1)',
   require='if'),

 # ---------- Chapter 5: Keys & doors (21-25) ----------
 L(21,'Keycard Entry','First door','ACCESS',
   'A locked door seals the corridor. Find the access badge, then open the way the professional way.',
   'Collect the badge, open the door, take the intel, extract.',
   'Skill 5 of 12 — KEYS & DOORS: agent.interact() opens a locked door when you hold its badge and stand beside it. The door physically blocks the route — there is no way around.',
   9,5,(1,2),(7,2),doors=[dict(id='vault',x=4,y=2)],items=[dict(type='badge',x=2,y=2,label='Access badge'),dict(type='intel',x=6,y=2,label='Intel case')],
   solution='agent.step(1)\nagent.collect()\nagent.step(1)\nagent.interact()\nagent.step(3)\nagent.collect()\nagent.step(1)'),
 L(22,'Double Gate','Two locks','ACCESS',
   'One badge, two gates. The same interact command works on every lock you hold the key for.',
   'Open both gates and retrieve the intel.',
   'Practice: agent.interact() opens whichever locked door you are standing beside — one badge is enough for both.',
   12,5,(1,2),(10,2),doors=[dict(id='vault1',x=4,y=2),dict(id='vault2',x=7,y=2)],items=[dict(type='badge',x=2,y=2,label='Access badge'),dict(type='intel',x=9,y=2,label='Intel case')],
   solution='agent.step(1)\nagent.collect()\nagent.step(1)\nagent.interact()\nagent.step(3)\nagent.interact()\nagent.step(3)\nagent.collect()\nagent.step(1)'),
 L(23,'Key Detour','Badge off-route','ACCESS',
   'The badge is not on the main corridor this time — fetch it around the corner, then come back for the door.',
   'Detour for the badge, open the door, extract.',
   'Practice: doors and turns together. Plan the whole route before you run: badge first, then the door.',
   10,7,(1,3),(8,3),doors=[dict(id='gate',x=5,y=3)],items=[dict(type='badge',x=3,y=1,label='Access badge'),dict(type='intel',x=7,y=3,label='Intel case')],
   solution='agent.step(2)\nagent.turn("left")\nagent.step(2)\nagent.collect()\nagent.turn("right")\nagent.step(1)\nagent.turn("right")\nagent.step(2)\nagent.turn("left")\nagent.interact()\nagent.step(3)\nagent.collect()\nagent.step(1)'),
 L(24,'Guarded Door','Door + wall','ACCESS',
   'A door and a wall share this corridor. Open the lock, then detour the wall — skills stack now.',
   'Open the door, detour the wall, take the intel.',
   'Practice: badge first, door second, wall third. The wall detour is the same up-over-down pattern from Chapter 4.',
   11,6,(1,3),(9,3),walls=[(6,3)],doors=[dict(id='gate',x=4,y=3)],items=[dict(type='badge',x=2,y=3,label='Access badge'),dict(type='intel',x=8,y=3,label='Intel case')],
   solution='agent.step(1)\nagent.collect()\nagent.step(1)\nagent.interact()\nagent.step(2)\nagent.turn("left")\nagent.step(1)\nagent.turn("right")\nagent.step(2)\nagent.turn("right")\nagent.step(1)\nagent.turn("left")\nagent.step(1)\nagent.collect()\nagent.step(1)'),
 L(25,'Door Mastery','Two floors','ACCESS',
   'Door exam: two floors, two locked doors, two cases. Every tool from Chapters 1–5 is on the table.',
   'Open both doors, collect both cases, extract.',
   'Mastery drill: doors. Trace the route floor by floor before coding. From Stage 26 the building starts watching back.',
   12,7,(1,5),(10,2),doors=[dict(id='gate1',x=4,y=5),dict(id='gate2',x=8,y=2)],items=[dict(type='badge',x=2,y=5,label='Access badge'),dict(type='intel',x=6,y=5,label='Intel case'),dict(type='intel',x=9,y=2,label='Intel case')],
   solution='agent.step(1)\nagent.collect()\nagent.step(1)\nagent.interact()\nagent.step(3)\nagent.collect()\nagent.turn("left")\nagent.step(3)\nagent.turn("right")\nagent.step(1)\nagent.interact()\nagent.step(2)\nagent.collect()\nagent.step(1)'),

 # ---------- Chapter 6: Cameras (26-30) — camera gates force disabling ----------
 L(26,'Camera Watch','First camera','STEALTH',
   'A security camera seals the only gate in this corridor. Step onto the watched tile while it is live and the alarm ends the run.',
   'Detect the camera, disable it, then cross through the gate.',
   'Skill 6 of 12 — CAMERAS: the camera watches the red tile — the only way through. agent.camera_ahead() reports a live camera on the tile ahead; agent.disable_camera() switches it off when you stand beside it.',
   9,7,(1,3),(7,3),walls=[(4,1),(4,2),(4,4),(4,5)],cameras=[dict(id='cam1',x=4,y=3,danger=[(4,3)])],items=[dict(type='intel',x=6,y=3,label='Intel case')],
   solution='agent.step(2)\nif agent.camera_ahead():\n    agent.disable_camera()\nagent.step(3)\nagent.collect()\nagent.step(1)'),
 L(27,'Two Watchful Eyes','Two gates','STEALTH',
   'Two cameras seal two gates, one after the other. The routine you learned now runs twice — a loop runs it for you.',
   'Loop through both camera gates, collect the intel, extract.',
   'Practice: the same disable routine, repeated for each gate. Stand beside the camera, disable, then walk through.',
   11,7,(1,3),(9,3),walls=[(4,1),(4,2),(4,4),(4,5),(7,1),(7,2),(7,4),(7,5)],cameras=[dict(id='cam1',x=4,y=3,danger=[(4,3)]),dict(id='cam2',x=7,y=3,danger=[(7,3)])],items=[dict(type='intel',x=8,y=3,label='Intel case')],
   solution='for i in range(2):\n    agent.step(2)\n    agent.disable_camera()\n    agent.step(1)\nagent.step(1)\nagent.collect()\nagent.step(1)'),
 L(28,'Camera Corner','Camera + turns','STEALTH',
   'The camera seals the gate right before the corner. Disable it, take the case, and swing down to extraction.',
   'Disable the camera, cross the gate, collect, and turn the corner to EX.',
   'Practice: cameras plus turning. Disable from the tile beside the gate, cross, then mind your turns.',
   10,7,(1,3),(7,5),walls=[(5,1),(5,2),(5,4),(5,5)],cameras=[dict(id='cam1',x=5,y=3,danger=[(5,3)])],items=[dict(type='intel',x=7,y=3,label='Intel case')],
   solution='agent.step(3)\nagent.disable_camera()\nagent.step(3)\nagent.collect()\nagent.turn("right")\nagent.step(2)'),
 L(29,'Guarded Gate','Camera + door','STEALTH',
   'A locked door, then a camera gate right behind it. Open first, silence second, then move.',
   'Open the door, disable the camera, take the intel.',
   'Practice: doors and cameras together — order matters. You cannot reach the camera until the door is open.',
   11,6,(1,3),(9,3),walls=[(6,1),(6,2),(6,4)],doors=[dict(id='gate',x=4,y=3)],cameras=[dict(id='cam1',x=6,y=3,danger=[(6,3)])],items=[dict(type='badge',x=2,y=3,label='Access badge'),dict(type='intel',x=8,y=3,label='Intel case')],
   solution='agent.step(1)\nagent.collect()\nagent.step(1)\nagent.interact()\nagent.step(2)\nagent.disable_camera()\nagent.step(3)\nagent.collect()\nagent.step(1)'),
 L(30,'Camera Mastery','Three gates','STEALTH',
   'Camera exam: three live cameras seal the whole corridor. One loop can disarm all three gates.',
   'Use a loop to disable every camera, collect, and extract.',
   'Mastery drill: cameras. Each gate is identical — step up beside it, disable, walk through. That is one loop body, repeated three times. From Stage 31 you learn the last skill — functions.',
   14,6,(1,3),(12,3),walls=[(3,1),(3,2),(3,4),(6,1),(6,2),(6,4),(9,1),(9,2),(9,4)],cameras=[dict(id='cam1',x=3,y=3,danger=[(3,3)]),dict(id='cam2',x=6,y=3,danger=[(6,3)]),dict(id='cam3',x=9,y=3,danger=[(9,3)])],items=[dict(type='intel',x=11,y=3,label='Intel case')],
   solution='agent.step(1)\nfor i in range(3):\n    agent.disable_camera()\n    agent.step(3)\nagent.collect()\nagent.step(1)'),

 # ---------- Chapter 7: Functions + finale (31-35) — HQ requires a def ----------
 L(31,'Write a Function','First def','FIELD TEST',
   'The final skill: package a maneuver into a named function and call it whenever you need it.',
   'Define climb(), call it twice, collect, and extract.',
   'Skill 7 of 12 — FUNCTIONS: def name(): defines a reusable block; call it by name. HQ REQUIREMENT: your program must define a function with def.',
   9,6,(1,4),(7,2),items=[dict(type='intel',x=5,y=2,label='Intel case')],
   solution='def climb():\n    agent.step(2)\n    agent.turn("left")\n    agent.step(1)\n    agent.turn("right")\n\nclimb()\nclimb()\nagent.collect()\nagent.step(2)',
   require='def'),
 L(32,'Reusable Routine','Hop chain','FIELD TEST',
   'Define the hop once, call it five times. This is what functions are for.',
   'Use a hop() function to collect all five cases.',
   'Practice: define once, call many times — each call runs the whole block. Five cases, one function.',
   14,5,(1,2),(12,2),items=[dict(type='intel',x=3,y=2,label='Intel case'),dict(type='intel',x=5,y=2,label='Intel case'),dict(type='intel',x=7,y=2,label='Intel case'),dict(type='intel',x=9,y=2,label='Intel case'),dict(type='intel',x=11,y=2,label='Intel case')],
   solution='def hop():\n    agent.step(2)\n    agent.collect()\n\nhop()\nhop()\nhop()\nhop()\nhop()\nagent.step(1)',
   require='def'),
 L(33,'Function Toolkit','Function + loop','FIELD TEST',
   'A function with a loop inside, called from another loop. Small code, big route.',
   'Build run(n) and patrol the square with two nested repeats.',
   'Practice: functions and loops compose — the outer loop drives the sides, the function walks each one. Functions can even take a number as input.',
   6,6,(1,1),(1,1),items=[dict(type='intel',x=4,y=1,label='Intel case'),dict(type='intel',x=4,y=4,label='Intel case'),dict(type='intel',x=1,y=4,label='Intel case')],
   solution='def run(n):\n    for i in range(n):\n        agent.step(1)\n\nfor i in range(4):\n    run(3)\n    agent.collect()\n    agent.turn("right")',
   require='def'),
 L(34,'Full Toolkit','Every tool','FINALE',
   'Badge, door, wall, and a sealed camera gate — every obstacle in one corridor. Write a detour() function and keep your plan readable.',
   'Open the door, detour the wall, disable the camera gate, extract.',
   'Practice: every skill trained so far, in one op. One helper function keeps the wall detour manageable. HQ requires a def.',
   12,6,(1,3),(10,3),walls=[(6,3),(8,1),(8,2),(8,4)],doors=[dict(id='gate',x=4,y=3)],cameras=[dict(id='cam1',x=8,y=3,danger=[(8,3)])],items=[dict(type='badge',x=2,y=3,label='Access badge'),dict(type='intel',x=9,y=3,label='Intel case')],
   solution='def detour():\n    agent.turn("left")\n    agent.step(1)\n    agent.turn("right")\n    agent.step(2)\n    agent.turn("right")\n    agent.step(1)\n    agent.turn("left")\n\nagent.step(1)\nagent.collect()\nagent.step(1)\nagent.interact()\nagent.step(2)\ndetour()\nagent.disable_camera()\nagent.step(2)\nagent.collect()\nagent.step(1)',
   require='def'),
 L(35,'The Grand Heist','Final operation','FINALE',
   'The final operation: two floors, two locked doors, a wall, a sealed camera gate, and two intel cases. Everything you have learned, in one heist.',
   'Clear the heist: badge, both doors, the wall, the camera gate, both cases — then extract.',
   'Final exam. Plan on paper first, then write the cleanest program of your career. A detour() function and a cool head will see you through.',
   14,8,(1,6),(11,1),walls=[(8,6),(10,1),(10,2),(10,3),(10,4),(10,5)],doors=[dict(id='gate1',x=4,y=6),dict(id='gate2',x=12,y=4)],cameras=[dict(id='cam1',x=10,y=6,danger=[(10,6)])],items=[dict(type='badge',x=2,y=6,label='Access badge'),dict(type='intel',x=6,y=6,label='Intel case'),dict(type='intel',x=12,y=1,label='Intel case')],
   solution='def detour():\n    agent.turn("left")\n    agent.step(1)\n    agent.turn("right")\n    agent.step(2)\n    agent.turn("right")\n    agent.step(1)\n    agent.turn("left")\n\nagent.step(1)\nagent.collect()\nagent.step(1)\nagent.interact()\nagent.step(3)\nagent.collect()\nagent.step(1)\ndetour()\nagent.disable_camera()\nagent.step(2)\nagent.turn("left")\nagent.step(2)\nagent.turn("right")\nagent.interact()\nagent.step(1)\nagent.turn("left")\nagent.step(3)\nagent.collect()\nagent.turn("left")\nagent.step(1)',
   require='def'),

 # ---------- Chapter 8: Variables (36-40) ----------
 L(36,'First Cache','Store a number','VARIABLES',
   'A distance is just a number — and numbers can be saved in a variable. Store the walk once, use it twice.',
   'Store d = 3, walk to the case with agent.step(d), collect, and reuse d to reach EX.',
   'Skill 8 of 12 — VARIABLES: a line like d = 3 stores the number 3 under the name d. From then on, agent.step(d) walks 3 tiles. HQ REQUIREMENT: your program must store a value with = and reuse it.',
   9,7,(1,3),(7,3),items=[dict(type='intel',x=4,y=3,label='Intel case')],
   solution='d = 3\nagent.step(d)\nagent.collect()\nagent.step(d)',
   require='assign'),
 L(37,'Double Distance','Math in variables','VARIABLES',
   'One stored number can power two different walks. Python does the math before the agent moves.',
   'Store n = 2, walk n tiles to collect, then walk n * 2 tiles to EX.',
   'Practice: expressions work anywhere a number does. agent.step(n * 2) doubles the stored distance in one command.',
   9,7,(1,3),(7,3),items=[dict(type='intel',x=3,y=3,label='Intel case')],
   solution='n = 2\nagent.step(n)\nagent.collect()\nagent.step(n * 2)',
   require='assign'),
 L(38,'The Counted Chain','Variable drives a loop','VARIABLES',
   'Four cases in a row. Instead of hard-coding range(4), store the count in a variable and let the loop read it.',
   'Store the case count in n, loop n times to collect every case, then walk to EX.',
   'Practice: n = 4 then for i in range(n): — the loop repeats as many times as the variable says. Change n, and the whole plan changes with it.',
   9,5,(1,3),(7,3),items=[dict(type='intel',x=2,y=3,label='Intel case'),dict(type='intel',x=3,y=3,label='Intel case'),dict(type='intel',x=4,y=3,label='Intel case'),dict(type='intel',x=5,y=3,label='Intel case')],
   solution='n = 4\nfor i in range(n):\n    agent.step(1)\n    agent.collect()\nagent.step(2)',
   require='assign'),
 L(39,'Growing Stride','Updating a variable','VARIABLES',
   'Each walk is one tile longer than the last: 1, then 2, then 3. A variable that updates itself is the clean way to grow.',
   'Start d at 0, then loop 3 times: raise d by 1, walk d tiles, collect.',
   'Practice: d = d + 1 reads the old value, adds 1, and stores the result back. That is how counters grow in real programs.',
   10,5,(1,3),(8,3),items=[dict(type='intel',x=2,y=3,label='Intel case'),dict(type='intel',x=4,y=3,label='Intel case'),dict(type='intel',x=7,y=3,label='Intel case')],
   solution='d = 0\nfor i in range(3):\n    d = d + 1\n    agent.step(d)\n    agent.collect()\nagent.step(1)',
   require='assign'),
 L(40,'Variable Mastery','Patrol square','VARIABLES',
   'Mastery drill: a square patrol where one variable holds the side length. Four identical legs — the loop reads the variable every time.',
   'Store side = 3, collect the case, then loop 4 times: walk side tiles, collect, turn right. You land back on EX.',
   'Mastery drill: variables + loops. The extraction point is the tile you started on — walk side, collect, turn right, four times over.',
   8,7,(2,1),(2,1),items=[dict(type='intel',x=5,y=1,label='Intel case'),dict(type='intel',x=5,y=4,label='Intel case'),dict(type='intel',x=2,y=4,label='Intel case')],
   solution='side = 3\nfor i in range(4):\n    agent.step(side)\n    agent.collect()\n    agent.turn("right")',
   require='assign'),

 # ---------- Chapter 9: While Loops (41-45) ----------
 L(41,'Sentinel Walk','Walk until blocked','WHILE LOOPS',
   'Some corridors you do not count — you just walk until something stops you. A while loop checks before every single step.',
   'Walk forward one tile at a time while no wall is ahead. Collect whatever you pass. The loop stops by itself at EX.',
   'Skill 9 of 12 — WHILE LOOPS: while CONDITION: repeats as long as the condition is true. agent.wall_ahead() is true when the next tile is blocked, so "while not agent.wall_ahead()" walks until the corridor ends. HQ REQUIREMENT: your program must contain a while loop.',
   10,7,(1,3),(8,3),walls=[(1,2),(2,2),(3,2),(4,2),(5,2),(6,2),(7,2),(8,2),(1,4),(2,4),(3,4),(4,4),(5,4),(6,4),(7,4),(8,4)],items=[dict(type='intel',x=3,y=3,label='Intel case'),dict(type='intel',x=5,y=3,label='Intel case'),dict(type='intel',x=7,y=3,label='Intel case')],
   solution='while not agent.wall_ahead():\n    agent.step(1)\n    agent.collect()',
   require='while'),
 L(42,'Corner Sentinel','While + turns','WHILE LOOPS',
   'Two corridors meet in a corner. Walk each one to the end with a sentinel loop — the wall tells you when to turn.',
   'Twice: walk while no wall is ahead (collecting on the way), then turn left.',
   'Practice: the same while loop handles both corridors, whatever their length. Walk until blocked, turn, repeat.',
   9,8,(1,6),(7,1),walls=[(1,5),(2,5),(3,5),(4,5),(5,5),(6,5),(6,1),(6,2),(6,3),(6,4),(6,5)],items=[dict(type='intel',x=4,y=6,label='Intel case'),dict(type='intel',x=7,y=3,label='Intel case')],
   solution='for i in range(2):\n    while not agent.wall_ahead():\n        agent.step(1)\n        agent.collect()\n    agent.turn("left")',
   require='while'),
 L(43,'Stairway Sentinel','While + zigzag','WHILE LOOPS',
   'A staircase climbs to the roof exit. Each stair is one step right, one step up — repeated until the wall on the roof says stop.',
   'Loop while no wall is ahead: step, turn left, step, collect, turn right.',
   'Practice: the loop body builds one whole stair. The sentinel (wall_ahead) decides when the staircase is finished.',
   9,8,(1,6),(6,1),walls=[(7,1)],items=[dict(type='intel',x=2,y=5,label='Intel case'),dict(type='intel',x=3,y=4,label='Intel case'),dict(type='intel',x=4,y=3,label='Intel case'),dict(type='intel',x=5,y=2,label='Intel case')],
   solution='while not agent.wall_ahead():\n    agent.step(1)\n    agent.turn("left")\n    agent.step(1)\n    agent.collect()\n    agent.turn("right")',
   require='while'),
 L(44,'Silent Patrol','While + cameras','WHILE LOOPS',
   'A patrolled corridor with two live cameras. The sentinel walks; a check inside the loop disarms each camera just before crossing.',
   'Walk one tile at a time while no wall is ahead; whenever a camera guards the next tile, disable it first.',
   'Practice: while keeps walking, if handles the camera. Combining the two is how real patrols are written.',
   12,7,(1,3),(10,3),walls=[(1,2),(2,2),(3,2),(4,2),(5,2),(6,2),(7,2),(8,2),(9,2),(10,2),(1,4),(2,4),(3,4),(4,4),(5,4),(6,4),(7,4),(8,4),(9,4),(10,4)],cameras=[dict(id='cam1',x=5,y=3,danger=[(5,3)]),dict(id='cam2',x=9,y=3,danger=[(9,3)])],items=[dict(type='intel',x=7,y=3,label='Intel case')],
   solution='while not agent.wall_ahead():\n    if agent.camera_ahead():\n        agent.disable_camera()\n    agent.step(1)\n    agent.collect()',
   require='while'),
 L(45,'Spiral Descent','While + counters','WHILE LOOPS',
   'A shrinking spiral: 4 tiles, then 3, then 2, then 1. A counter variable and a while loop trace it perfectly.',
   'Start n at 4. While n is above 0: walk n tiles, collect, turn right, and lower n by 1.',
   'Mastery drill: while loops shine when the number of repeats is computed. Here n counts the spiral down to zero.',
   8,7,(1,1),(3,3),items=[dict(type='intel',x=5,y=1,label='Intel case'),dict(type='intel',x=5,y=4,label='Intel case'),dict(type='intel',x=3,y=4,label='Intel case')],
   solution='n = 4\nwhile n > 0:\n    agent.step(n)\n    agent.collect()\n    agent.turn("right")\n    n = n - 1',
   require='while'),

 # ---------- Chapter 10: Logic — and / or / not (46-50) ----------
 L(46,'Two Watches','Stop on two sensors','LOGIC',
   'The corridor can end in a wall OR a live camera. Check both sensors at once and stop at whichever comes first.',
   'Walk while no wall is ahead AND no camera is ahead. Disable the camera, then walk the rest of the way.',
   'Skill 10 of 12 — LOGIC: and needs both sides true, or needs at least one, not flips a condition. "while not wall and not camera" keeps walking only when BOTH sensors are clear. HQ REQUIREMENT: combine conditions with and / or / not.',
   11,7,(1,3),(9,3),walls=[(1,2),(2,2),(3,2),(4,2),(5,2),(6,2),(7,2),(8,2),(9,2),(1,4),(2,4),(3,4),(4,4),(5,4),(6,4),(7,4),(8,4),(9,4)],cameras=[dict(id='cam1',x=5,y=3,danger=[(5,3)])],items=[dict(type='intel',x=3,y=3,label='Intel case'),dict(type='intel',x=7,y=3,label='Intel case')],
   solution='while not agent.wall_ahead() and not agent.camera_ahead():\n    agent.step(1)\n    agent.collect()\nif agent.camera_ahead():\n    agent.disable_camera()\nwhile not agent.wall_ahead():\n    agent.step(1)\n    agent.collect()',
   require='logic'),
 L(47,'Stop Rules','or stops the walk','LOGIC',
   'A camera gate, then a locked door — two very different blockers. One sentinel rule stops at either: wall OR camera.',
   'Walk while not (wall ahead or camera ahead). Handle the camera, walk to the door, open it, and finish the route.',
   'Practice: not (a or b) stops at the first blocker of any kind. One loop, two obstacle types — that is the power of or.',
   12,7,(1,3),(10,3),walls=[(1,2),(2,2),(3,2),(4,2),(5,2),(6,2),(7,2),(8,2),(9,2),(10,2),(1,4),(2,4),(3,4),(4,4),(5,4),(6,4),(7,4),(8,4),(9,4),(10,4)],doors=[dict(id='lock',x=7,y=3)],cameras=[dict(id='cam1',x=4,y=3,danger=[(4,3)])],items=[dict(type='badge',x=2,y=3,label='Access badge'),dict(type='intel',x=9,y=3,label='Intel case')],
   solution='while not (agent.wall_ahead() or agent.camera_ahead()):\n    agent.step(1)\n    agent.collect()\nif agent.camera_ahead():\n    agent.disable_camera()\nwhile not agent.wall_ahead():\n    agent.step(1)\n    agent.collect()\nagent.interact()\nwhile not agent.wall_ahead():\n    agent.step(1)\n    agent.collect()',
   require='logic'),
 L(48,'Double Condition','Counter and sensor','LOGIC',
   'Three cases, then a sprint to the exit. Stop collecting when the counter hits 3 AND keep a sensor check as a safety net.',
   'Collect the three cases with a loop that runs while i < 3 and no wall is ahead, then walk to EX.',
   'Practice: i < 3 and not agent.wall_ahead() — two guards on one loop. and means the loop continues only while BOTH hold.',
   11,7,(1,3),(9,3),walls=[(1,2),(2,2),(3,2),(4,2),(5,2),(6,2),(7,2),(8,2),(9,2),(1,4),(2,4),(3,4),(4,4),(5,4),(6,4),(7,4),(8,4),(9,4)],items=[dict(type='intel',x=3,y=3,label='Intel case'),dict(type='intel',x=5,y=3,label='Intel case'),dict(type='intel',x=7,y=3,label='Intel case')],
   solution='i = 0\nwhile i < 3 and not agent.wall_ahead():\n    agent.step(2)\n    agent.collect()\n    i = i + 1\nagent.step(2)',
   require='logic'),
 L(49,'Fork Sensors','Store and combine','LOGIC',
   'A T-junction: one branch is walled off, the other leads to extraction. Store a sensor reading in a variable, then combine it with a second check.',
   'Face the upper branch and store blocked_up = agent.wall_ahead(). Then, if blocked_up and the lower lane is clear, walk it to EX.',
   'Practice: readings can live in variables — blocked_up = agent.wall_ahead(). Combine stored facts with and / not to choose a route.',
   9,8,(1,3),(4,6),walls=[(1,2),(2,2),(3,2),(4,2),(5,2),(6,2),(7,2),(1,4),(2,4),(3,4),(5,4),(6,4),(7,4),(3,5),(3,6),(5,5),(5,6)],items=[dict(type='intel',x=4,y=5,label='Intel case')],
   solution='agent.step(3)\nagent.turn("left")\nblocked_up = agent.wall_ahead()\nagent.turn("right")\nagent.turn("right")\nif blocked_up and not agent.wall_ahead():\n    while not agent.wall_ahead():\n        agent.step(1)\n        agent.collect()',
   require='logic'),
 L(50,'Logic Mastery','Camera, wall, logic','LOGIC',
   'Mastery drill: a camera gate early on, a full wall block later, and logic tying the whole patrol together.',
   'Sentinel-walk with not (wall or camera), disable the camera, walk to the block, detour over it, and sentinel-walk to EX.',
   'Mastery drill: logic. Two sentinel walks, one if, one four-turn detour — every condition earns its place.',
   13,7,(1,3),(11,3),walls=[(1,2),(2,2),(3,2),(4,2),(5,2),(9,2),(10,2),(11,2),(1,4),(2,4),(3,4),(4,4),(5,4),(6,4),(7,4),(8,4),(9,4),(10,4),(11,4),(7,3)],cameras=[dict(id='cam1',x=4,y=3,danger=[(4,3)])],items=[dict(type='intel',x=9,y=3,label='Intel case')],
   solution='while not (agent.wall_ahead() or agent.camera_ahead()):\n    agent.step(1)\n    agent.collect()\nif agent.camera_ahead():\n    agent.disable_camera()\nwhile not (agent.wall_ahead() or agent.camera_ahead()):\n    agent.step(1)\n    agent.collect()\nagent.turn("left")\nagent.step(2)\nagent.turn("right")\nagent.step(2)\nagent.turn("right")\nagent.step(2)\nagent.turn("left")\nwhile not agent.wall_ahead():\n    agent.step(1)\n    agent.collect()',
   require='logic'),

 # ---------- Chapter 11: Lists (51-55) ----------
 L(51,'First List','A plan in brackets','LISTS',
   'Three walks of different lengths — pack them into one list and let a loop run the whole plan.',
   'Store steps = [2, 1, 3], loop over the list walking each distance and collecting, then step to EX.',
   'Skill 11 of 12 — LISTS: [2, 1, 3] is a list of three numbers. "for s in steps:" visits them one by one, with s holding each value in turn. HQ REQUIREMENT: your program must build a list with [...].',
   10,7,(1,3),(8,3),items=[dict(type='intel',x=3,y=3,label='Intel case'),dict(type='intel',x=4,y=3,label='Intel case'),dict(type='intel',x=7,y=3,label='Intel case')],
   solution='steps = [2, 1, 3]\nfor s in steps:\n    agent.step(s)\n    agent.collect()\nagent.step(1)',
   require='list'),
 L(52,'Turn Plan','List of directions','LISTS',
   'A slalom route: straight runs with a turn after each one. Directions are just words — a list of them drives the whole route.',
   'Store the four turn directions in a list, then loop: walk 2, collect, turn as the list says. One last walk reaches EX.',
   'Practice: strings live in lists too. turns = ["left", "right", ...] and agent.turn(t) reads each direction straight from the plan.',
   9,8,(1,5),(7,5),walls=[(2,4),(4,4),(6,4)],items=[dict(type='intel',x=3,y=5,label='Intel case'),dict(type='intel',x=3,y=3,label='Intel case'),dict(type='intel',x=5,y=3,label='Intel case'),dict(type='intel',x=5,y=5,label='Intel case')],
   solution='turns = ["left", "right", "right", "left"]\nfor t in turns:\n    agent.step(2)\n    agent.collect()\n    agent.turn(t)\nagent.step(2)',
   require='list'),
 L(53,'Zipped Plans','Two lists, one loop','LISTS',
   'Walks AND turns, paired up. Two lists plus zip() run both plans in lock-step — a real-world Python pattern.',
   'Zip a steps list with a turns list, loop over the pairs, then climb to the intel and EX.',
   'Practice: for s, t in zip(steps, turns): unpacks one value from each list every round. Two plans, one loop.',
   10,8,(1,5),(5,1),walls=[(2,4),(6,4),(4,2)],items=[dict(type='intel',x=5,y=2,label='Intel case')],
   solution='steps = [2, 1, 2]\nturns = ["left", "right", "left"]\nfor s, t in zip(steps, turns):\n    agent.step(s)\n    agent.turn(t)\nagent.step(2)\nagent.collect()\nagent.step(1)',
   require='list'),
 L(54,'Gate Distances','List-driven cameras','LISTS',
   'Two camera gates at different ranges. Store the approach distances in a list and clear both gates with one compact loop.',
   'Loop over the gap list: walk the gap, disable the camera. Then collect the case and extract.',
   'Practice: gates = [2, 4] holds the distance to each gate. The loop body never changes — only the data does.',
   13,7,(1,3),(11,3),walls=[(1,2),(2,2),(3,2),(4,2),(5,2),(6,2),(7,2),(8,2),(9,2),(10,2),(11,2),(1,4),(2,4),(3,4),(4,4),(5,4),(6,4),(7,4),(8,4),(9,4),(10,4),(11,4)],cameras=[dict(id='cam1',x=4,y=3,danger=[(4,3)]),dict(id='cam2',x=8,y=3,danger=[(8,3)])],items=[dict(type='intel',x=9,y=3,label='Intel case')],
   solution='gaps = [2, 4]\nfor g in gaps:\n    agent.step(g)\n    agent.disable_camera()\nagent.step(2)\nagent.collect()\nagent.step(2)',
   require='list'),
 L(55,'List Mastery','Slalom + camera gate','LISTS',
   'Mastery drill: a zip-driven slalom through four cases, ending at a sealed camera gate. Data drives, the loop executes.',
   'Zip steps with turns to clear the four cases, walk up to the gate, disable the camera, and extract.',
   'Mastery drill: lists. The slalom is pure data — change the lists and the route changes. The gate at the end keeps you honest.',
   14,8,(1,5),(12,5),walls=[(2,4),(4,4),(6,4),(10,1),(10,2),(10,3),(10,4),(10,6)],cameras=[dict(id='cam1',x=10,y=5,danger=[(10,5)])],items=[dict(type='intel',x=3,y=5,label='Intel case'),dict(type='intel',x=3,y=3,label='Intel case'),dict(type='intel',x=5,y=3,label='Intel case'),dict(type='intel',x=5,y=5,label='Intel case')],
   solution='steps = [2, 2, 2, 2]\nturns = ["left", "right", "right", "left"]\nfor s, t in zip(steps, turns):\n    agent.step(s)\n    agent.collect()\n    agent.turn(t)\nagent.step(4)\nagent.disable_camera()\nagent.step(3)',
   require='list'),

 # ---------- Chapter 12: Functions with Arguments (56-60) ----------
 L(56,'First Argument','A function that takes input','ARGUMENTS',
   'A hop of 2 and a hop of 3 — the same move, different sizes. Give the function an argument and one definition handles both.',
   'Define hop(n) to walk n tiles and collect. Call hop(2), hop(3), hop(2) to reach EX.',
   'Skill 12 of 12 — ARGUMENTS: def hop(n): names its input n; calling hop(3) runs the block with n = 3. One definition, many sizes. HQ REQUIREMENT: define a function that takes an argument.',
   10,7,(1,3),(8,3),items=[dict(type='intel',x=3,y=3,label='Intel case'),dict(type='intel',x=6,y=3,label='Intel case')],
   solution='def hop(n):\n    agent.step(n)\n    agent.collect()\nhop(2)\nhop(3)\nhop(2)',
   require='args'),
 L(57,'Loop-Driven Function','Function + list','ARGUMENTS',
   'Four hops of different lengths, all from one list. The function takes the size; the loop feeds it from the data.',
   'Define hop(n), store the four gaps in a list, loop over them calling hop(g), then step to EX.',
   'Practice: functions + lists + loops — the full toolkit. hop never changes; the list decides every distance.',
   12,7,(1,3),(10,3),items=[dict(type='intel',x=3,y=3,label='Intel case'),dict(type='intel',x=6,y=3,label='Intel case'),dict(type='intel',x=8,y=3,label='Intel case'),dict(type='intel',x=9,y=3,label='Intel case')],
   solution='def hop(n):\n    agent.step(n)\n    agent.collect()\ngaps = [2, 3, 2, 1]\nfor g in gaps:\n    hop(g)\nagent.step(1)',
   require='args'),
 L(58,'Sweep Function','Loop inside a function','ARGUMENTS',
   'An L-shaped sweep in three segments of different lengths. sweep(n) walks and collects n tiles — call it three times.',
   'Define sweep(n) with a loop inside, then sweep 3, turn, sweep 2, turn, sweep 3 to EX.',
   'Practice: a function can own a whole loop. sweep(3) walks three tiles collecting everything; sweep(2) walks two.',
   9,8,(1,5),(7,3),walls=[(2,4),(3,4),(5,4),(6,4)],items=[dict(type='intel',x=2,y=5,label='Intel case'),dict(type='intel',x=4,y=4,label='Intel case'),dict(type='intel',x=6,y=3,label='Intel case')],
   solution='def sweep(n):\n    for i in range(n):\n        agent.step(1)\n        agent.collect()\nsweep(3)\nagent.turn("left")\nsweep(2)\nagent.turn("right")\nsweep(3)',
   require='args'),
 L(59,'Parameter Patrol','Function clears gates','ARGUMENTS',
   'Two camera gates, one routine. gate(gap) walks the approach and disarms the camera — the argument is the only thing that changes.',
   'Define gate(gap), loop over the two gaps calling gate(g), then collect the case and extract.',
   'Practice: the patrol routine from before, now parameterized. gap is a placeholder the caller fills in each time.',
   13,7,(1,3),(11,3),walls=[(1,2),(2,2),(3,2),(4,2),(5,2),(6,2),(7,2),(8,2),(9,2),(10,2),(11,2),(1,4),(2,4),(3,4),(4,4),(5,4),(6,4),(7,4),(8,4),(9,4),(10,4),(11,4)],cameras=[dict(id='cam1',x=4,y=3,danger=[(4,3)]),dict(id='cam2',x=8,y=3,danger=[(8,3)])],items=[dict(type='intel',x=9,y=3,label='Intel case')],
   solution='def gate(gap):\n    agent.step(gap)\n    agent.disable_camera()\ngaps = [2, 4]\nfor g in gaps:\n    gate(g)\nagent.step(2)\nagent.collect()\nagent.step(2)',
   require='args'),
 L(60,'The Full Arsenal','Grand finale','ARGUMENTS',
   'The graduation heist: a badge, a locked vault door, a camera gate, a case of intel, and a sentinel walk out. Every Python skill from the whole campaign, in one program.',
   'Grab the badge, open the vault, use a gate(gap) function for the camera, take the intel, and sentinel-walk to EX.',
   'Final exam of the extended campaign: variables, while, logic, lists, and functions with arguments — all of it. Plan first, write once, extract.',
   14,8,(1,6),(12,6),walls=[(1,5),(2,5),(3,5),(4,5),(5,5),(7,1),(7,2),(7,3),(7,4),(7,5)],doors=[dict(id='vault',x=4,y=6)],cameras=[dict(id='cam1',x=7,y=6,danger=[(7,6)])],items=[dict(type='badge',x=2,y=6,label='Access badge'),dict(type='intel',x=8,y=6,label='Intel case')],
   solution='def gate(gap):\n    agent.step(gap)\n    agent.disable_camera()\nagent.step(1)\nagent.collect()\nagent.step(1)\nagent.interact()\ngate(3)\nagent.step(2)\nagent.collect()\nwhile not agent.wall_ahead():\n    agent.step(1)',
   require='args'),
]

def code_lines(src):
    return len([l for l in src.split('\n') if l.strip() and not l.strip().startswith('#')])

def run(level_id, code):
    body = json.dumps({"levelId": level_id, "code": code}).encode()
    req = urllib.request.Request("http://127.0.0.1:8000/api/run", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

def verify_all():
    stats = {}
    for lv in LEVELS:
        r = run(lv['id'], lv['solution'])
        ok = r.get('ok') and r.get('complete')
        lines = code_lines(lv['solution'])
        stats[lv['id']] = (r.get('actions'), lines)
        print(f"stage {lv['id']:2}: {'OK ' if ok else 'FAIL'} actions={r.get('actions')} lines={lines}" +
              ("" if ok else f"  ERROR: {r.get('error')}"))
        if not ok:
            sys.exit('SOLUTION FAILED — fix before emitting')
    return stats

def emit_server(stats):
    rows = []
    for lv in LEVELS:
        doors = ', '.join('{"id": "%s", "x": %d, "y": %d}' % (d['id'], d['x'], d['y']) for d in lv['doors'])
        cams = ', '.join('{"id": "%s", "x": %d, "y": %d, "danger": %s}' % (
            c['id'], c['x'], c['y'], json.dumps([list(p) for p in c['danger']])) for c in lv['cameras'])
        items = ', '.join('{"type": "%s", "x": %d, "y": %d, "label": "%s"}' % (
            i['type'], i['x'], i['y'], i['label']) for i in lv['items'])
        walls = json.dumps([list(w) for w in lv['walls']])
        req = '"require": "%s"' % lv['require'] if lv['require'] else '"require": None'
        rows.append('    %d: {"cols": %d, "rows": %d, "start": %s, "exit": %s, "walls": %s, "doors": [%s], "cameras": [%s], "items": [%s], %s},' % (
            lv['id'], lv['cols'], lv['rows'], json.dumps(lv['start']), json.dumps(lv['exit']),
            walls, doors, cams, items, req))
    block = 'LEVELS = {\n' + '\n'.join(rows) + '\n}'
    open('/tmp/server_levels.txt', 'w', encoding='utf-8').write(block)
    print('server LEVELS written to /tmp/server_levels.txt')

REQ_LABELS = {'loop': 'A FOR LOOP', 'if': 'AN IF CHECK', 'def': 'A DEF FUNCTION',
            'assign': 'A VARIABLE (n = 3)', 'while': 'A WHILE LOOP', 'logic': 'AND / OR / NOT',
            'list': 'A LIST', 'args': 'A FUNCTION WITH ARGUMENTS'}

def emit_client(stats):
    parts = []
    for lv in LEVELS:
        actions, lines = stats[lv['id']]
        js_items = ','.join("{type:'%s',x:%d,y:%d,label:'%s'}" % (i['type'], i['x'], i['y'], i['label']) for i in lv['items'])
        js_doors = ','.join("{id:'%s',x:%d,y:%d}" % (d['id'], d['x'], d['y']) for d in lv['doors'])
        js_cams = ','.join("{id:'%s',x:%d,y:%d,dir:'down',danger:[%s]}" % (
            c['id'], c['x'], c['y'], ','.join('{x:%d,y:%d}' % (p[0], p[1]) for p in c['danger'])) for c in lv['cameras'])
        js_walls = ','.join('{x:%d,y:%d}' % (w[0], w[1]) for w in lv['walls'])
        esc = lambda t: t.replace("'", "\\'")
        code = '%s-%02d' % (lv['tag'][:4], lv['id'])
        req = ",req:'%s'" % REQ_LABELS[lv['require']] if lv['require'] else ''
        parts.append("""    {
      id:%d,title:'%s',short:'%s',code:'%s',tag:'%s',
      desc:'%s',
      objective:'%s',cols:%d,rows:%d,lines:%d,start:{x:%d,y:%d},exit:{x:%d,y:%d},walls:[%s],doors:[%s],cameras:[%s],
      items:[%s],
      note:'%s'%s
    }""" % (lv['id'], esc(lv['title']), esc(lv['short']), code, lv['tag'], esc(lv['desc']),
            esc(lv['objective']), lv['cols'], lv['rows'], lines + 1, lv['start'][0], lv['start'][1],
            lv['exit'][0], lv['exit'][1], js_walls, js_doors, js_cams, js_items, esc(lv['note']), req))
    open('/tmp/client_levels.txt', 'w', encoding='utf-8').write(',\n'.join(parts))
    targets = '{' + ','.join('%d:%d' % (lv['id'], stats[lv['id']][0]) for lv in LEVELS) + '}'
    open('/tmp/star_targets.txt', 'w', encoding='utf-8').write(targets)
    print('client levels + star targets written')

if __name__ == '__main__':
    import sys as _s
    if len(_s.argv) > 1 and _s.argv[1] == 'server-only':
        emit_server({lv['id']: (0, 0) for lv in LEVELS})
    else:
        stats = verify_all()
        emit_client(stats)
        print('ALL %d STAGES VERIFIED' % len(LEVELS))
