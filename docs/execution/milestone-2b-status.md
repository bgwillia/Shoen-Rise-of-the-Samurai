# SHŌEN status

## Current milestone

**Milestone 2B — stable building selection and inspection: ACCEPTED.** On 2026-09-15 the user confirmed that all requested physical checks passed in the actual Unreal game. Automated regressions, the build and rendered verification also pass. No M2C work has begun.

Source starts from accepted M2A commit `f27632b05e124934779b3dc574b017851608859d` on `codex/milestone-2b-inspection`. This acceptance commit records the verified M2B state. [Authorized request](../../docs/execution/milestone-2b-request.md), [execution plan](../../docs/execution/milestone-2b-inspection.md).

Milestone 1 remains accepted at `44c33ca14de4669031e7e85ab7f157476f5a0a23`; its physical input issue remains resolved. Milestone 2A remains accepted, including human verification of HUD, pointer-following preview, placement/rotation/validation/cancellation/save/load. Complete prior evidence is preserved in [M1 status](../../docs/execution/milestone-1-status.md) and [M2A status](../../docs/execution/milestone-2a-status.md).

## Architecture and behavior added

- **Typed selection identity:** `domain::EntitySelection` contains only entity kind and stable ID. Const resolvers look up the exact current World record and exact compatible definition. Missing, zero, wrong-kind or mismatched IDs fail safely. Borrowed records are reacquired for each use, never retained through world replacement.
- **Visible building → ID → World → inspector:** the passive settlement view decodes the current body/roof instance index through a transient ID table. Picking intersects the actual transformed wall box and shared gable triangles, chooses the nearest positive hit and checks nearer saved terrain. Persistent selection never uses an Actor pointer, display name or array slot.
- **Placeholder highlight:** a separate passive cyan footprint follows the selected instance's frozen position, yaw and dimensions. No building Actor ticks, engine collision cooking, engine patches or pointer-coordinate correction were added.
- **Read-only inspector:** click a building outside placement mode. The panel appears in the existing left sidebar **below the Small Storehouse button**. Instance data: ID, settlement/district, exact centimeter position, yaw, completed state and placed footprint. Definition data: display name, type ID, configured footprint/version and configured cost. Missing definition data is explicitly unavailable. Current configured cost is not a refund or a claim about historical spending.
- **Lifecycle:** click another building to switch, empty terrain or Esc to clear. Entering placement clears inspection; cancellation restores normal clicking. Same-world view reconstruction reacquires the selected ID. Missing records clear safely. Reset/load intentionally clears UI selection, including when a new world reuses a numeric ID. Save keeps the current selection. Snapshot format is unchanged.
- **Diagnostics:** F12 remains off by default. Existing cursor diagnostics are preserved. While enabled, `SHOEN_INSPECT` logs the resolved ID/type/position/yaw or a clear event. This is an inspection audit, not a latency measurement. No permanent debug overlay or speculative latency/renderer fix was added.

## Automated verification

Host: Unreal 5.8.2 / CL 56702186, macOS 26.6.2, Xcode 26.6.0, Apple Clang 21.0.0; Apple M1 Max (10 CPU / 32 GPU), 32 GB RAM. Same portable C++20 core compiled by CMake and Unreal. Content schema 1, Small Storehouse definition version 1. Editor/game workflow, not packaged acceptance.

| Exact command | Final result |
|---|---|
| `python3 -m unittest discover -s tools/tests -v` | Exit 0; 28/28 passed |
| `python3 tools/dev.py core-test` | Exit 0; CTest 3/3: 20 original + 17 placement + 7 inspection suites |
| `python3 tools/dev.py build` | Exit 0; ShoenEditor Mac Development succeeded |
| `python3 tools/dev.py editor-test --suite foundation` | Exit 0; 5/5, zero test warnings/errors |
| `python3 tools/dev.py editor-test --suite placement` | Exit 0; 4/4, zero test warnings/errors |
| `python3 tools/dev.py editor-test --suite inspection` | Exit 0; 3/3, zero test warnings/errors |

[Final logs, summaries and red/green evidence](../../artifacts/inspection/). Core tests cover three real placements with distinct IDs, exact lookup, wrong/missing/removed IDs, key-record mismatch, snapshot round-trip, unchanged World state and configured-versus-frozen data. Unreal covers body/roof picking, rotated/oblique/nearest/occluded/invalid rays, shifted instance ordering, destroyed-view recreation, highlight geometry and controller selection/placement/save/load/reset lifetimes. Tooling rejects wrong-suite or failed inspection reports.

Failing tests were run before implementation: core inspection 0/7, three new tooling failures and all three Unreal inspection tests failing against stubs. During integration, a compile error in conditional diagnostic logging was fixed. The first lifecycle run also exposed an uninitialized test World with no registered player controller; the fixture now uses normal actor initialization and asserts registration. No runtime workaround was added for that fixture issue. All final commands above pass. [Independent conformance and code-quality reviews](../../artifacts/inspection/review.md) found no remaining material defect.

