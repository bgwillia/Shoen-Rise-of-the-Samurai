# Milestone 2 — persistent Small Storehouse placement

## Goal

Complete the user-authorized placement slice: preview, rotate, validate, atomically purchase, assign stable identity, render from authoritative state, save/load, and reject invalid/duplicate commands. Stop before Milestone 2B.

## Architecture

The persistent subsystem still owns `domain::World`. Add passive building records and settlement build areas to that world. Import the Small Storehouse and settlement fixture from JSON into plain C++ definitions; Unreal submits typed commands and rebuilds presentation from saved records. No actor owns building existence or resources.

Use a small authoritative triangulated height field for the fixture: mostly flat with a visible sloped test strip. Render those same vertices. This keeps terrain validation and preview ray intersection deterministic without trusting a separate collision scene. Building rectangles rotate freely in integer degrees; UI rotation steps come from definition data. SAT rejects overlapping oriented footprints; exact edge touching is allowed within a documented numeric tolerance. Terrain checks clip the footprint against height-field triangles so an interior ridge cannot pass a corners-only test.

## Spec

[User request](milestone-2-request.md), accepted source `44c33ca14de4669031e7e85ab7f157476f5a0a23`, beta specification, architecture A01–A10, and handoff `docs/plans/02_CITY_ECONOMY.md`. User's narrow scope overrides later systems in that plan.

## Decisions

- New branch `codex/milestone-2-placement` starts at the accepted M1 commit. Keep the existing checkout/Unreal project path and preserved untracked handoff available, as in the accepted execution setup; no additional linked worktree is needed.
- The explicit implementation request supplies the approved design and scope. Routine implementation choices do not require another approval ceremony.
- Small Storehouse: 800×600 cm, placeholder height 450 cm, 20 timber + 5 treasury, 15-degree UI rotation steps. Dimensions, costs, and terrain tolerance are content data.
- Settlement fixture: 200 timber, 100 treasury, existing finite 200-person ledger unchanged. A bounded height field provides flat ground plus a sloped invalid test strip; no roads or economy simulation.
- Snapshot writer becomes v2, retaining the existing magic/header/checksum and the v1 payload prefix. Reader accepts v1 (empty buildings/build areas) and v2; a real v1 fixture produced with the accepted codec must pass migration tests. Old executables cannot read v2; use separate settlement save filename and existing backup behavior.
- Each building stores definition ID/version, stable ID, settlement/district, integer-centimeter transform, integer-degree yaw, frozen dimensions/terrain limits, completed construction state, and placement transaction ID. Definition changes cannot resize existing buildings on reload.
- Preview never spends or allocates IDs. Confirmation carries one transaction ID; duplicate accepted payload returns the same building without spending, while conflicting reuse fails. Failed placement leaves the entire world, counters, and transaction ledger unchanged.
- Geometry and economy checks return typed reason codes. Candidate-world commit protects multi-resource deduction and registry insertion as one operation.
- Runtime building presentation is batched and passive. Only placement preview updates while placement mode is active. Existing camera, formation lab, F12, and clock behavior remain.
- Existing camera keys Q/E and middle drag retain their meanings. Building mode uses B to choose/toggle Small Storehouse, brackets to rotate, left click or Enter to confirm, Esc/right click to cancel. HUD provides equivalent temporary placement controls. F5/F9 retain save/load.

## Tasks and Progress

### 1. Core buildings and snapshot compatibility

Files: new `BuildingTypes.h`, `Buildings.h`, `Buildings.cpp`, `core/tests/test_buildings.cpp`; extend `World.h`, `World.cpp`, `SaveCodec.h/.cpp`, `core/CMakeLists.txt`; add v1 save fixture under `core/tests/fixtures/`.

- [x] Capture a real v1 save from accepted source before modifying codec.
- [x] Define the plain data/API contract below, write behavioral tests, and retain expected failures.
- [x] Implement success/exact cost, each insufficient resource independently, rotated overlap/boundary, terrain interior variation/slope, bad content/coordinates/references, capacity/counter limits, duplicate/conflicting transaction, stable global IDs, unchanged population, and deterministic commands.
- [x] Test v1 migration, v2 exact round trip, malformed added records, and duplicate replay after reload.
- [x] Run old 20 core suites plus new placement suites.

### 2. Content, subsystem and passive rendered view

Files: `game/Content/Domain/Data/buildings.json`, `settlement_fixture.json`; new Unreal content reader and `SettlementView`; extend subsystem and game mode.

- [x] Import JSON with bounded numeric/string/count validation; fail with an actionable message rather than silently substitute missing definitions.
- [x] Implement a new settlement fixture without replacing existing foundation/scale fixtures; expose `--scenario settlement` and a temporary in-game fixture button/shortcut.
- [x] Create terrain mesh from the same authoritative grid and instanced placeholder building bodies/roofs from simulation records. No building ticks.
- [x] Recreate/deleting presentation must leave world IDs/resources unchanged; test it through Unreal automation.
- [x] Persist/load world only through the existing snapshot path; rebuild terrain/buildings on view generation. v1 load preserves its ledger and reports no settlement build area.

### 3. Placement input and temporary HUD

Files: controller/HUD and dedicated placement helpers; minimal camera framing addition if needed.

- [x] Deproject the native viewport cursor against authoritative terrain, with flat-plane fallback outside the build area to display boundary rejection.
- [x] Preview follows cursor, uses configured rotation increments, shows footprint and valid/invalid color, definition/cost/available stocks/reason.
- [x] UI consumes its own clicks. Placement mode suppresses formation click/order handling but preserves camera controls and F12. Cancel releases preview without a command.
- [x] Confirm revalidates current state, reports stable ID, and blocks duplicate press/release processing. Load/reset cancels stale preview transactions.
- [x] No changes to unrelated M1 stable systems.

