# SHŌEN status

## Current task: core-loop feasibility prototype

**VERIFIED — the integrated settlement → army → tactical battle → settlement consequence loop is playable.** Work stops at this prototype. This is feasibility evidence, not a completed beta or production acceptance. [Authorized request](docs/execution/core-loop-prototype-request.md), [execution plan](docs/execution/core-loop-prototype.md), [play instructions](README.md#play-the-integrated-prototype).

Implementation is on `codex/core-loop-prototype`, based on the profiling preservation checkpoint `8d69fa3`. The earlier accepted foundation remains M1 `44c33ca14de4669031e7e85ab7f157476f5a0a23`, M2A `f27632b05e124934779b3dc574b017851608859d`, and M2B `396bf5e0f2dd22222edf1a6cbf5bb6c873cfc954`.

## What is playable

- **640-person settlement:** 320 farmers, 160 laborers, 40 smiths, 40 retainers and 80 dependents. Six placed placeholder building types: houses, agricultural fields, granary, smithy, manor and retainer training. Existing placement/rotation/validation/cancellation handles additional buildings.
- **Daily economy:** food consumption, continuous simplified agriculture, general-labor timber/iron/fuel production, smith production using those resources, and distinct basic/elite gear. Houses affect workforce productivity, farms enable food, granaries add food capacity, smithies enable equipment, manor/training enable elite recruitment and production. Rules are data-driven in [prototype.json](game/Content/Domain/Data/prototype.json).
- **Real mobilization:** M farmer spears, L laborer spears, J emergency smith spears, K farmer bows, T samurai. Ordinary formations default to 50, smith levy to 20, elite foot to 20. Recruitment removes available workers and appropriate gear; exact district/cohort/occupation/skill/estate origins remain in service records. No presentation object creates people.
- **Actual tactical battle:** F deploys against a finite equal-size enemy army. Movement, facing, contact melee, ranged attacks/tracers, casualties, morale, routing and fatigue run at 20 Hz while campaign time freezes. Every player formation remains selectable; right-click/drag orders and existing groups remain available. G advances selected formations, or all if none are selected. Elite foot troops are stronger, but lose effectiveness when flanked/exhausted and can lose to overwhelming numbers.
- **Return and consequences:** H returns after a result or retreats during fighting. One atomic candidate applies battle dispositions and demobilization through the existing ledger, returns surviving equipment and commits one operational day. Dead remain dead; wounded recover into their original cohorts after seven days. Repeated return cannot duplicate people, gear or the day. P advances seven campaign days; normal speed controls also work.
- **Minimal presentation:** workforce/away/recovering, food/materials/gear, production, army composition, battle losses and last outcome. F6 profiling and F12 cursor diagnostics remain off by default.

## Rendered gameplay demonstration

Launch: `python3 tools/dev.py run --scenario prototype`. Actual 1280×720 windowed Unreal game on this Mac. [Full observed sequence and representative screenshots](artifacts/prototype/rendered-demo.md).

| Stage | Farmers available | Smiths available | Retainers available | Food produced / day | Basic gear / day |
|---|---:|---:|---:|---:|---:|
| Before mobilization | 320 | 40 | 40 | 960 | 8 |
| 240 people mobilized | 170 | 20 | 20 | 510 | 4 |
| Returned after battle | 278 | 28 | 35 | 834 | 5 |
| Seven days after return | 291 | 32 | 36 | 873 | 6 |

The rendered **240 vs 240** battle ended in victory after approximately **43 simulated seconds**, with **57 player deaths, 26 wounded and 157 healthy survivors**. The smaller samurai formation retained 15 of 20 soldiers while ordinary formations routed. Return advanced Day 8 to Day 9 once. Seven days later, all wounds had healed but 57 deaths remained: 29 farmers, 16 laborers, 8 smiths and 4 retainers. Living population was 583. Food net changed from +320 before mobilization to −130 while mobilized, +251 immediately after return, and +290 after recovery.

Keyboard recruitment, deployment, advance orders, pause/resume, return and fast-forward were visibly exercised through computer control. Bow tracers, contact losses, shrinking formations, morale, fatigue and routing were observed. The final readability changes were subsequently viewed during rendered combat.

**Input evidence boundary:** this was not new human physical-input acceptance. Computer-control mouse click and Ctrl+A did not activate their intended actions in the ordinary demo, matching the existing automation limitation; no new human cursor failure was reported. Earlier human physical M1/M2A/M2B acceptance remains distinct. Core/group tests and scripted benchmark orders provide separate command evidence. This does not create another approval gate under the user's feasibility-mode request.

## Actual combat performance

Unreal **5.8.2 / CL 56702186**, Mac Development editor/game, **Metal SM5**, Apple **M1 Max / 32 GB**, macOS 26.6.2. Actual **1280×720 windowed** viewport. Each run starts full armies, uses 50-person spear/bow formations, has a three-second warmup and measures 45 seconds of real combat. Standing counts decline with casualties. Runs were serial, with no concurrent builds/heavy tests; F6/F12 off, VSync off, `t.MaxFPS 0`.

| Soldiers per side | Formations total | Median FPS | Frame median / p95 | Simulation CPU p95 per game tick | Peak friendly overlap pairs |
|---|---:|---:|---:|---:|---:|
| 500 vs 500 | 20 | 120.0 | 8.33 / 9.00 ms | 0.011 ms | 4 |
| 1,000 vs 1,000 | 40 | 113.3 | 8.82 / 9.39 ms | 0.022 ms | 24 |
| 2,000 vs 2,000 | 80 | 120.0 | 8.33 / 8.99 ms | 0.047 ms | 103 |

All runs recorded genuine contact, ranged attacks and casualties on both sides. Scripted selection/group/advance batches accepted **23 / 27 / 28 formation orders**, with p95 dispatch cost below 0.010 ms. This is not physical input latency. Worst observed frames were **44.13 / 41.72 / 75.14 ms**; short-run host/render pacing variation remains. The faster 2,000 run does not imply inverse scaling. Most render ticks have no combat step, so near-zero simulation medians are not per-step costs. Peak process memory was roughly 3.3 GiB.

[Detailed measurements, exact commands and limitations](artifacts/combat/measurements.md). Raw JSON: [500](artifacts/combat/combat-500.json), [1,000](artifacts/combat/combat-1000.json), [2,000](artifacts/combat/combat-2000.json). The 500/1,000 combat windows were visually inspected; 2,000 was measured through the same actual rendered path and finished before direct visual inspection. No claim of final graphics, obstacle pathfinding, other hardware or packaged performance.

## Automated verification

Final commands and observed results (2026-09-15):

| Command | Result |
|---|---|
| `python3 -m unittest discover -s tools/tests -v` | Exit 0; **47/47** |
| `python3 tools/dev.py core-test` | Exit 0; **CTest 5/5**, including seven targeted prototype suites |
| `python3 tools/dev.py build` | Exit 0; **ShoenEditor Mac Development** |
| `python3 artifacts/prototype/run-unreal-smoke.py` | Exit 0; **17/17 Unreal tests**, zero test errors/warnings; includes `Shoen.Prototype.IntegratedLoop` |
| `python3 tools/dev.py combat-benchmark --per-side 500 --seconds 45` | Exit 0; rendered report validated |
| `python3 tools/dev.py combat-benchmark --per-side 1000 --seconds 45` | Exit 0; rendered report validated |
| `python3 tools/dev.py combat-benchmark --per-side 2000 --seconds 45` | Exit 0; rendered report validated |

The single-process Unreal runner executes `-ExecCmds=Automation RunTests Shoen.` with `-TestExit=Automation Test Queue Empty -unattended -NullRHI`; [exact argument array](artifacts/prototype/unreal-command.json), [per-test results](artifacts/prototype/unreal-summary.json), [logs](artifacts/prototype/). NullRHI tests are not rendering measurements. `python3 tools/dev.py editor-test --suite prototype` is also available for the focused integrated smoke test.

Targeted core tests cover worker/output reduction, equipment/estate/origin constraints, deterministic combat and frozen/paused clocks, real ranged/contact damage, elite strength and counters, outcome/recovery conservation, duplicate-return rejection and scale smoke. Integration review fixed battle pause, inherited seed reserve conflicting with food depletion, forward contact overshoot and the one-time operational day. [Focused independent review](artifacts/prototype/review.md).

## Simplifications and remaining risks

- **Movement quality is the main technical risk.** Contact standoff works, but no friendly avoidance, obstacle navigation or congestion resolution exists. Friendly overlaps rose to 103 pairs at the largest tested size. Targeting/congestion work is quadratic in formation count; it remains cheap at 80 formations on this host. A formation-level spatial grid/local avoidance and terrain corridor planning are plausible next approaches if bottleneck tests require them. No engine rewrite is justified by these results.
- Placeholder bodies, rigid formations, pulsed arrow tracers and labels. No individual combat animation/collision, siege or terrain effects. Routing labels can overlap HUD text at scale, and recruited formations overlap while idle in the settlement. These are known presentation limits; further polish is deferred.
- **Session-only prototype.** No prototype/battle persistence. F5/F9 explain the limitation and do not overwrite accepted legacy saves. Existing foundation/placement saves still work in their separate scenarios.
- Instant, free prototype construction; simple capacity/eligibility building functions. Agriculture is continuous daily production; general labor produces an abstract resource basket. No worker assignment logistics, seasons, construction labor, storage transport or final balance. Food shortfall is reported; starvation, migration and growth are not implemented.
- Basic gear is a shared bow/polearm abstraction; elite gear is separate. No final smith apprenticeship/quality progression, horses or bespoke cavalry mechanics. Cavalry was not evaluated.
- Enemy army is an authored finite fixture, with nearest-visible-enemy battlefield logic, no campaign AI or opponent economy. Casualty allocation and two-dead/one-wounded split are deterministic approximations. No morale contagion, supply lines, pursuit/capture or army campaign travel.
- **Design risk remains:** this proves the mechanical connection, not that the balance is fun. Current stocks/production are generous, losses can reduce consumption as well as output, and open-ground fights resolve quickly. Terrain, recovery pacing and meaningful deployment choices need playtesting.
- Development editor/game only, one Mac and short measurements. No certification of larger armies, final animated art, packaging or other platforms. Minor UI latency remains known and non-blocking.

## Latency work preserved

The user explicitly made M2C latency non-blocking and changed strategy. [Preserved investigation](docs/execution/milestone-2c-status.md), [F6 profiling guide](docs/execution/milestone-2c-profiling.md), [measurements](artifacts/latency/measurements.md). Selection logic measured about 0.03–0.05 ms and replay-to-backbuffer about 16 ms; placement about 24 ms including the next-frame view update. These are software endpoints, not physical input-to-photon measurements. No speculative engine/coordinate fix or default frame cap was applied. Final physical M2C capture was not completed and is no longer blocking. Revisit only if interaction becomes materially worse.

## Feasibility assessment and next prototype

**The central loop is technically and mechanically feasible at the tested prototype scale, and promising enough to continue.** The shared population ledger, worker-dependent economy, equipment gates, tactical casualties and return-home consequences work together. No measured compute/representation limit materially threatening the concept appeared through 2,000 vs 2,000. Fun and terrain-aware tactical quality remain unproven.

**Recommended next feasibility prototype:** one constrained battlefield with a village edge, a narrow crossing and a flanking route. Test formation separation, pathfinding/congestion and group commands at the same army sizes, then carry losses through a second mobilization cycle. Evaluate whether terrain and deployment choices create better decisions. Do not begin it automatically.
