# Prototype B rendered gameplay evidence

## Ordinary 2,320 vs 2,320 session

Command: `python3 tools/dev.py run --scenario terrain`. Actual Unreal 5.8.2 Metal game, 1280×720 viewport. Computer control supplied keyboard input; this is not a new human physical-input acceptance.

The initial session rendered the 6,000-person settlement. At displayed Day 4 it was paused, then U recruited 16×100 polearms, 6×100 bows and 3×40 samurai. F deployed both armies. Tab selected all 25 formations; Y issued a reserved line across the bridge; slash selected the three elite formations and O sent them toward the ford. Space resumed actual combat. F7 snapshots and F10 screenshots recorded authoritative state and rendered output.

### Failure discovered during play

At 109 seconds the primary bridge had one recorded completion, while the outgoing elite force had no ford completion. Routed friendlies returning through the single-lane ford blocked the elite approach. The stall remained at 183 seconds, with no friendly overlaps. This was a real pathing failure, not a cursor issue. [109-second state](demo/failure-ford-head-on.json), [image](demo/failure-ford-head-on.png), [183-second state](demo/failure-ford-still-blocked.json).

H retreated at 224.2 simulated seconds. The return transaction conserved all 6,000 people: 434 dead, 209 wounded and 1,677 healthy soldiers returned. The dead included 381 farmers, 39 laborers and 14 smiths. The settlement ran a few normal days during inspection, was paused, then P advanced seven further days. U remustered from the same society, with no N/reset or population/resource refill.

| Stage | Ready farmers | Ready laborers | Ready smiths | Ready retainers | Food produced/day | Basic gear/day |
|---|---:|---:|---:|---:|---:|---:|
| Before first muster | 3,400 | 1,000 | 200 | 120 | 10,200 | 40 |
| First army away | 1,600 | 700 | 100 | 0 | 4,800 | 20 |
| Immediately returned (visible HUD) | 2,835 | 942 | 180 | 120 | 8,505 | 36 |
| Recovered, Day 17 | 3,019 | 961 | 186 | 120 | 9,057 | 37 |
| Second army away | 1,219 | 661 | 86 | 0 | 3,657 | 17 |