### 4. Tooling, tests, rendered acceptance and commit

Files: tools/dev.py/tests, new `Shoen.Placement` automation suite, STATUS/README, evidence.

- [x] Tooling tests cover settlement scenario and exact automation suite selection; retain M1 defaults.
- [x] Run `python3 -m unittest discover -s tools/tests -v`, `python3 tools/dev.py core-test`, `python3 tools/dev.py build`, `python3 tools/dev.py editor-test --suite foundation`, and `python3 tools/dev.py editor-test --suite placement`.
- [x] Launch `python3 tools/dev.py run --scenario settlement` and exercise preview, rotation, placement/cost, overlap, boundary, slope, cancel, save/alter/load and identical restored IDs/transforms/resources. Distinguish tool-driven from human physical evidence; never claim automated tests prove rendering.
- [x] Independent review of spec coverage and implementation. Fix demonstrated defects, rerun affected tests.
- [x] Update STATUS with M2 first-slice acceptance, exact evidence, v1/v2 policy, placeholders/limitations and one M2B recommendation; commit verified state only.

## Core API contract

Definitions in `domain/BuildingTypes.h`: `BuildingDefinition` (string id/display_name, uint32 version; int32 width_cm/depth_cm/height_cm/rotation_step_degrees/max_height_variation_cm/max_slope_permille; int64 timber_cost/treasury_cost); `BuildArea` (uint64 settlement_id; int32 origin_x_cm/origin_y_cm/cell_size_cm; uint32 columns/rows; vector<int32> heights_cm); `Building` (uint64 id/settlement_id/district_id/placement_transaction_id; string definition_id; uint32 definition_version; int32 x_cm/y_cm/z_cm/yaw_degrees/width_cm/depth_cm/height_cm/max_height_variation_cm/max_slope_permille; ConstructionState state=Completed).

`World` gains `map<EntityId,Building> buildings` and `map<EntityId,BuildArea> build_areas` (areas keyed by their settlement ID, not a new entity identity). `BuildingCatalog` is `map<string,BuildingDefinition>` and belongs to loaded scenario content, not the saved world.

`PlacementCommand`: transaction_id, definition_id, settlement_id, district_id, x_cm, y_cm, yaw_degrees. `PlacementResult`: bool ok, PlacementCode code, EntityId building_id, int32 ground_z_cm. Codes include Valid, AlreadyApplied, UnknownDefinition, InvalidCommand, InvalidWorld, NoBuildArea, OverlapsBuilding, OutsideBuildArea, TerrainTooSteep, InsufficientResources, TransactionConflict, CapacityExceeded.

Exports in `Buildings.h`: `ValidateBuildingCatalog`, `ValidateBuildingState` returning existing Result; `ValidatePlacementGeometry`, `EvaluatePlacement`, `PlaceBuilding` returning PlacementResult; `PlacementReason(PlacementCode)`; `FootprintCorners(x_cm,y_cm,width_cm,depth_cm,yaw_degrees)` returning four Point2 values; `TerrainHeightAt(BuildArea,double x,double y)` returning double (NaN outside); `RaycastBuildArea(BuildArea,Point3 origin,Point3 direction,Point3& hit)` returning bool. All share one terrain triangulation convention.

## Discoveries

M1 is accepted with native pointer alignment confirmed by the user. The computer-control marker can still differ from the actual pointer. Do not add input scaling to accommodate that tool behavior. The current snapshot v1 has a 28-byte header and strict exact payload consumption, so appended fields require a real version branch.

## Validation

Baseline and later red/green logs belong in `artifacts/placement/`; raw Unreal logs remain ignored. The final report lists actual command exits, report files, rendered behavior and remaining limitations. No M2B implementation.

## Handoff

ACCEPTED Milestone 2A placement/save slice, committed on `codex/milestone-2-placement`. Tooling25/25, core37 suites (CTest2/2), Unreal foundation5/5 and placement4/4, Mac Development build, and final rendered save/alter/load all pass. The user subsequently physically accepted Milestone 2A, including HUD text, continuous preview movement, HUD/building controls and the placement/save loop. Slight UI response delay is a known, unmeasured follow-up with no observed missed input or incorrect behavior. No Milestone 2B work.

### Verification progress

- Baseline: tooling 21/21 and original core CTest 1/1 passed before edits.
- Retained failing tests precede core geometry/transaction/save implementation and passive Unreal view implementation.
- Independent core review found a saved-terrain rejection gap. Frozen original terrain tolerances and whole-footprint validation fix it; 17 placement suites plus 20 original suites pass. Current placement ASan+UBSan run passes.
- Final tooling: 25/25. Final Unreal content, transaction/save, input lifecycle and passive recreation tests pass after removal of the failed HUD experiment. Final commands/reports are listed in STATUS.md.
- Rendered loop: choose/rotate, Enter and native-position click placement, exact resource debit, overlap/boundary/slope rejection, two-building save, third-building alteration and F9 restoration. Paused save bytes match exactly after reload and invalid attempts. These specific historical tool-driven steps are separate from the user's subsequent physical acceptance.
- Intermittent Canvas glyph corruption reproduced with placed instances. Initial draw-command-merging workaround failed extended validation and was removed. Fresh Metal binding-reset/serialization diagnostics also reproduced it. A temporary Slate overlay also reproduced glyph loss and was removed. No engine/global CVar/input correction or speculative batch-backend change remains. See renderer-isolation.md.

Final evidence is under `artifacts/placement/`. Scene captures retain the intermittent glyph symptom; the user subsequently confirmed correct physical text and explicitly accepted the slice. The acceptance-only update adds no runtime code or speculative latency fix; see milestone-2a-latency.md.