Headless automation does not establish rendering or physical mouse acceptance.

## Rendered verification

Launched `python3 tools/dev.py run --scenario settlement`, Metal SM5. The wrapper requests 1600×900; the actual Mac viewport is **1280×720**, window origin (116,118), DPI/app scale 1, backing scale 2. F12 reported the native and viewport pointer together at (953,533); the computer-control click marker itself can appear elsewhere. This is the already-known automation limitation, not evidence of a new physical pointer offset.

Tool-driven actions observed in the actual game:

- Scene contained ID 5 when this rendered pass began. Added ID 6 by native-position mouse press at (2067,2404,0) cm, yaw 15°. Exited placement and clicked it: cyan highlight and inspector showed its own ID/transform, Completed, settlement 1/district 2 and Small Storehouse configuration.
- Entered placement (clearing inspection), zoomed to a separate valid position, rotated and mouse-placed ID 7 at (1086,1778,0) cm, yaw 30°. Cancelled placement and clicked it: inspector and highlight switched to ID 7.
- F5 saved three buildings and 140 timber/85 treasury. Added unsaved ID 8 at approximately (72,1131,0) cm, yaw 0°; resources became 120/80 and count became four. F9 restored the three-building layout and 140/85 with no selection. Save/load actions were separate and their results observed.
- F12 was toggled off for ordinary presentation. The game was left paused with the restored three buildings visible for the human pass.

The 1,295-byte saved snapshot was decoded through the shared DomainCore reader: IDs 5/6/7, positions and rotations are recorded in [saved records](../../artifacts/inspection/manual-saved-records.txt). ID 5 is (-2054,-258,0) cm at 0°; all are Small Storehouse version 1 with an 800×600 cm footprint. Captures: [ID 6 inspector](../../artifacts/inspection/selected-building-6.png), [ID 7 inspector](../../artifacts/inspection/selected-building-7.png).

These are tool-driven observations, supplemented by the separate human physical acceptance below.

## Human physical acceptance

On 2026-09-15, in response to the explicit M2B physical acceptance checklist, the user answered **“All listed checks pass.”** This verifies:

- Physical clicking of each of the three buildings; correct cyan highlight and distinct ID/position/yaw.
- Empty-ground deselection.
- Entering and cancelling placement, then ordinary selection again.
- F5 save, adding a building, F9 load, and physically selecting restored buildings.
- Readable inspector, aligned physical clicks, and correct restored IDs/types/transforms.

This is new human verification of M2B, separate from earlier M2A acceptance and the tool-driven replay. [Exact acceptance procedure and record](../../artifacts/inspection/manual-acceptance.md).

## Save compatibility and preserved scope

Writer v2; readers v1/v2, unchanged in M2B. Building identity, type/version, integer transform, frozen dimensions/state and paid transactions remain authoritative in World. Selection is UI state and is not serialized. Separate Foundation/Settlement save slots remain. The existing settlement save and backup were copied to `game/Saved/AcceptanceBackups/m2b-20260915-060836/` before testing; [backup hashes](../../artifacts/inspection/save-backup.txt). The current settlement slot contains the three-building acceptance fixture.

No demolition, upgrades, construction queues/workers, inventories/storage capacity, roads, farming, housing, infill, district specialization, smith production, combat or final art was added. Ordinary storehouses still complete immediately and have no production/storage behavior. User-supplied handoff documents and asset workbook remain untouched.

## Known limitations

- The computer-control tool cannot reliably move the native pointer. Human physical selection/alignment is accepted; automation limitations remain separate from game behavior.
- The slight UI response delay reported and accepted in M2A remains **unmeasured**, with no established cause or new latency fix. F12 logs do not measure end-to-end input-to-display latency. See [profiling boundaries](../../docs/execution/milestone-2a-latency.md).
- Placeholder Canvas panel targets at least 1280×720 and the current single building family. No advanced/responsive inspector framework, editing or tooltips. The cyan footprint is a simple selection aid, not final art.
- Earlier automated captures sometimes lost glyph portions; human M2A text acceptance remains valid. Current inspector engine captures are readable. The user also physically confirmed this new panel is readable.
- Picking scans buildings and terrain on clicks. This is not proof of 5,000/10,000-building response time. No spatial index or performance promise was introduced.
- Only Mac editor/game has been verified. Other platforms, standalone packaging, final art/animation/audio and full beta scale remain unverified. Existing optional ACL/audio startup diagnostics are separate from the zero-warning final test results.
- Rapid save/load inputs in one update retain the existing fixed polling order. Acceptance separates each action and observes its result.

## Recommended next task

With M2B accepted, **M2C should begin with a focused, opt-in UI latency measurement pass**: correlate input event receipt, UI hit processing, preview update, simulation transaction and rendered/presented response, then fix only an observed bottleneck. This recommendation addresses the user's known delay before more interaction systems are added. No M2C implementation has begun.
