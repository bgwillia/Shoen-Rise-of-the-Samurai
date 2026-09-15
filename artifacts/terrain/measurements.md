# Prototype B — final rendered constrained combat measurements

2026-09-15, after the ford/retreat reservation and command fixes. Unreal **5.8.2 / CL 56702186**, Mac Development editor `-game`, Metal SM5, Apple M1 Max (10 CPU / 32 GPU cores), 32 GB, macOS 26.6.2. The actual viewport was **1280×720 windowed**, despite the wrapper requesting 1600×900. One Unreal process ran at a time; this task ran no builds or heavy tests during these captures. F6/F12 were off, VSync off, `t.MaxFPS 0`.

Each run has a three-second warmup, resets its benchmark fixture once, then measures 120 wall-clock seconds of actual 20Hz combat. Main infantry/bows and elite formations are selected, assigned groups 1/2 and ordered once through the bridge/ford respectively. Both final captures remained in their first measured battle; neither needed an in-capture restart. These isolated benchmark fixtures do not establish the persistent second-war loop: that was demonstrated in the separate ordinary rendered session.

## Frame and simulation cost

| Soldiers per side | Formation Actors total | Median FPS | Frame median / p95 / worst ms | Simulation CPU median / p95 / worst ms | Navigation median / p95 / worst ms |
|---|---:|---:|---|---|---|
| 1,000 | 22 | 109.4 | 9.139 / 10.002 / 54.785 | 0.0015 / 0.0308 / 0.2296 | 0.0163 / 0.0428 / 0.1435 |
| 2,000 | 44 | 108.6 | 9.212 / 10.083 / 43.295 | 0.0013 / 0.0863 / 0.3302 | 0.0491 / 0.1131 / 0.2947 |

Simulation CPU covers the core update inside each rendered game tick; most render ticks contain no 20Hz simulation step. Navigation covers each actual terrain movement/AI/separation step, with **2,400 samples per capture**. These have different sample populations: do not divide their p95s or sum them. The optional timing hook is outside deterministic state and performs no clock reads when disabled.

Navigation is a material part of the simulation work, but it does **not dominate the measured frame budget**: the largest measured terrain step was 0.295ms, compared with a roughly 9.2ms median frame. The data do not isolate every other CPU subsystem or the GPU. They do not justify an engine rewrite, per-soldier navigation or speculative optimization. Worst frames of **54.8ms and 43.3ms** remain unexplained; this is no input-to-photon latency claim. One capture per size cannot establish a scaling law or explain differences from the archived pre-fix baseline.

## Real combat, queue behavior and crossings

| Per side | Contact / ranged attack ticks | Player / enemy killed or wounded | Bridge / ford completions | Peak waiting / stuck | Peak friendly overlap pairs | Path requests / failed detours |
|---|---|---|---|---|---:|---|
| 1,000 | 1420 / 2797 | 314 / 212 | 2 / 5 | 14 / 8 | 0 | 813 / 663 |
| 2,000 | 2437 / 3955 | 453 / 290 | 1 / 7 | 23 / 17 | 0 | 2014 / 1514 |

Both sizes recorded flank and hill attack ticks. Crossing completions include both directions and routing units, not only offensive crossings. Waiting includes contact stops; stuck means a current reserved-cell wait over ten seconds, excluding contact stops. Failed paths here are temporary dynamic detour attempts in an occupied grid, not a count of rejected player orders. Peaks include both armies and describe congestion during combat, not a final unopposed clearing test.

The low bridge completion counts and long waits are significant gameplay findings, even with zero overlaps and cheap navigation. Opposing defenders stop a queued army; a flank needs support and another attack order after crossing. The separate unopposed 30-formation stress clears in 209.1 simulated seconds; the opposing 6+6 ford test clears without a remaining stall. This does not solve arbitrary opposite manual orders on the narrow bridge.

## Exact commands and reports

- `python3 tools/dev.py combat-benchmark --terrain --per-side 1000 --seconds 120` — **exit 0**, wrapper validated actual combat, finite timings, navigation samples and both crossings; 13,041 frames, 2 accepted group orders, command-batch p95 0.114ms, peak process memory 3.36GiB. [Raw report](../combat/combat-terrain-1000.json), [complete launch/output log](combat-1000.log).
- `python3 tools/dev.py combat-benchmark --terrain --per-side 2000 --seconds 120` — **exit 0**, wrapper validated actual combat, finite timings, navigation samples and both crossings; 12,957 frames, 2 accepted group orders, command-batch p95 0.391ms, peak process memory 3.37GiB. [Raw report](../combat/combat-terrain-2000.json), [complete launch/output log](combat-2000.log).

Standing instances decline with real casualties; there are zero soldier Actors. All orders in these timing runs are scripted through project command functions, not physical input-latency tests. Formation footprints, fixed corridors, primitive instancing and simple AI remain prototype approximations. No final animation, generalized navmesh, individual collision, packaged build, other hardware or capacity beyond these sizes is claimed.

The earlier [1,000](before-ford-fix-1000.json) / [2,000](before-ford-fix-2000.json) reports remain explicitly archived as pre-correction evidence. [Rendered gameplay and second mobilization](rendered-demo.md#final-rendered-verification-after-the-correction), [targeted core stress and conservation tests](core-evidence.md).
