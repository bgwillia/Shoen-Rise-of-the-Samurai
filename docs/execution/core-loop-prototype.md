# Core-loop feasibility implementation plan

**Goal:** One playable 640-person settlement → equipment-limited mobilization → tactical battle → exact return and production consequences loop.

**Architecture:** Keep the existing engine-independent `World` population ledger and its service origins. New `domain::PrototypeState` contains prototype rules, elite gear, recovery dates, enemy ledger and formation combat state. Campaign time freezes during battle; tactical casualties are authoritative in that battle and reconcile through existing outcome/demobilization transactions on return. One portable worker owns all ledger and combat mutations. Unreal only presents the state and submits commands.

**Spec:** [User's integrated request](core-loop-prototype-request.md). This explicit feasibility-mode request supersedes prior milestone gates and elaborate skill approval/testing workflows. Use the accepted foundation branch as the base; preserve unrelated user files.

## Steps and progress

- [x] Preserve latency work at `8d69fa3`; keep F6/F12 opt-in and defer further latency work.
- [x] Agree `domain/Prototype.h` interfaces before parallel presentation/tooling work.
- [x] Portable prototype: `Prototype.cpp`, targeted `core/tests/test_prototype.cpp`, CMake. Test workforce/gear constraints, economy interruption, casualty conservation and origins, recovery, tactical casualties/routing and elite counters. Implement fixed 20 Hz formation combat, no soldier actors/AI.
- [x] Integration: `PrototypeSession.cpp`, subsystem, controller, game mode/camera. Keep legacy scenarios; add `prototype`. Bind recruitment, battle, orders, return, time acceleration and six existing-placement building controls. Read simple rules from `Content/Domain/Data/prototype.json`.
- [x] Presentation: prototype-specific branch of existing Canvas HUD and combat updates to existing instanced `FormationView`. Show occupations, production, equipment, army, casualties and postwar consequences. Use colors/labels/placeholders, no HUD redesign or final art.
- [x] Tooling: `run --scenario prototype`, `combat-benchmark --per-side {500,1000,2000}` with real rendered contact/ranged/casualty evidence.
- [x] Verification: targeted accounting tests, existing portable/tooling regression smoke, Mac Development build, one rendered loop demonstration, actual-combat timing at 500/1000/2000 per side.
- [x] Record measured results, simplifications and feasibility risks in STATUS; commit coherent playable prototype and stop.

## Decisions

- 320 farmers, 160 general labor, 40 smiths, 40 retainers, 80 dependents = 640. Ordinary formations default to 50, elite foot to 20; a smaller emergency smith levy demonstrates specialist cost.
- Daily food is a temporary continuous harvest abstraction in food person-days. Available workers drive production. Farms, houses, granary, smithy, manor and training area have simple capacity/eligibility functions. No per-resident simulation.
- Basic equipment uses the existing stock; better equipment has a separate prototype quantity and resource recipe. Recruitment requires equipment and an appropriate cohort, and returning healthy equipment is accounted for once.
- Formation combat uses contact/range/facing, morale/routing and fatigue. Enemy decisions use visible battlefield positions; no hidden campaign intelligence exists in this scenario. Open ground and simple separation are explicitly below final pathfinding scope.
- Prototype runtime is session-only. Existing versioned foundation/settlement saves remain available in their legacy scenarios. Save migration and battle persistence are deferred.
- Root owns all Unreal launches/builds and rendered benchmarking. Portable core, isolated HUD/formation presentation and tooling can proceed in parallel under the handoff's PLANS guidance.

## Discoveries

The prior foundation's individual service records and transactional outcome path are directly reusable. No new population owner or per-soldier AI is needed. Measured scale risks will be recorded after actual combat runs.

## Validation

`python3 -m unittest discover -s tools/tests -v`; `python3 tools/dev.py core-test`; `python3 tools/dev.py build`; targeted Unreal prototype smoke; `python3 tools/dev.py run --scenario prototype`; `python3 tools/dev.py combat-benchmark --per-side 500 --seconds 45`, then 1000 and 2000 serially. Keep builds/heavy tests out of rendered timing intervals.

## Handoff

Complete: rendered 240-vs-240 loop, exact postwar/recovery consequences, serial actual-combat measurements at 500/1,000/2,000 per side, final tooling/portable/Unreal tests and build. See STATUS.md for results and remaining limits. Stop after the prototype commit; no next slice begins automatically.
