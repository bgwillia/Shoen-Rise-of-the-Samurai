# SHŌEN status

## Current milestone

**Milestone 2 — settlement foundation, first Small Storehouse placement slice.** The complete placement/save loop is implemented and functionally verified. All required regressions and the final rendered functional replay pass; intermittent captured HUD glyph loss remains a visual acceptance limitation. The coherent slice is committed on `codex/milestone-2-placement`. **Milestone 2B has not begun.**

Milestone 1 remains accepted at `44c33ca14de4669031e7e85ab7f157476f5a0a23`. Its complete physical-input acceptance, root-cause investigation, tests and performance evidence are preserved in [Milestone 1 status](docs/execution/milestone-1-status.md). The prior Mac physical-input issue remains resolved. No engine patches or pointer coordinate corrections were added.

Scope and design: [user request](docs/execution/milestone-2-request.md), [execution plan](docs/execution/milestone-2-placement.md).

## Implemented

- One data-defined **Small Storehouse**: 8×6 m footprint, 4.5 m placeholder height, 20 timber + 5 treasury, 15-degree rotation steps, 20 cm maximum height variation and 100-permille maximum slope. Definitions and fixture live in [content data](game/Content/Domain/Data/buildings.json).
- New settlement fixture on the existing Foundation map: 200 timber, 100 treasury and the existing 200 workers; a saved triangulated build area with flat ground and a deliberately invalid raised strip. No population is created by placement.
- Native viewport cursor raycasts against the same authoritative triangles used for rendering. Green/red body and footprint preview, readable reason, selected building/cost and current resources. Preview freezes over the HUD. B chooses placement; brackets rotate; left click/Enter confirm; Esc/right click cancel. Equivalent HUD controls; N starts a new fixture. Existing camera, F12, clock, formation lab and shortcuts remain.
- `domain::World` owns building records and terrain. Stable global ID, definition/version, settlement/district, integer-centimeter position, integer-degree yaw, frozen dimensions/terrain tolerances, completed state and placement transaction ID persist. Unreal presents batched wall/roof instances with no per-building actor Tick.
- Separate deterministic oriented-footprint/boundary/terrain and resource validation. Terrain clipping checks interior ridges as well as corners. Edge contact within 1e-6 cm is allowed. Typed reason codes drive UI; no string parsing drives rules.
- Candidate-world transaction commits one building and both costs together. Failures preserve the entire world, including ID/transaction counters and revision. A matching accepted retry returns the same ID without spending; conflicting reuse rejects. Same-frame UI confirmation is guarded, and reset/load invalidate stale gestures.
- Original Canvas HUD and explicit building ISM batches are retained. Extended rendering checks disproved the attempted command-merging and Slate text workarounds; neither remains. Intermittent missing HUD glyph sections in captures are documented without claiming a fix or an established engine cause. [Renderer investigation](artifacts/placement/renderer-isolation.md).
- Passive view recreation preserves the entire simulation and stable transforms. Terrain meshes are reused while unchanged; render-only meshes do not cook physics. No storage, production, workers or housing systems were added.

## Manual acceptance

Actual Metal-rendered 1280×720 game, launched with `python3 tools/dev.py run --scenario settlement`. The complete placement/save loop was exercised through the rendered interface. Functional acceptance is verified; text-presentation acceptance remains qualified by the captured glyph issue below.

- B selects Small Storehouse and enters placement with a green body/footprint at the native pointer's ground intersection.
- Bracket rotation changes facing 0→15 degrees and rotates the rendered footprint/roof.
- Enter places ID 5 at (1344, 2647) cm, yaw 15°; stocks 200/100→180/95. Workers stay 200.
- Overlap turns the preview red; repeated Enter rejects without spending or adding buildings.
- Wheel zoom moves the ray/ground intersection while the placed building stays fixed. A native-position mouse press places ID 6 at (551, 1957) cm, yaw 15°; stocks become 160/90.
- Right-click cancels without an order or resource debit. F5 saves two buildings.
- B, wheel zoom and Enter add ID 7 at (−268, 1245) cm, yaw 0°; stocks become 140/85. F9 removes that unsaved third building and restores both saved buildings and 160/90.
- F5 after reload produces a byte-identical 1,194-byte snapshot, including IDs, transforms, resources and paused clock. See [save comparison](artifacts/placement/manual-save-comparison.txt).
- Zoom outside the boundary produces a red reason and rejected Enter. Q camera rotation moves the preview onto the raised strip; excessive slope produces a red reason and rejected Enter. Esc cancels. F5 afterward is still byte-identical to the saved state.
- F12 displays matching native/viewport cursor measurements; toggled off afterward.

The final ordinary-launch replay again verified native-position mouse placement, overlap rejection, cancellation and separately observed save/alter/load. The final resave remains byte-identical. [Full manual record](artifacts/placement/manual-acceptance.md), [final layout](artifacts/placement/final-restored-layout.png).

These are tool-driven actions in the visible native game, not human observations. Continuous physical pointer movement and direct new HUD-button clicks have no new human attestation. The computer-control pointer-movement limitation remains; M1's human physical-input acceptance is unchanged. No coordinate correction was introduced.

## Automated verification

