# M2C investigation record

> Superseded as the active task on 2026-09-15 by the core-loop feasibility prototype request. The user made slight UI latency non-blocking. Physical M2C capture was not completed; the measurements below remain software/replay evidence. Preserve diagnostics; do not optimize further without materially worse interaction.

## Current milestone

**Milestone 2C — interaction latency investigation: final physical capture pending.** Automated checks and repeated rendered measurements pass. No gameplay latency change is justified by the evidence so far. This work starts from accepted M2B commit `396bf5e0f2dd22222edf1a6cbf5bb6c873cfc954` on `codex/milestone-2c-latency`.

[Authorized request](milestone-2c-request.md), [execution record](milestone-2c-latency.md), [profiling procedure and measurement boundaries](milestone-2c-profiling.md). Earlier acceptances remain intact: [M1](milestone-1-status.md), [M2A](milestone-2a-status.md), [M2B](milestone-2b-status.md). The previously resolved physical cursor issue has not reappeared. No later gameplay milestone has begun.

## Findings and root cause

The dominant **measured software interval is the game/render pipeline after interaction logic**, not building lookup, simulation transactions or a delayed UI timer. In the final uncapped runs, selection takes about 0.03–0.05 ms of logic and reaches the matching backbuffer in about 15.6–16.1 ms. At 100 buildings, successful placement takes 0.95 ms of logic and about 24.8 ms overall.

- Selection, clearing, rotation and preview presentation are applied during the action's game frame. The matching frame reaches the backbuffer later; a matching frame number identifies its content, not simultaneous CPU/display completion.
- Successful placement commits synchronously. GameMode observes its changed view generation on the **next game frame** and rebuilds instances. The measured rebuild itself takes only 0.02–0.04 ms. That additional ordinary update boundary explains the extra frame for a new building.
- In the uncapped runs, most selection time is split between waiting for the matching scene's render-thread work to begin and reaching its backbuffer. These are queued rendering stages, not a 15 ms authoritative lookup.
- A temporary **60 FPS** control leaves selection logic at 0.028 ms but reduces its replay-to-backbuffer median to **2.14 ms**; placement takes **18.91 ms**, including its next-game-frame update. This shows that rendering queue depth and pacing materially affect the software endpoint. A lower frame rate also changes physical input sampling, so this is **not proof of a physical input-to-screen improvement**.
- No abnormal selection/preview throttle, campaign-day wait, delayed delegate, asynchronous handoff or file operation was found in these action paths. Selection updates only its highlight. Save/load file work belongs to explicit save/load actions. Repeated whole-World validation becomes measurable at 100 buildings but remains below one millisecond in successful placement logic here.

**No gameplay optimization, default frame cap, engine patch or coordinate adjustment was applied.** The evidence supports ordinary update/render queuing. Physical switch-to-Slate delay, GPU completion and actual display scanout are outside the software measurements; they must not be inferred from these numbers.

## Measurements

Host: Unreal **5.8.2 / CL 56702186**, Mac Development editor/game, Apple M1 Max, 32 GB, Metal SM5. Actual viewport **1280×720, windowed**, despite the wrapper requesting 1600×900. F12 diagnostic logging was off. Uncapped frame medians were approximately 8.3 ms; the 60 FPS control measured 16.67 ms.

### Representative interactions: 10 initial buildings

Milliseconds, **median / worst**, 30 repetitions per action. These are deliberately labelled **replay** samples: input-to-logic is unavailable because the harness dispatches controller actions without physical/Slate input. Total starts at replay dispatch; the endpoint is the matching backbuffer-ready callback on the render thread.

