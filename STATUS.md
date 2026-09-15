# SHŌEN status

## Kabuto 01 art-pipeline note — 2026-09-15

Kabuto 01 now has a modular Blender source, three runtime LODs (Unreal: 94,608 / 31,238 / 7,062 triangles), one opaque material atlas, and an isolated Unreal review on the unchanged prototype mannequin. The revised construction and materials passed source/import checks, a current Unreal build, portable tests, and rendered idle/walk/head-turn checks; static 100 / 500 / 1,000 helmet crowds measured 108.3 / 89.4 / 63.5 median FPS, with timing outliers and remaining visual regularity documented in the [evidence](artifacts/kabuto01/verification.md). [Asset and workflow](SourceArt/Characters/Samurai/Kabuto01/README.md); visual approval and full-army performance certification are not claimed, and no next armor component was started.

## Prototype B — constrained battlefield and repeated warfare

**Prototype B is complete and committed as a playable feasibility prototype.** Prototype A was accepted at `60ca49fb0416d12423eb8c57ed3e234eba17dedb`; its evidence is archived in [Prototype A status](docs/execution/prototype-a-status.md). M1, M2A and M2B remain accepted. This work follows the [Prototype B request](docs/execution/prototype-b-request.md), on `codex/prototype-b-terrain`. It does not start Prototype C or restore production-hardening approval milestones.

### What is playable

