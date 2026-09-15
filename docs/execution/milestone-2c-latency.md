> Historical M2C scope: superseded on 2026-09-15 by [feasibility prototype mode](core-loop-prototype-request.md). Preserve results; physical latency acceptance is no longer blocking.

# Milestone 2C — interaction latency investigation

## Goal

Measure selection, placement and preview latency through the available input, game and rendering pipeline. Identify a cause or ordinary frame-boundary behavior; change gameplay behavior only when evidence justifies it. Commit verified state and stop before another gameplay slice.

## Architecture

Tech stack: current UE 5.8.2 C++/Metal game, portable shared core, Python report tooling. Add one opt-in bounded profiler with `FPlatformTime::Cycles64` timestamps and game/render frame correlation. Normal play remains quiet; no per-stage file/console logging. Export on capture stop, outside the sampled interval.

- Slate `IInputProcessor` passively observes mouse/key events (always returns false). Use `FInputEvent::GetEventTimestamp()` for Slate-event construction, capture preprocessor and controller receipt separately. This timestamp is not physical button activation or the earlier macOS deferred-event timestamp.
- Scoped action records collect pick/ID/record/state/highlight, validation/commit/resources/rebuild, preview and HUD stages. Optional plain-C++ placement observer callbacks expose validation/commit boundaries without Unreal dependencies, rule changes or clock work when disabled.
- Applied visual tokens use separate selection/mode/rotation/preview/building/message channels. Scene view extension snapshots tokens with the actual `FSceneViewFamily::FrameCounter`; HUD draw snapshots its tokens. Join only matching scene/HUD/frame/window data at `OnBackBufferReadyToPresent` on the render thread. Superseded/unmatched states are not counted as visible.
- The endpoint is **backbuffer ready on the render thread**, not screen scan-out. Optional nonblocking GPU fences provide a completion observation interval/upper bound, not exact GPU finish or display. Never block/flush per measured sample; an end-of-capture flush/export is outside sampling.
- Deterministic development fixtures use real placement transactions for 1/10/100 buildings on identical terrain/camera, with equal post-seed stocks and a free placement strip. A transient session owns a saved in-memory baseline, restores between successful trials, and prevents fixture writes into normal save slots. No content/save-format expansion.
- A serial in-game replay drives existing action methods for repeatable logic/render comparisons, explicitly labelled `replay` with no invented physical/Slate input interval. A separate physical capture measures actual Slate/controller receipt and normal input polling. Never merge those origins into one latency claim.

## Spec

[Full authorized request](milestone-2c-request.md). [Accepted M2B status](milestone-2b-status.md). [Earlier latency boundaries](milestone-2a-latency.md). Existing architecture/product/beta guidance applies; this is measurement only until a specific hypothesis is supported.

## Progress

- [x] Read request/status, inspect current input/render/core paths and installed engine hooks.
- [x] Create `codex/milestone-2c-latency` from accepted `396bf5e0f2dd22222edf1a6cbf5bb6c873cfc954` in the established checkout.
- [x] Run preliminary portable-core probe, retaining source and 1,500 raw observations.
- [x] Implement bounded collector, input/render hooks and stage instrumentation with focused tests.
- [x] Implement isolated development fixtures and opt-in repeated replay; test no save leakage and state integrity.
- [x] Add validated report analysis and profile/test command routing with failing tests first.
- [x] Run full regressions/build and rendered 1/10/100 captures, plus instrumentation-overhead comparison.
- [ ] Collect physical-input capture and validate stage/frame correspondence and normal interactions.
- [x] Analyze medians/worst values, identify the dominant measured interval and make only justified minimal corrections.
- [ ] Regress any correction, independently review, update STATUS with evidence/limits, commit and stop.

## Decisions

- Project-only hooks; no engine patches or speculative timing/CVar changes.
- Capture off by default, distinct from noisy F12 cursor debugging. F6 starts/stops manual profiling; named debug commands/options may launch repeatable fixtures/replay. No permanent overlay.
- Use at least 30 repetitions per action/count after warmup, with exact pre-action building counts. A-to-B switching is unavailable at count 1. Record sample count, median, p95 and worst without claiming statistical certainty. Keep frame rate/viewport/source cohorts separate.
- Measure ordinary uncapped editor/game first; a controlled frame-cap experiment may test a frame-boundary hypothesis but is not a shipping configuration change.
- Preserve all normal saves and restore the prior World after a development session. Synthetic replay and human capture remain separately labelled.

## Discoveries

