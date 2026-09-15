# Prototype B portable core evidence

**Current status:** the rendered opposing-traffic failure was reproduced and corrected after the initial baseline below. Ten terrain suites now pass; full CTest remains 6/6. The final section records the current ford lanes, routed-exit reservations, actual 2,320-person command sequence and remaining limitations. Earlier performance tables are the pre-correction baseline, not the final rendered performance result.

## Verified scope

The same DomainCore sources compile under CMake and Unreal. New files are `domain/Terrain.h`, `sim/Terrain.cpp`, and `core/tests/test_terrain.cpp`; Prototype.h/.cpp integrate terrain movement, formation-scale contact, elite reports and enemy army setup. Existing World, Battle and SaveCodec remain unchanged.

The initial six targeted terrain suites passed; the final terrain executable has ten suites, and the complete portable CTest run passes 6/6, including all accepted Prototype A tests. Real initial failures, mid-transit retarget failures, and review failures are preserved in `core-red.log`, `core-retarget-red.log`, and `core-review-red.log`.

Commands from repository root:

```sh
/opt/homebrew/bin/cmake -S core -B /tmp/shoen-terrain-core -DCMAKE_BUILD_TYPE=Release
/opt/homebrew/bin/cmake --build /tmp/shoen-terrain-core -j4
/tmp/shoen-terrain-core/domain_terrain_tests
/opt/homebrew/bin/ctest --test-dir /tmp/shoen-terrain-core --output-on-failure
```

## Fixed battlefield and movement

Shared geometry exposes west/east deployments, an impassable river, bridge at y=0, ford at y=9600, forest movement factor 0.55 and a 550cm hill. A fixed 1600cm four-neighbor grid reserves both current and next cells. Final destinations reserve unique formation spaces. Deterministic grid routes use stable ID priority and try dynamic detours when occupied cells block progress. Group line commands preserve current frontage ordering, including headings crossing the -pi/pi boundary. Mid-transit retargeting preserves the current adjacent-cell leg; a unit already committed to one crossing can finish that leg when the rest of its group receives an alternate-crossing order.

Enemy infantry guard the east bank; bows deploy behind them and reposition into range; samurai react to nearby eastern-bank threats. Terrain contact distance is 1500cm for 100-person formation footprints; non-bow reach is 1650cm and bow range is 7000cm. Hill defense/attack and flank attack ticks are recorded. Routed troops use the ford for westward retreat to avoid reversing into primary-bridge traffic. Stationary and queued troops recover fatigue.

## Thirty-formation bridge stress

Real recruitment creates 30 formations of 100 people. Enemy combat is disabled and the enemy moved away for this isolated traffic test; its results are not combat performance claims.

- All 30 crossed the primary bridge by **209.1 simulated seconds**.
- The test continues through a 360-second budget: final waiting=0, stuck=0, peak friendly overlap=0.
- 1,663 path requests, including 1,612 failed dynamic detour attempts while the narrow queue was occupied.
- Total CPU for 360 simulated seconds: **73.33ms** in the final portable Release capture (`core-ford-green.log`); the earlier baseline was 68.70ms.

The failed-detour counter measures unsuccessful temporary replanning attempts, not rejected player commands or lost formations. `waiting_formations` includes reserved-cell waits and contact-stopped movement; `stuck_formations` counts a current reserved-cell wait exceeding 10 seconds, excluding contact-blocked movement from the deadlock classification. The 3.5-minute clearing time is a real command/pacing limitation; this is reliable serialization, not sophisticated crowd maneuvering. Opposition/contact and conflicting orders can still create much longer waits. The fixed graph has no generalized navmesh or local continuous steering.

## Initial constrained combat baseline

These pre-ford-correction figures measure portable simulation CPU only, not Unreal rendering or FPS. The 180-second advance budget stops early if combat resolves.

| Per side | Actual simulated time | 20Hz steps | Total CPU | Navigation median / p95 | Contact ticks | Ranged ticks | Total dead | Peak friendly overlap |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1,000 | 115.35s | 2,307 | 17.01ms | 0.00296 / 0.01638ms | 2,300 | 3,751 | 509 | 0 |
| 2,000 | 180s | 3,600 | 83.15ms | 0.01200 / 0.03988ms | 2,658 | 5,044 | 663 | 0 |

Both tests record bridge and ford completions, hill attack ticks and flank attack ticks. Crossing completions include all directions and routing soldiers; they are not a count of successful offensive flanks. The default attack sends infantry/bows through the bridge and elite units through the ford.

Navigation timings use the optional thread-local `SetTerrainTimingHook`. The clock is read only when the hook is enabled; measured durations are absent from deterministic state. Terrain behavior matches for one 5-second advance and 100 advances of 50ms.

