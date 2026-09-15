# Milestone 2B rendered and physical acceptance

Status: **ACCEPTED by human physical verification on 2026-09-15.** Automated and computer-control evidence is reported separately.

## Procedure in the actual game

Launch `python3 tools/dev.py run --scenario settlement` at 1280×720. Preserve the existing settlement save before using the single save slot for this test. Pause the clock to make before/after comparisons simple.

1. Choose Small Storehouse with **B** or the left sidebar button. Place three separated storehouses with the physical mouse, rotating with **[ / ]** so their positions/facings differ. Press **Esc** to exit placement.
2. Physically click the visible body or roof of A. Check its cyan footprint highlight and the inspector beneath the Build button. Record ID, position and yaw. Check instance settlement/district/completed state, and the separate definition name/type/footprint/configured cost.
3. Click B and C separately. Each must change the highlight and show its own distinct ID/position/yaw.
4. Click empty terrain; the highlight and inspector must clear. Click a building again, enter placement, and cancel; normal clicking must work again.
5. Save with **F5** or **Save settlement**. Observe the save result before continuing. Place one additional building, cancel placement and observe the altered world.
6. Load with **F9** or **Load settlement**. Observe the restored three-building layout and resources. Selection intentionally clears on load.
7. Physically click each restored building. Its ID, type, position and yaw must match the recorded values. Hover/click positions must correspond to the visible controls; note any reproducible miss or offset.

## Observed evidence

Unreal 5.8.2, Metal SM5, Mac editor/game; actual viewport 1280×720. The final compiled M2B implementation on `codex/milestone-2b-inspection` passed all requested regressions before this physical pass.

The assistant presented this explicit acceptance question:

> The M2B build is open with three storehouses; the inspector appears below the Small Storehouse button after selection. Please physically click each building and empty ground, check the cyan highlight and distinct ID/position/yaw, enter and cancel placement, then save (F5), add a building, load (F9), and click the restored buildings. Are the panel readable, clicks aligned, and restored IDs/types/transforms correct?

The user replied: **“All listed checks pass.”**

This confirms physical A/B/C selection and switching, cyan highlighting, distinct ID/pose inspection, empty-ground deselection, placement entry/cancellation, save/add/load/reselection, readable text and aligned physical clicks. The user confirmed correct restored IDs/types/transforms. Prior M2A acceptance is not substituted for these new checks.

Before the human pass, tool-driven replay verified IDs 6 and 7, saved three buildings, added an unsaved fourth and loaded back to three with 140 timber/85 treasury. Selection captures `selected-building-6.png` and `selected-building-7.png`, `manual-saved.shoen` and `manual-saved-records.txt` preserve that separate replay. The scene already contained ID 5 when the assistant began rendered checks; no claim is made that the assistant physically created or selected every building.

F12 confirmed native/viewport agreement at (953,533), with window origin (116,118), window/app scale 1 and display backing scale 2. The tool's click marker did not reliably reposition the native pointer. The native pointer later moved outside the window during a tool-driven attempt on the unsaved fourth building, so that attempted selection is not counted as a passing check. No coordinate workaround was added. F12 was turned off for the human pass.

Existing save and backup were preserved before test saves; see `save-backup.txt`. The one-off `read_snapshot.cpp` evidence utility uses the shared DomainCore reader, not a separate decoder. It produced `manual-saved-records.txt` with IDs 5/6/7 and exact frozen transforms.

## Existing known issue

The user reported a slight UI response delay in M2A, without missed inputs. It remains unmeasured. This slice adds no speculative latency fix and leaves F12 diagnostics off during ordinary play.