| Interaction | Input → logic | Logic | Logic → backbuffer | Total |
|---|---:|---:|---:|---:|
| Select building | N/A | 0.031 / 0.064 | 15.908 / 17.053 | 15.939 / 17.087 |
| Clear selection | N/A | 0.017 / 0.020 | 15.982 / 56.138 | 15.999 / 56.156 |
| Switch A → B | N/A | 0.032 / 0.069 | 15.825 / 16.705 | 15.858 / 16.761 |
| Enter placement | N/A | 0.012 / 0.015 | 15.568 / 16.798 | 15.581 / 16.809 |
| Rotate preview | N/A | 0.065 / 0.103 | 16.001 / 17.259 | 16.071 / 17.318 |
| Place successfully | N/A | 0.124 / 0.156 | 24.290 / 27.802 | 24.412 / 27.945 |
| Reject overlap | N/A | 0.074 / 0.100 | 16.116 / 17.488 | 16.199 / 17.553 |
| Cancel placement | N/A | 0.009 / 0.011 | 16.265 / 16.914 | 16.275 / 16.923 |

The 56.16 ms clear outlier was after logic; it is retained, not discarded or described as a simulation stall. Thirty repetitions show the observed distribution, not statistical certainty.

### Scene-size comparison

| Interaction | Logic median, 1 / 10 / 100 buildings (ms) | Total median, 1 / 10 / 100 (ms) |
|---|---:|---:|
| Select | 0.029 / 0.031 / 0.049 | 15.58 / 15.94 / 16.07 |
| Clear | 0.015 / 0.017 / 0.034 | 15.54 / 16.00 / 16.09 |
| Switch | N/A / 0.032 / 0.051 | N/A / 15.86 / 16.12 |
| Enter | 0.012 / 0.012 / 0.012 | 15.51 / 15.58 / 16.07 |
| Rotate | 0.049 / 0.065 / 0.286 | 15.69 / 16.07 / 16.38 |
| Place | 0.071 / 0.124 / 0.949 | 23.76 / 24.41 / 24.80 |
| Reject | 0.044 / 0.074 / 0.486 | 15.56 / 16.20 / 16.34 |

Cancellation follows a successful placement and therefore uses actual counts **2/11/101**. Its figures and every scene's median/worst, preview cohorts and core sub-stages are in the [complete measurement tables](../../artifacts/latency/measurements.md); p95 and raw counts are in the [validated report](../../artifacts/latency/measured-report.json).

The fixtures use the same flat terrain, catalog, camera and initial remaining resources. Real transactions create each fixture. Thirty cycles per count produce **870 observed visual changes**, with **zero pending, superseded or dropped records** in these serial replay runs. Additional cached/unevaluated preview polls are recorded without inventing a new visual response. This is a small-scene comparison, not dense-settlement certification.

### Preview behavior

Preview updates are **frame-driven** during placement, including when the campaign is paused. Cursor deprojection and terrain intersection occur in PlayerTick; validation is cached by position/yaw/World revision. Presentation refresh does not wait for a campaign day. At 10 buildings, replay validation misses take 0.067 ms median / 0.124 ms worst; cached refresh takes about 0.029 ms median. Deterministic replay points bypass physical cursor deprojection; the separate physical capture covers that path.

### Physical input verification

The final ordinary game was launched, F9 loaded the existing five-building save, and the HUD rendered readably. The user has been asked to collect a short F6 physical capture covering selection/clear/switch, HUD building controls, preview motion, successful and rejected placement, cancellation and save/load/reselection. Its input-receipt timings and human result are pending; earlier M2B physical acceptance is not being relabelled as new M2C evidence.

## Changes and profiling overhead