## Persistent second war

The 6,000-person settlement has 3,400 farmers, 1,000 laborers, 200 smiths, 120 retainers and 1,280 dependents. Its real first muster raises 16x100 polearms, 6x100 bows and 3x40 samurai: **2,320 people**, including 100 smiths.

The targeted consequence test is scripted, not physical user play: after real muster and battle initialization, it places the three elite formations at x=4800 and y=-1600/0/1600, then advances 180 seconds of actual opposing combat while the ordinary army remains back. After 60 elite deaths, transactional return, one operational day and seven recovery days, the same World fields **60 samurai and 2,260 total people** in its second muster. No reset or resource refill occurs. After recovery and before the second muster, ready cohorts are 3,400 agriculture / 1,000 labor / 200 smith / 60 retainer. The second muster removes 1,800 agriculture / 300 labor / 100 smith / 60 retainer, leaving 1,600 / 700 / 100 / 0 available respectively; all 1,280 dependents remain. Conservation remains 6,000 including dead; service origins are retained. Malformed battle membership rejects return without changing World.

## Limits

This is an authored fixed-grid prototype. Destination snapping, cardinal travel, long single-lane queues, broad defensive AI and abstract ranged attacks remain visible simplifications. These tests establish accounting, deterministic routing and representative combat; rendered feel, frame time and command usability are measured separately by the integrated Unreal runs. Prototype B benchmark scope is 1,000 and 2,000 per side; Prototype A retains its 500-person benchmark.

## Rendered opposing-traffic blocker and correction (current)

The one-way bridge stress did not cover opposing traffic. The real 2,320-person run ordered the whole army over the bridge, then redirected the samurai through the ford. At 109.1 seconds its saved snapshot had 1 bridge completion, 0 ford completions, 29 waiting formations, 23 stuck formations, and zero overlap. The ford was a single traversable grid row: westward routed formations blocked eastward samurai. This was an actual rendered failure, not a theoretical risk.

Two focused portable RED tests reproduced it: six formations in each direction completed zero crossings, and the exact all-bridge-then-elite-ford sequence got zero elite formations across by 360 seconds. Widening alone let the real army flank but still failed the symmetric opposing-traffic test. The correction therefore uses:

- A shared ford rectangle from y=7200 to y=12000, exposing grid rows at y=8000, 9600 and 11200. Eastward traffic uses the northern lane; westward traffic uses the southern lane. The crossing center remains y=9600. Renderer and movement read the same geometry.
- Unique reserved home-exit cells for routed formations. Previously several retreating units selected the same final cell; the first parked there and backed up all following traffic. A targeted test observed only 1 of 3 settled; now all 3 settle without overlap or a stuck queue. Settled retreats are not reissued every tick.
- The original one-cell bridge remains unchanged. This is a fixed-corridor traffic rule, not a generalized avoidance system.

Current targeted results (`core-ford-green.log`):

- Opposing ford traffic: **6 eastward and 6 westward crossed**, zero overlap, zero remaining stuck formations.
- The original 30-formation bridge test is unchanged: all cross by **209.1 simulated seconds**, zero overlap/stuck at the 360-second budget.
- Exact 2,320-person all-Y then elite-O command sequence: all **3 elite formations crossed**. A scripted nearest-enemy attack command at 120 seconds accepted 10 orders and rejected one bow standoff target in blocked terrain. At 360 seconds waiting=0, stuck=0, peak overlap=0. The battle remained in Fighting because some troops held outside engagement range; the test explicitly used retreat/return to finish, and validated the same 6,000-person ledger. This is scripted simulation evidence, not physical user play or an automatic-victory claim.
- Both 1,000 and 2,000 actual combat tests retain melee, ranged, hill and flank activity. Their post-fix CPU samples are in the same log; total wall times varied with concurrent machine load and are not used as a rendering or architecture-cap claim. Fresh Unreal performance runs are required after this algorithm change.
- Full portable regressions pass **6/6** (including accepted A); the terrain executable now contains ten targeted suites. No Unreal process was started by the core worker.

Remaining limitations: opposite manual orders on the narrow bridge can still require player reorganization or the ford; contact can deliberately stop forward traffic; formations that reach their reserved line outside enemy range need another attack order. The raw scripted nearest-enemy test can reject a bow standoff point in blocked terrain. The final Unreal G helper advances that point toward its target until it is traversable; the final rendered session verifies that project-level command path. The metrics distinguish reserved-cell waits over 10 seconds from contact stops, and failed dynamic-detour retries from failed player orders. No maximum-capacity conclusion is claimed.