Reserves still supported a second **2,320-person** army. This is an important design result: one war need not reduce headcount immediately, but it permanently worsens the society supporting it. During mobilization the food deficit worsened from 1,200 to 1,909/day, and equipment output fell from 20 to 17/day. The elite force suffered no losses in this failed-crossing session because it remained blocked on the home bank. The separate [actual-combat elite exposure test](core-evidence.md#persistent-second-war) establishes the cost of elite losses without claiming this session did so.

Snapshots: [baseline](demo/01-before-muster.json), [first army](demo/02-first-army.json), [deployment](demo/03-deployed.json), [contact](demo/04-bridge-contact.json), [returned](demo/05-returned.json), [recovered](demo/06-recovered.json), [second army](demo/07-second-army.json). The returned snapshot was captured after several campaign days; the immediate-return row above was read from the rendered HUD.

Images: [baseline](demo/01-before-muster.png), [first muster](demo/02-first-army.png), [bridge combat](demo/04-bridge-contact.png), [recovered society](demo/06-recovered.png), [second muster](demo/07-second-army.png).

## Input boundary

Rendered keyboard actions exercised: pause/resume, muster, battle deployment, mass/category selection, bridge/ford commands, retreat/return, seven-day recovery and remuster, plus optional snapshots/screenshots. Core tests cover line ordering, facing and reservations; the rendered benchmark assigns and uses control groups through the same authoritative command functions. A synthetic Ctrl+1 attempt did not assign a group, consistent with the already documented computer-control modifier limitation. This does not establish a physical-input regression; prior human foundation input acceptance remains separate. No mouse-coordinate correction or engine patch was introduced.

## Final rendered verification after the correction

The final build and all 18 Unreal regressions passed before this second ordinary session. It used the same run command and actual 1280×720 Metal viewport. The revised camera shows the bridge, ford label, woods, hill and both deployments. No benchmark reset occurred in this session.

The game was paused on displayed Day 9 with its first real 2,320-person army deployed. Tab/Y ordered everyone over the bridge; slash/O redirected the three samurai formations through the ford. Space resumed at normal battle speed. At 69.45 seconds one samurai formation had already reached x=2683 on the east bank via y=11200; the others were still approaching. At 129.7 seconds the snapshot recorded **9 ford completions, 1 bridge completion, 0 current/peak friendly overlaps**, 2,818 melee contact ticks, 5,770 ranged attack ticks, 917 flank attack ticks and 3,785 hill attack ticks. Completions count both directions and routed units; they are not nine successful offensive flanks. The samurai had fought and were routing west, with **54 dead, 25 wounded and 41 healthy** out of their original 120.

Bridge congestion remained: 16 waiting and 14 reserved-cell waits over ten seconds at that snapshot. Thus the ford blocker is corrected, but this is not a claim that active combat has no queues. The main force did not establish a supported battle line before the samurai's local fight. Sending the elite detachment unsupported was costly; the result does not prove the flank is balanced or tactically superior.

While paused, Tab/G accepted attack orders for **all 11 eligible formations**. Comma selected 16 polearm formations, I created a western destination line, and right bracket rotated its facing with visible destination markers and HUD feedback. Routing units were excluded from new orders. H then explicitly retreated at 129.7 seconds; this was not a victory or automatic battle resolution. It returned 1,606 healthy and 232 wounded and applied 482 deaths exactly once. The game stayed paused, so the following snapshots are exact immediate-return / seven-day-recovery / remuster states.

| Stage | Ready farmers | Ready laborers | Ready smiths | Ready retainers | Food produced/day | Basic gear/day |
|---|---:|---:|---:|---:|---:|---:|
| Original society | 3,400 | 1,000 | 200 | 120 | 10,200 | 40 |
| First army away | 1,600 | 700 | 100 | 0 | 4,800 | 20 |
| Returned, Day 10 | 2,824 | 942 | 199 | 41 | 8,472 | 39 |
| Recovered, Day 17 | 3,012 | 961 | 199 | 66 | 9,036 | 39 |
| Second army away | 1,212 | 661 | 99 | 0 | 3,636 | 19 |

Deaths by origin: **388 farmers + 39 laborers + 1 smith + 54 retainers = 482**. All 232 wounded recovered through P; the 1,280 dependents remained. U recruited **2,266 people**, including only **66 samurai** (40+26), despite 113 elite gear available before muster. The constraint was surviving elite manpower. The first and second mobilized food deficits were **1,200/day and 1,882/day**. F successfully deployed this second army, preserving the 482 dead and reduced worker counts. No N/reset, population refill, gear refill or debug mutation was used. The current fixture scales the next enemy's total to the raised army; it is not yet a persistent adversary simulation.

Final snapshots and corresponding F10 images:

- [Deployment](demo-final/01-deployed.json), [image](demo-final/01-deployed.png).
- [Ford approach at 69.45 seconds](demo-final/02a-ford-approach.json).
- [Combat and elite losses](demo-final/02-ford-combat.json), [image](demo-final/02-ford-combat.png).
- [Immediate return](demo-final/03-returned.json), [image](demo-final/03-returned.png).
- [Seven-day recovery](demo-final/04-recovered.json), [image](demo-final/04-recovered.png).
- [Second muster](demo-final/05-second-army.json), [image](demo-final/05-second-army.png).
- [Second deployment](demo-final/06-second-deployed.json), [image](demo-final/06-second-deployed.png).

This is actual rendered keyboard-driven gameplay, not a human physical-input acceptance. The final run confirms the ordinary controls and population loop; targeted tests separately prove all three elite formations cross and both ford directions clear. The separate [final performance measurements](measurements.md) use uninterrupted automated rendered combat after this session exited.