- Added F6 opt-in capture, passive Slate observation, controller/UI/domain/presentation stages and exact scene/HUD/frame/window correlation. Timings use monotonic `FPlatformTime::Cycles64`. No per-event logging or permanent overlay; Shipping cannot start profiling.
- Added bounded input/action/frame storage with explicit loss counters. Cached/no-point preview and unchanged selection do not claim new visible changes. Replaced messages and state invalidate old markers. Tests cover stale input, input overflow, nested scopes, exact frame/revision joins and supersession.
- Added transient 1/10/100-building fixtures and replay. Save/load/reset/nested fixture operations are guarded; original World/catalog/message are restored. Tests verify existing save bytes and restored state. Normal settlement save and backup remained byte-identical through every automated fixture run.
- Added an optional, engine-independent placement observer; validation/commit/resource timing does not alter transaction rules or serialization. Added report validation and profiling test routing.
- Reduced **profiler** overhead by skipping idle scene/HUD snapshot commands and retiring already-observed markers. Two earlier enabled 100-building runs measured 9.45/8.70 ms median frame times; final capture measured **8.30 ms**, versus **8.33 ms** with profiling disabled. Host/render variation prevents attributing all of that difference to the change. Matched replay phases show small timing overhead (approximately 4–68 microseconds in selected action medians), not zero overhead. This was a diagnostic improvement, not a gameplay latency fix.

[Independent review](../../artifacts/latency/review.md) found no remaining actionable issue. [Operator guide](milestone-2c-profiling.md) describes F6, bounds, stage meanings, safe fixtures and reproducible commands.

## Automated verification

All final checks passed after the last code change. [Serial regression runner](../../artifacts/latency/run-final-tests.py) invokes the first three exact commands below, then runs all four Unreal suites in one editor process. It verifies the expected suite counts and every reported result.

| Command | Result |
|---|---|
| `python3 -m unittest discover -s tools/tests -v` | Exit 0; 43/43 |
| `python3 tools/dev.py core-test` | Exit 0; CTest 4/4, 50 behavioral suites |
| `python3 tools/dev.py build` | Exit 0; ShoenEditor Mac Development |
| UnrealEditor with `-ExecCmds=Automation RunTests Shoen.` and `-TestExit=Automation Test Queue Empty -unattended -NullRHI` | Exit 0; foundation 5/5, placement 4/4, inspection 3/3, profiling 4/4; zero test warnings/errors |

[Exact final Unreal argument array](../../artifacts/latency/final-unreal-command.json), [per-test results](../../artifacts/latency/final-unreal-summary.json), [logs](../../artifacts/latency/). Individual `python3 tools/dev.py editor-test --suite foundation`, `--suite placement`, `--suite inspection` and `--suite profiling` also passed earlier in this investigation. One simultaneous-editor rerun collided while moving the shared asset-registry cache file; foundation passed alone afterward and the final combined process passed all 16 tests. No game workaround was made for that test orchestration error.

New observer/fixture/collector/tooling checks were exercised against missing implementations before their passing runs. The final rendered datasets were collected after regression checks, using `run-captures.py --counts 1 10 100 --iterations 30 --label measured`; the 60 FPS control uses `--counts 10 --iterations 30 --cap 60 --label cap60`. Exact expanded commands accompany the data.

## Remaining limitations

- Backbuffer-ready is before GPU completion/presentation/scanout. Physical switch-to-Slate time is not exposed by the available project hooks. Hardware instrumentation would be needed for true input-to-photon timing.
- Development editor/game and an active macOS host introduce queueing and occasional outliers. This is not packaged, cross-platform or large-population performance acceptance.
- Software-generated replay does not prove physical cursor tracking or button alignment. Physical M2C verification remains pending as described above. The existing computer-control pointer limitation remains separate from the accepted game cursor behavior.
- Profiling has measurable, bounded overhead and a finite capture capacity. F6 stop drains rendering and exports outside sampled interactions. F12 synchronous logs should stay off during timing captures.
- Existing placeholder visuals/Canvas layout, immediate completed storehouses, synchronous explicit save/load and older startup ACL/audio/SM5 diagnostics remain. No new storage, production, roads, farming, construction simulation, growth, combat or final art was added.

## Recommended next task

After M2C is accepted: **one Small Storehouse construction-progress slice**, using the existing authoritative labor/resource ledger, with progress/completion in the inspector and pause/speed/save/load regression tests. Keep it to one building family and a minimal queue. This is a recommendation only; no implementation has begun.
