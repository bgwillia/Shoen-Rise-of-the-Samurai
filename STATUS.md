# SHŌEN status

## Current task

**IN PROGRESS — core-loop feasibility prototype.** The user changed development strategy on 2026-09-15: build one integrated settlement → mobilization → actual battle → settlement consequence loop. No separate approval gate for each subsystem. [Authorized request](docs/execution/core-loop-prototype-request.md).

The accepted foundation remains M1 `44c33ca14de4669031e7e85ab7f157476f5a0a23`, M2A `f27632b05e124934779b3dc574b017851608859d`, and M2B `396bf5e0f2dd22222edf1a6cbf5bb6c873cfc954`.

## Latency investigation preserved, non-blocking

[Investigation and exact results](docs/execution/milestone-2c-status.md), [profiling procedure](docs/execution/milestone-2c-profiling.md), [raw evidence](artifacts/latency/measurements.md). Selection logic measured roughly 0.03–0.05 ms and replay-to-backbuffer roughly 16 ms; placement about 24 ms including a next-frame presentation update. These are software endpoints, not physical input-to-photon measurements. No speculative gameplay fix, engine patch, coordinate adjustment or default cap was added. F6 profiling and F12 cursor diagnostics remain opt-in. The requested final physical M2C capture was not completed and is no longer a blocking acceptance gate.

Preserved M2C regression results: tooling 43/43; portable CTest 4/4 (50 behavioral suites); Mac Development build passed; Unreal 16/16. These predate the integrated prototype and are not its verification.

## Integrated deliverable

A roughly 640-person placeholder settlement, daily worker-dependent production and consumption, equipment-limited recruitment, many small tactical formations with casualties/morale/fatigue, one elite formation, and exact return-home/recovery accounting. Measure rendered actual combat at 500, 1,000 and 2,000 soldiers per side. Keep tests focused on accounting and critical behavior, then build and demonstrate the loop in Unreal.

## Progress

- [x] Preserve prior profiling work and remove the obsolete blocking gate.
- [ ] Implement portable economy, recruitment, tactical battle and return/recovery.
- [ ] Integrate temporary HUD and rendered settlement/battle controls.
- [ ] Run targeted regressions/build, demonstrate rendered loop, measure combat scales.
- [ ] Record simplifications, risks, feasibility conclusion and next prototype.

## Limits

No final art, diplomacy, advanced city growth, roads, narratives, naval systems or production hardening. Slight UI latency remains known; revisit only if materially worse.
