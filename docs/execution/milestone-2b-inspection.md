# Milestone 2B — stable building selection and inspection

## Goal

Click each placed Small Storehouse, highlight it, and inspect its authoritative record and configured type. Preserve accepted M2A placement, M1 formations and all saved identity. Stop before M2C.

## Architecture

Tech stack: existing Unreal 5.8.2 C++ presentation and shared portable C++20 domain core; Canvas sidebar and passive instanced meshes. No engine patches, save-format changes, physics cooking or gameplay-value copies in the view for inspection.

- `domain/Inspection.h`: `EntityKind { None, Building }`, `EntitySelection { kind, id }`, const `ResolveBuilding(World, EntitySelection)` and `ResolveBuildingDefinition(BuildingCatalog, Building)`. UI owns selection; callers reacquire records instead of retaining pointers across world replacement.
- `SettlementView`: transient instance-to-ID map, ray intersection with the actual placeholder wall box and gable triangles, nearest visible hit. The index is used only to decode the current hit. Selection persists by ID. A separate passive footprint outline uses the authoritative frozen transform/dimensions.
- `FoundationPlayerController`: normal settlement click deprojects the existing cursor, asks the view for an ID, resolves it in the current World, and stores only the typed ID. Empty clicks, placement entry, reset/load and missing records clear safely. Same-world view recreation reapplies the same ID.
- `FoundationHUD`: compact read-only panel beneath the existing Build button. Separate instance identity/pose/state/placed footprint from definition name/type/configured footprint/cost. Missing definition displays unavailable, never another type's values.

## Spec

[Authorized request](milestone-2b-request.md). [Accepted M2A status](milestone-2a-status.md). Product/beta and architecture in the supplied handoff remain authoritative within this slice. Placement's slight human-observed latency remains unmeasured; no speculative fix. F12 stays off by default.

## Progress

- [x] Read current status, request, code, beta, architecture and guidance.
- [x] Create `codex/milestone-2b-inspection` from `f27632b05e124934779b3dc574b017851608859d`.
- [x] Baseline tooling/core regressions: 25/25 tooling, CTest 2/2 (exit 0).
- [x] Portable inspection red 0/7, green 7/7; complete CTest 3/3. Const resolvers implemented.
- [x] Unreal picking/highlight red evidence retained; exact body/roof rays, terrain occlusion and stable passive highlight implemented.
- [x] CLI inspection routing: three new tests failed first, all 28 tooling tests then passed.
- [x] Controller lifecycle tests and panel implemented; Unreal red run confirmed 3/3 tests fail against stubs, including lifecycle (15 expected errors). Final inspection 3/3 passes with zero test warnings/errors.
- [x] Final commands pass: tooling 28/28, CTest 3/3 (44 named suites), build exit 0, foundation 5/5, placement 4/4, inspection 3/3; zero final Unreal test warnings/errors.
- [x] Independent spec and code-quality reviews found no remaining material defect; direct include and mismatched-ID guard applied. See `artifacts/inspection/review.md`.
- [x] Rendered replay and human physical acceptance completed. User confirmed “All listed checks pass” for three-building selection/inspection/highlights, empty deselection, placement transitions, save/alter/load/reselection, readable panel and aligned clicks.
- [x] Update STATUS with exact evidence and limitations.
- [x] Finalize the verified state for the M2B acceptance commit; stop before M2C.

## Decisions

- Continue in the established project checkout on a dedicated branch, retaining Unreal paths/caches as for M2A. Preexisting user workbook/handoff/archive are untouched and excluded from staging.
- No snapshot expansion for UI selection. Reset/load deliberately clear it, including if a replacement world reuses an ID.
- Picking uses render geometry because ground-only footprint picking can miss a visible roof in perspective. No global cursor corrections or new engine collision dependencies.
- Picking scans building instances only on clicks. This is bounded simple behavior for the slice, not a 10,000-building performance claim.
- Ordinary settlement selection is separate from the existing formation multi-selection. The shared typed-ID concept is the extension point; no new entity systems yet.

## Discoveries

- `WorldGeneration` changes on load/reset; `ViewGeneration` also changes on placement. This existing distinction supports safe selection lifetime without save changes.
- Existing bodies/roofs are render-only and have no collision or ticks. Their exact placeholder geometry can be shared by rendering and picking.
- Existing Canvas sidebar targets 1280×720; inspection will reuse the available vertical area rather than redesign it.

## Validation

Final tooling 28/28 and portable CTest 3/3 pass (20 original, 17 placement, 7 inspection suites). Unreal build passes. First integration run found that the test fixture had not initialized actors, so the controller was absent from the World controller list. Installed `AActor::PostActorConstruction`/`AController::PostInitializeComponents` explain the failure; the fixture now uses `InitializeActorsForPlay` and asserts controller registration. No runtime workaround was added for this test setup issue. Final engine suites and the human physical checks now pass; see STATUS and the acceptance record.

Commands: `python3 -m unittest discover -s tools/tests -v`; `python3 tools/dev.py core-test`; `python3 tools/dev.py build`; `python3 tools/dev.py editor-test --suite foundation`; `python3 tools/dev.py editor-test --suite placement`; `python3 tools/dev.py editor-test --suite inspection`.

Focused invariants: three real placements have distinct IDs; selecting A cannot return B; lookup is const and safe for absent/removed/invalid identities; snapshot restores the exact type/transform; view reordering/recreation retains ID mapping and never changes the World; selection lifecycle rejects stale load/reset state; actual roof/body hits select, empty rays clear.

Retain red/green and final evidence under `artifacts/inspection/`. Headless test results are separate from rendering and human physical-input evidence. Back up any existing user settlement save before interactive acceptance.

## Handoff

M2B is accepted; final status/evidence is included in this acceptance commit. No M2C work authorized. Recommend an opt-in latency measurement pass next; no speculative fix or new gameplay system begun.