Host: Unreal 5.8.2 / CL 56702186, macOS 26.6.2, Xcode 26.6.0, Apple Clang 21.0.0; Apple M1 Max (10 CPU / 32 GPU cores), 32 GB RAM. Editor `-game`, Metal SM5, 1280×720; content schema 1 and Small Storehouse definition version 1. Source starts from accepted M1 commit above on `codex/milestone-2-placement`.

Final regression results after the saved-terrain fix and removal of ineffective renderer experiments:

| Exact command | Result |
|---|---|
| `python3 -m unittest discover -s tools/tests -v` | Exit 0; 25/25 passed |
| `python3 tools/dev.py core-test` | Exit 0; CTest 2/2, 20 original + 17 placement suites |
| `python3 tools/dev.py build` | Exit 0; ShoenEditor Mac Development succeeded |
| `python3 tools/dev.py editor-test --suite foundation` | Exit 0; 5/5 passed, zero test warnings/errors |
| `python3 tools/dev.py editor-test --suite placement` | Exit 0; 4/4 passed, zero test warnings/errors |

The current 17 placement suites also pass under ASan+UBSan; the earlier full sanitizer run predates the final frozen-terrain fields. Red/green logs and final results are retained in [placement evidence](artifacts/placement/). Unreal automation covers actual content parsing/rejection, transaction+file save/load, input cancellation/duplicate/replacement-world handling and passive view recreation. Headless automation is not rendering evidence.

Independent integration review found no remaining important UI/state-lifecycle defect. Core review found a saved-terrain validation gap. A failing regression reproduced it; frozen per-building terrain limits now reject corrupted steep-ground placements while preserving valid buildings after stricter tuning. Core 17/17 placement suites and current placement sanitizers pass.

## Save compatibility

**Writer v2; reader v1 and v2.** The existing 28-byte header, magic, checksum and v1 payload prefix remain. V2 appends bounded build-area grids and building records, including frozen visual dimensions and terrain limits. Exact IDs, position/yaw, completed state, costs already paid, shared transaction ledger, resources, population, clock/RNG and formation state round-trip.

A real 4,971-byte v1 snapshot generated before codec edits is retained as [migration fixture](core/tests/fixtures/milestone1-v1.shoen), SHA-256 `1f4fb37fe2d0de0147ad09e467cb301b6352c1ea00105c0e83df8ab5d96f326a`. V1 loads preserve its world and produce empty buildings/build areas; migration does not reset resources or invent a fixture. The original M1 executable cannot read v2; retain original v1 saves for that executable.

Foundation and settlement use separate `Foundation.sav` and `Settlement.sav` slots under `game/Saved/SaveGames/`, with temporary replacement and previous `.bak`. Missing/too-new building definitions or invalid snapshots reject before replacing the live world. Catalog validation is independent of the new-fixture file; saved terrain/resources remain authoritative. The checksum detects accidental corruption, not malicious tampering.

## Placeholder

All buildings, terrain, colors and Canvas controls are temporary technical presentation. The storehouse has no storage capacity or production. Construction completes immediately; only a completed-state contract exists. No final Japanese art, audio, animation, housing simulation, farming, smithing, organic growth, roads, workers, pathfinding, AI, combat or diplomacy was implemented. User-supplied design files and asset workbook remain untouched.

## Known limitations

- Automated captures intermittently lose sections of HUD letters. Physical text stability has no new human attestation; the root cause is not established. The issue reproduced through Canvas and a temporary Slate experiment, even with instance drawing hidden. Ineffective workarounds were removed. This is an unresolved visual acceptance limitation.
- Continuous physical pointer movement and direct HUD-button clicks have no new human attestation for this slice. Rendered keyboard controls and a native-position mouse press were exercised; the M1 physical-input acceptance remains valid.
- Multiple save/load shortcuts arriving within one game update use the existing fixed polling order (F5 before F9). Acceptance separates each operation and observes its result; a rapid automated batch is recorded as rejected evidence.
- Only the Mac editor/game workflow is verified. Standalone packaging and other platforms are untested; JSON staging is configured but not packaged acceptance.
- The HUD targets at least 1280×720. A single fixture and building family are exposed. New-fixture controls intentionally replace the unsaved test world.
- Terrain is a bounded static height grid; no arbitrary landscape/navmesh, terrain editing or obstruction system. Buildings have no selection/edit/demolition workflow in this slice.
- Saved-building validation checks pairs and terrain raycasts scan triangles. Passive instancing avoids ordinary-building ticks, but this does not certify 10,000-building performance. Spatial indexing/incremental validation needs measurement before dense settlements.
- Snapshot cap 16 MiB; 10,000 buildings, 64 build areas and 65,536 vertices per area are safety bounds, not performance promises. Determinism is tested on this build/platform, not across all floating-point implementations.
- Existing engine startup diagnostics about optional ACL compression assets/audio may appear; final test-result warnings are tracked separately. No animation/audio systems were added.

## Next recommended task

After the remaining text-presentation question is settled: **Milestone 2B — select an existing building and inspect its authoritative ID, type, transform, completed state and placement transaction, including after load.** This gives a small useful interaction foundation before demolition, construction phases or economy. Recommendation only; no Milestone 2B implementation.
