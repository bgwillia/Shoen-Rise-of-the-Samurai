The SHŌEN integrated core-loop prototype is accepted at commit:

`60ca49fb0416d12423eb8c57ed3e234eba17dedb`

Continue in **FEASIBILITY PROTOTYPE MODE**.

Do not return to production-hardening or small approval milestones.

The first prototype established that:

* settlement population can drive the economy
* real population can be mobilized
* equipment constrains military recruitment
* samurai and ordinary formations can fight
* casualties correctly affect occupations after returning home
* post-war economic effects are visible
* 2,000 vs 2,000 simplified combat is technically feasible on the current machine

The next prototype must answer a different question:

# Can large numbers of small formations maneuver and fight meaningfully on constrained terrain?

Build one representative tactical battlefield and improve tactical control just enough to evaluate this.

---

# 1. Battlefield

Create one placeholder but intentionally designed battlefield containing:

* two deployment sides
* a river or otherwise impassable terrain barrier
* one narrow primary crossing
* one longer secondary/flanking route
* open ground
* a wooded or concealed area
* one hill or elevated defensive position

Example topology:

Enemy deployment
|
open field
|
==== river =================
| bridge |
|        |
|        +---- distant shallow crossing
|
wooded ridge
|
Player deployment

Do not spend time on final terrain art.

Simple terrain and placeholder materials are sufficient.

The purpose is gameplay geometry.

---

# 2. Formation separation

The current prototype permits friendly formations to overlap.

Improve movement enough that formations attempt to preserve physical separation.

I do NOT need perfect crowd simulation.

I need to test whether many small units can form a readable battle line.

Requirements:

* friendly formations should not normally occupy the same final footprint
* group destinations should reserve sensible formation spaces
* formations approaching a constrained crossing should queue or reorganize rather than stack directly on top of one another
* units should be able to pass around friendly formations when reasonable
* formations should not jitter indefinitely when close together

Keep the algorithm simple enough for prototype iteration.

Measure before attempting sophisticated solutions.

---

# 3. Terrain constraints

Make terrain influence formation movement.

At minimum:

* river/impassable areas block ordinary movement
* bridge permits movement
* secondary crossing permits movement
* forest can slow movement and/or provide concealment if inexpensive
* hill/elevation can provide a simple combat or visibility advantage

Do not create a generalized navigation research project.

Use the simplest implementation that reveals whether SHŌEN’s battlefield concept works.

---

# 4. Group control

The player will eventually command many relatively small formations.

Improve group control enough to evaluate this.

Support:

* selecting many formations
* line deployment
* moving an entire selected line
* maintaining approximate relative ordering
* rotating/facing the selected line
* control groups
* selecting major categories if inexpensive:

  * infantry
  * ranged
  * samurai/elite

Do not remove independent formation control.

Group commands are convenience controls, not replacement army blobs.

---

# 5. Representative army

Create an army large enough to expose command problems.

Start around:

Player:

* 12–20 ordinary polearm formations
* 6–10 bow formations
* 2–4 samurai formations

Enemy:
similar overall size

Use roughly 80–150 ordinary soldiers per formation and smaller samurai formations using the existing data model.

Target approximately:

1,500–2,500 soldiers per side

Increase only if useful.

The goal is command complexity, not another maximum-FPS test.

---

# 6. Tactical roles

Keep combat simple, but ensure roles behave differently enough to test tactics.

## Polearm infantry

* main battle line
* average morale
* cheap equipment

## Bow infantry

* ranged damage
* vulnerable in melee
* should benefit from firing behind or beside friendly lines

## Samurai

* substantially stronger
* higher morale
* better equipment
* smaller formations
* expensive to lose

Samurai should be capable of changing a local fight.

They should not defeat unlimited enemies without support.

---

# 7. Flanking

Add a simple meaningful flanking effect.

A formation attacked from the side or rear should experience disadvantages such as:

* morale loss
* reduced cohesion
* increased casualties

Keep the calculation readable.

The secondary river crossing should provide a real tactical reason to send part of the army around the enemy.

---

# 8. Constrained-crossing test

Create a scenario where the obvious route is the narrow bridge.

Test what happens when many formations are ordered across it.

Record:

* whether units overlap
* whether traffic deadlocks
* whether the player can reasonably organize the crossing
* approximate performance
* any obvious algorithmic failure

Do not hide a failure.

If 30 formations cannot navigate the crossing reliably, identify why.

This is exactly what the prototype is intended to discover.

---

# 9. Second mobilization cycle

After the battle, return survivors and casualties to the settlement as in Prototype A.

Then allow enough recovery/time progression to mobilize another army.

The second mobilization should demonstrate that the first battle had persistent consequences.

For example:

First army:
2,000 people

After battle:
significant farmer / smith / retainer casualties

Second mobilization:

* fewer people available
* reduced equipment production
* reduced food production
* reduced samurai availability if elite losses were severe

Do not reset the settlement to a pristine fixture between wars.

I want to see whether repeated warfare naturally degrades the society supporting it.

---

# 10. Samurai-loss consequence

Make one explicit demonstration of the cost of elite losses.

If the player loses a large share of their samurai/retainers:

* available elite manpower should fall
* replacing that elite formation should be harder than replacing ordinary levies

Do not build the complete samurai political system yet.

A simple warrior-estate confidence or elite-availability indicator is enough if needed.

---

# 11. Enemy AI

Use simple tactical AI.

Enough behavior to:

* deploy a line
* protect ranged units reasonably
* engage the player
* react to a major flank if practical
* use samurai as stronger formations

Do not create sophisticated strategy AI.

The AI exists to provide resistance while evaluating battlefield control.

---

# 12. Performance measurement

Measure actual combat on this constrained battlefield.

Record representative results for approximately:

* 1,000 vs 1,000
* 2,000 vs 2,000

Optionally test larger if performance remains healthy.

Measure:

* median FPS
* p95 frame time
* simulation CPU cost
* any obvious navigation spike

More important than maximum FPS:

document whether pathfinding/separation becomes the dominant cost.

---

# 13. Prototype UI

Keep UI temporary.

Prioritize:

* readable formation selection
* selected formation count
* troop role
* strength
* morale
* fatigue
* routed state
* group assignment

If current labels become unreadable at army scale, simplify them.

Do not redesign the full SHŌEN HUD.

---

# 14. Do not work on these yet

Do not implement:

* final Japanese models
* animation polish
* detailed castle assaults
* generals
* scouting
* campaign routes
* diplomacy
* organic city districts
* religion
* artifacts
* naval systems
* final economy balance
* elaborate save migration

The focus is battlefield movement/control and repeated societal consequences.

---

# 15. Validation philosophy

Stay in prototype mode.

Use targeted tests for invariants that can corrupt the simulation.

For temporary controls and UI:

* smoke-test them
* play the actual battlefield
* fix obvious blockers
* move on

Do not create exhaustive acceptance matrices.

Do not stop for approval after every small subsystem.

---

# Deliverable

Stop when I can:

1. field a representative multi-formation army
2. deploy and move it as groups
3. maneuver through a constrained battlefield
4. fight using infantry, bows and samurai
5. use the alternate crossing to flank
6. experience real congestion at the bridge without formations simply overlapping
7. finish the battle
8. return casualties to the settlement
9. mobilize for a second war
10. see that the first war has reduced my future capability

Then report:

* what feels playable
* movement/pathfinding problems
* command/UI problems
* combat performance
* second-mobilization consequences
* technical risks discovered
* design risks discovered
* whether this reinforces or weakens the overall feasibility assessment
* recommended Prototype C

Commit the prototype when it reaches that state.
