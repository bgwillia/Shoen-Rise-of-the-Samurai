# Prototype B implementation plan

## Goal
Evaluate many small formations on constrained terrain, then carry first-war losses through recovery and a second mobilization from the same settlement.

## Architecture
Use the existing engine-independent PrototypeState and population ledger. Add authored terrain and transient navigation state at formation level; no engine patches, per-soldier pathfinding or save migration. Fixed river geometry and two crossings permit deterministic corridor routes. Friendly movement uses reserved destinations, separation checks and stable traffic priority. Forest slows; hill improves defense; existing facing damage becomes measurable. Presentation consumes the same terrain coordinates. Tactical enemies guard their bank and react to nearby enemies/flanking.

## Spec
[Complete user specification](prototype-b-request.md). Ordinary formations 80–150, elite smaller. Target 12–20 polearm, 6–10 bow, 2–4 elite and roughly 2,000 per side. Include narrow bridge, distant ford, open ground, woods and a defensive hill. Group orders preserve approximate ordering and facing; category selection is optional if cheap. Population/accounting ownership and legacy scenarios remain intact.

## Progress
- [x] Preserve accepted A evidence and create B branch.
- [x] Core: authored larger settlement, real mixed-army recruitment, terrain routing, separation, enemy roles and targeted navigation/accounting tests.
- [x] Integration: battlefield placeholder geometry, ordinary controls for muster/line/crossing choice, selection details with quiet world labels.
- [x] Evidence: crossing stress, first/second war and elite losses, actual rendered 1,000/2,000 combat timing.
- [x] Regressions, review, STATUS/README update and coherent commit.

## Decisions
Use the fixed two-crossing topology rather than generalized navmesh or engine navigation. Keep Prototype A accessible and add the terrain scenario. Reserve final spaces and serialize narrow traffic; explicitly report unresolved queue/pathing failures. UI/render work may be delegated under the handoff PLANS after agreeing simulation interfaces. One owner edits core population/combat, root owns Unreal processes. No heavy parallel work during rendered measurements.

## Discoveries
A measured friendly overlap count reached 103 pairs at 2,000 per side; computation was cheap. Current labels overlap HUD and need scale-appropriate simplification. Synthetic mouse/modifier limitations are distinct from accepted human physical input.

## Validation
Targeted core tests: terrain boundary/crossing constraints, friendly overlap and crossing progress, deterministic repeated orders, preserved origins/conservation and second-war/elite depletion. Re-run tooling unit tests, core-test, build, all Shoen Unreal automation. Actual rendered terrain combat at ~1,000 and ~2,000 per side: frame median/p95, simulation and navigation costs, queue/overlap/stuck counts. Demonstrate return/recovery/remuster without reset. Record failures, not only successes.

## Handoff
Stop after playable Prototype B and commit it. Report feel, pathing/UI problems, combat performance, second-war effects, feasibility risks and recommended C. Do not begin C automatically.

### Final integration findings

Tooling 51/51, CTest 6/6 and Unreal 18/18 pass. The final Development build succeeds. The 30-formation one-way bridge stress clears at 209.1 simulated seconds with zero overlap and no final stuck formations at its 360-second budget.

Review fixes use shared hill height for box selection, consume the opaque battle-status panel, average facing circularly and preserve committed movement legs when retargeting. Queued troops recover fatigue. Benchmark setup explicitly splits main/elite groups so ford orders cannot overwrite the entire bridge order. The optional 500-per-side terrain benchmark is rejected; accepted A's 500-person benchmark remains available.

Actual play exposed an opposing-traffic ford deadlock that the one-way bridge test did not cover. Focused failing tests established two causes: a one-row crossing and overlapping routed exit destinations. The final model widens the ford into three grid rows, assigns opposing directional lanes and reserves unique retreat exits. All 12 opposing test formations now cross. The primary bridge remains one lane. Route-preserving line rotation and a traversable bow standoff point complete the command fixes.

The final ordinary rendered session demonstrates battle, elite losses, return, seven days of recovery, a smaller second muster and second deployment from the same 6,000-person ledger. First army 2,320/120 elite; second army 2,266/66 elite after 482 total deaths. While remobilized, food output falls from 4,800 to 3,636/day and gear output from 20 to 19/day. The full before/after failure and correction evidence is in `artifacts/terrain/rendered-demo.md`.

The remaining weaknesses are congestion/pacing and command intent, not a measured simulation compute ceiling. Formation grid snapping, active battle queues, an unsupported elite flank's heavy losses and frame outliers must remain visible in the handoff. Final rendered benchmarks use the corrected build, one Unreal process at a time, after ordinary gameplay exits.

Final rendered captures both exited 0: 1,000 per side at 109.4 median FPS / 10.002ms frame p95; 2,000 per side at 108.6 FPS / 10.083ms p95. Navigation p95 was 0.0428 / 0.1131ms, peak friendly overlap zero at both sizes. Complete methodology and remaining queue/frame limits: `artifacts/terrain/measurements.md`. The deliverable and limitations are consolidated in STATUS.md; commit this B state and stop without beginning C.