- Input is polled each PlayerTick; preview is frame-driven and does not wait for campaign days. No interaction throttle/timer/async/file operation found. Selection only updates the cyan outline, not all buildings.
- Successful placement validates the entire World three times inside the core, and refreshes preview afterward; successful view generation triggers a full building-instance rebuild on GameMode Tick. These are candidates, not diagnosed defects.
- Portable probe: same flat 117-vertex area, 10 warmups and 100 samples per stage/count. Placement median/max: 1 building 0.023/0.124 ms; 10 buildings 0.117/0.355 ms; 100 buildings 1.649/2.929 ms. Core validation dominates this measured core interval at 100, but does not establish physical UI latency.
- Installed Slate event timestamps are monotonic construction times after macOS deferred dispatch. `OnSlateWindowRendered` is only a GT enqueue notification and is unsuitable as completion. `OnBackBufferReadyToPresent` runs on RT before presentation. No public physical-display callback was found.

## Validation

Required commands: `python3 -m unittest discover -s tools/tests -v`; `python3 tools/dev.py core-test`; `python3 tools/dev.py build`; `python3 tools/dev.py editor-test --suite foundation`; `python3 tools/dev.py editor-test --suite placement`; `python3 tools/dev.py editor-test --suite inspection`. Add profiler/fixture automation where meaningful. Retain raw captures and curated results under `artifacts/latency/`; keep bulky engine startup logs under ignored `artifacts/local/`.

Initial probe command: `clang++ -std=c++20 -O2 -DNDEBUG -I game/Source/DomainCore/Public artifacts/latency/core-probe.cpp game/Source/DomainCore/Private/sim/World.cpp game/Source/DomainCore/Private/sim/Buildings.cpp game/Source/DomainCore/Private/sim/SaveCodec.cpp game/Source/DomainCore/Private/sim/Battle.cpp game/Source/DomainCore/Private/sim/Inspection.cpp -o /tmp/shoen-placement-latency-probe`; then `/tmp/shoen-placement-latency-probe`. Exit 0, actual first-run source lived in /tmp and is copied unchanged into evidence.

## Handoff

M2C in progress. No gameplay behavior fix is justified yet. No roads, farming, construction simulation, growth, art or other new gameplay systems authorized.

## Verification progress

- Final tooling: 43/43; core: CTest4/4 (50 behavioral suites); Unreal foundation5/5, placement4/4, inspection3/3 and profiling4/4; Mac Development build succeeds.
- Collector/fixture tests failed against intentional stubs before implementation. Review corrected stale tokens, message replacement, no-op selection, missing input-drop accounting and unevaluated-preview classification. These are profiler corrections, not latency optimizations.
- One concurrent automation rerun hit a shared asset-registry temporary-file move error. Foundation passed alone afterward. Future Unreal checks/captures run serially; no engine or game workaround was applied.
- Preliminary rendered runs: 30 cycles each at1/10/100, actual1280×720, ~8.33ms frame interval. Selection logic medians0.029/0.031/0.048ms; total to matchingbackbuffer15.61/15.53/15.71ms. Placement logic0.067/0.122/0.899ms; total23.85/23.99/24.05ms, presentation appliedonegameframe later. Final captures repeat this after correcting the preview-cache label.
- Detailed operator procedure and limitations: [profiling guide](milestone-2c-profiling.md). Physical input capture and profiling overhead/control runs remain pending.

## Pending human capture — 2026-09-15 11:46 UTC

Final code is built and all 43 tooling tests, CTest4/4 and 16 Unreal tests pass. Definitive rendered captures are `artifacts/latency/measured-{1,10,100}.json`; all 870 requested visual changes are observed, with no dropped/pending records. `cap60-10.json` confirms that a 60 FPS cap reduces queued software rendering delay without establishing physical input-to-screen benefit. No gameplay timing/default changes were made. Idle gating reduces unnecessary profiler render commands; the final 100-building median wall frame is 8.30 ms versus 8.33 ms with capture disabled. STATUS contains the measured replay tables and boundaries.

The ordinary rendered game is open, paused, with the existing five-building save loaded. The user was asked to press F6, perform physical selection/UI/placement/save-load checks, press F6 again and report the outcome. No physical capture export has appeared under `game/Saved/Profiling/` yet. Do not mark M2C accepted, reuse M2B physical evidence as new evidence, or claim input-receipt latency from replay. On reply, inspect the actual export, validate/analyze it, record the human outcome, update STATUS/measurements/manifest, commit the verified state and stop. Branch HEAD remains accepted M2B `396bf5e0f2dd22222edf1a6cbf5bb6c873cfc954`; no M2C commit has been made yet. The unrelated untracked workbook and handoff package remain outside this work.