Run `python3 tools/dev.py run --scenario terrain` after `python3 tools/dev.py build`. [Controls and two-war walkthrough](README.md#play-prototype-b-terrain-and-repeated-warfare).

- One authored west/east battlefield: impassable river, narrow bridge, distant ford, open ground, slowing woods and a defensive hill. Shared geometry controls movement, height, selection and passive rendering.
- A real 6,000-person settlement fields **16×100 polearms, 6×100 bows and 3×40 samurai: 25 formations / 2,320 people**. Recruitment removes workers from their occupations and consumes gear. The opposing finite army has comparable mixed roles.
- Individual/box selection remains available. Tab/category keys select armies or roles; group line destinations reserve separate spaces, preserve approximate frontage order and accept facing rotation. Ctrl+1–9 assigns groups; 1–9 recalls. Y chooses bridge, O ford, G nearest-enemy attack, I western deployment line.
- Formation-level reservations produce real queues without soldier Actors or per-person pathfinding. Bows have range and weaker melee; samurai have stronger combat/higher morale but finite estate manpower and elite gear. Facing, flank, woods and hill modifiers matter. Simple enemies guard the east bank, position bows behind infantry and react to nearby flank threats.
- H ends an active battle as a retreat, or returns the army after a result. Casualties return transactionally to their original occupations. P advances recovery; U remusters from the same diminished World. N is the explicit whole-session reset and must not be used between wars.

### Crossing failure found and fixed

The first rendered run exposed a genuine opposing-traffic deadlock: at 109 seconds, routed troops returning through the single-lane ford blocked all outgoing samurai. At 183 seconds it remained stalled, with zero friendly overlap. [Preserved failure and gameplay evidence](artifacts/terrain/rendered-demo.md).

The cause was a one-cell ford plus retreating formations sharing a final home-exit destination. The fix is confined to the authored terrain/navigation model: a three-row ford, separate eastbound/westbound lanes, unique reserved retreat exits and no repeated orders for settled retreats. Renderer and simulation consume the same widened geometry. Mid-transit retargeting keeps its committed adjacent leg; facing rotation preserves a common chosen crossing. The Unreal attack helper also moves invalid bow standoff points out of impassable river terrain. No engine patch or mouse-coordinate adjustment was made.

Targeted results: **30/30 one-way bridge formations cross by 209.1 simulated seconds**, with zero overlaps and no remaining stuck formations at the 360-second budget; **12/12 opposing ford formations cross**, also without overlap or a remaining stall. The actual 2,320-person command sequence gets all three elite formations across. [Core evidence, including RED failures](artifacts/terrain/core-evidence.md).

### First war → recovery → second war, in the final rendered build

The final ordinary game fought for 129.7 seconds, then H explicitly retreated: **482 dead, 232 wounded, 1,606 healthy returned**. The dead were 388 farmers, 39 laborers, 1 smith and 54 retainers. After P recovered the wounded, U raised a second army and F deployed it, with **no reset or resource refill**.

| Capability | First army | Second army |
|---|---:|---:|
| Soldiers | 2,320 | 2,266 |
| Samurai | 120 | 66 |
| Food produced/day while away | 4,800 | 3,636 |
| Food deficit/day while away | 1,200 | 1,882 |
| Basic equipment produced/day while away | 20 | 19 |

Elite replacement was limited by the 66 surviving retainers, despite sufficient gear. Ordinary reserves still supplied 2,200 levies; the first war damages economic support before exhausting all ordinary recruitment. The unsupported elite flank was expensive. The final combat snapshot had 9 ford completions (including returning troops), zero friendly overlap, and real melee/ranged/flank/hill activity; bridge congestion still left 14 reserved-cell waits over ten seconds. [Full rendered sequence, snapshots and images](artifacts/terrain/rendered-demo.md#final-rendered-verification-after-the-correction).

### Commands and input evidence

Rendered keyboard play exercises pause/resume, muster, deployment, army/category selection, bridge/ford commands, attack, line deployment/facing rotation, return, recovery, second muster and optional F7/F10 capture. Automated integration additionally covers line rotation preserving route, hill-aligned formation rendering and population conservation. Benchmark setup selects and assigns main/elite control groups through the authoritative command path.

Prior **human physical input acceptance** remains recorded: cursor alignment, camera/formation controls, UI clicks and building interactions worked. This B run uses computer-controlled keyboard input; it is **not new human physical mouse acceptance**. Synthetic mouse/modifier delivery limitations remain, including an unsuccessful synthetic Ctrl+1 attempt. No reproducible physical pointer regression was established. The user's slight UI delay remains non-blocking; no speculative latency fix was applied.

F7 snapshots, F6 profiling and F12 cursor diagnostics are optional. Normal play has no permanent profiling or diagnostic cursor overlay. F7 records software state, not physical input-to-display latency.

### Final rendered combat performance

Final corrected build, 120 seconds per size after three-second warmup, one Unreal process at a time. Actual 1280×720 windowed Metal, Mac Development editor-game, M1 Max / 32 GB. Both runs exited 0 and validated real combat, both crossings and navigation samples.

| Per side | Median FPS | Frame p95 / worst ms | Simulation CPU p95 ms | Navigation p95 / worst ms | Peak overlaps |
|---|---:|---|---:|---|---:|
| 1,000 | 109.4 | 10.002 / 54.785 | 0.0308 | 0.0428 / 0.1435 | 0 |
| 2,000 | 108.6 | 10.083 / 43.295 | 0.0863 | 0.1131 / 0.2947 | 0 |

Navigation is not the measured frame-budget bottleneck; its largest sample is 0.295ms. Simulation samples are per render tick, navigation samples per 20Hz step, so their percentiles are not directly comparable. Frame hitches remain, with no established cause. Peak reserved-cell waits over ten seconds were 8 / 17 formations; low CPU cost does not remove tactical congestion. [Full measurement methodology, queue counts, raw reports and limitations](artifacts/terrain/measurements.md).

### Automated verification

Final code passed on 2026-09-15:

| Exact command | Result |
|---|---|
| `python3 -m unittest discover -s tools/tests -v` | 51/51 passed |
| `python3 tools/dev.py core-test` | 6/6 CTest targets passed, including ten terrain suites and accepted A invariants |
| `python3 tools/dev.py build` | ShoenEditor Mac Development succeeded, 22.66 seconds |
| `python3 artifacts/terrain/run-unreal-smoke.py` | 18/18 Shoen Unreal tests passed; zero errors/warnings, including foundation, placement, inspection, profiling, A and B |
| `python3 tools/dev.py combat-benchmark --terrain --per-side 1000 --seconds 120` | Exit 0, 13,041 rendered frames; validated |
| `python3 tools/dev.py combat-benchmark --terrain --per-side 2000 --seconds 120` | Exit 0, 12,957 rendered frames; validated |

[Tooling log](artifacts/terrain/tooling-tests.log), [core log](artifacts/terrain/core-tests.log), [build log](artifacts/terrain/build.log), [Unreal summary](artifacts/terrain/unreal-summary.json), [exact Unreal command](artifacts/terrain/unreal-command.json), [bounded integration review](artifacts/terrain/review-integration.md). Unreal regression automation uses NullRHI and makes no rendering claim; rendered gameplay and benchmarks are separate.

### Remaining limits and risks

- The navigation model is an authored four-neighbor grid with visible snapping/cardinal travel. A 30-formation unopposed bridge queue takes about 3.5 minutes. Opposing manual orders on the single-lane bridge can still require regrouping or the ford; contact deliberately stops traffic. Passing is a corridor rule, not general crowd avoidance.
- A formation holding outside enemy range needs another attack/order. The simple AI does not guarantee every battle resolves without further commands. The next enemy scales to the newly raised army; there is no persistent opposing society yet. H retreat is a valid finish. This prototype does not establish polished attack-move behavior or enjoyable command pacing.
- UI labels are selected-only and capped to limit clutter; the temporary sidebar/status panel occupies substantial screen space. Automatic frontage and coarse target reservations need human tactical playtesting. Physical B-specific mouse and modifier usability has not been newly accepted.
- Frame outliers require investigation; no GPU, engine or input-latency cause is assumed. These are placeholder, Development editor-game measurements on one Mac, not packaged/final-art capacity claims.
- Terrain and both prototype sessions are session-only; F5/F9 protect the legacy save slots. Economy remains the deliberately coarse A model: free immediate prototype construction, simplified recovery/production, no final balance or extended samurai politics.

### Feasibility and recommended Prototype C

The results reinforce technical feasibility of formation-scale navigation and a shared population/economy/combat ledger. They also expose the larger design risk: affordable computation does not ensure readable orders or satisfying congestion and flank timing.

**Recommended C:** a bounded combined-arms command and battle-pacing playtest on this same map. Make attack/hold intent and queue feedback clear, test line width and supported flanks with a human, and profile the observed frame hitches. Keep the same society and terrain; do not add campaign systems or final art. **C has not begun.**
