# SHŌEN status

## Current milestone

**User Milestone 1: technical foundation.** Implemented and built on macOS, with simulation and save proofs passing. **Mouse-input acceptance remains open**, so this milestone is not yet fully accepted. No work on the next gameplay milestone has begun.

The initial repository contained only a tracked README and user-supplied, untracked design/asset-planning files. There was no Unreal project to preserve. The authoritative handoff was found at `japan_strategy_codex_handoff/`, not `design-handoff/`. Those documents, their ZIP, and the asset workbook were preserved.

## Working

- C++ Unreal 5.8.2 project with a real [Foundation map](game/Content/Domain/Maps/Foundation.umap). Runtime code creates primitive terrain, a road and two building blocks.
- Unreal exclusions, binary LFS attributes and a repository-local LFS hook. Generated `Binaries`, `Intermediate`, `DerivedDataCache`, `Saved` and CMake output are ignored.
- A game-instance subsystem owns one engine-independent C++20 world. CMake and Unreal compile the same simulation implementation. Rendering does not own population, and recreating a view does not reset the world.
- Stable settlement, district, cohort, service, formation and general IDs. Six occupations; cohort origin, skill and estate; six general attributes; food, treasury, timber, iron, fuel and equipment stocks.
- Campaign clock: pause / 1× / 3× / 5× / 10×, fixed whole-day processing, integer subday remainder, starting year 1180 and a 360-day simulation calendar. One day takes three real seconds at 1×. Date and speed appear in the HUD.
- **Population proof verified in automated tests and the rendered game:** 200 available → 100 available / 100 in service → 20 dead, 15 wounded and 65 healthy → **165 available / 15 recovering / 20 dead**. Workers in service or recovery do not count as available civilian labor. Outcomes and demobilization cannot be applied twice.
- Immutable source information returns survivors to their exact originating cohort. Formation membership agrees with attached active/wounded service records. Captive, missing and deserted statuses remain living people in the accounting model.
- Versioned, bounded snapshot with a corruption checksum, explicit field encoding, validation before replacement, temporary write and previous-save backup. Clock remainders, resources, origins, formations/orders/groups, transaction IDs and RNG state survive loading.
- **Live save/load verified with F5/F9:** saved a paused 100-person mobilized formation, applied casualties and demobilized, then restored the original date, pause state, 100 available workers and 100-person formation. Unreal automation also compares the entire restored world after replacing it with a different fixture.
- Finite 1,000 / 4,000 / 8,000 / 20,000-person fixtures. Each formation has 100 primitive instances, one Actor and one instanced-mesh component; there are **zero individual soldier Actors**.
- The final Z/X/C/V preset shortcuts and R reset were each verified in the rendered game. All four displayed the expected counts. [8,000-soldier screenshot](artifacts/evidence/scale-8000.png).
- Fixed 20 Hz formation movement, target facing and control-group data. Small group orders form a line; large group orders use a compact, rotated grid with nonoverlapping targets. Movement, facing, selection highlights and camera motion were observed in the rendered benchmark.
- Strategy-camera code provides smooth WASD pan, wheel zoom, Q/E or middle-drag rotation, Shift-middle pan and speed scaled by zoom. The automated rendered camera sweep verifies pan/zoom/rotation presentation. Physical held-key and mouse-drag acceptance is still pending with the pointer issue below.

See [README](README.md) for launch commands and controls, and [population screenshot](artifacts/evidence/population-proof.png) for the visible accounting result.

## Placeholder

All art is temporary: engine cubes, flat colors, one simple ground slab, rigid rectangular soldier slots, debug selection/facing markers and a Canvas HUD. Wounded instances are shorter blocks. No final Japanese architecture, samurai, civilians, equipment, terrain or animation was created.

The casualty result is an explicitly labeled accounting script, not combat. There is no daily production, automatic wound recovery, recruitment travel, pathfinding, collision avoidance, organic growth, campaign network, general gameplay, AI or diplomacy. General and occupation/resource structures establish future contracts only.

## Milestone 1 input acceptance — 2026-09-15 follow-up

**Milestone 1 is NOT accepted yet.** The automated cursor mismatch is characterized, and a separate invalid-selection defect is fixed. The human-operated acceptance pass is still pending. No Milestone 2 slice is authorized or started.

### Root cause and coordinate evidence

The computer-control tool's click marker is independent of the native macOS pointer in this reproduction. At a displayed click on the 1,000-soldier button (window image approximately 80,550), macOS reported screen position **780,580**, Slate reported **780,579**, and both converted to viewport position **664,462**. The click reached Unreal at **664,462**, outside that button. This is an input-delivery limitation of the reproduced automation path, not evidence for a HUD multiplier or a 2× Retina correction.

The F12 diagnostic now independently reads `NSEvent.mouseLocation`, converts it with Unreal's installed Mac screen conversion, and compares it with Slate and SceneViewport. It never warps the cursor or feeds substitute coordinates into gameplay.

| Stable rendered sample | Windowed | F11 window fullscreen | Returned to windowed |
|---|---:|---:|---:|
| Actual viewport pixels | 1280×720 | 1512×949 | 1280×720 |
| Viewport/Slate window origin | 116,118 | 0,33 | 116,116 |
| Local-to-pixel scale | 1,1 | 1,1 | 1,1 |
| macOS screen backing scale | 2 | 2 | 2 |
| Window DPI / Slate application scale | 1 / 1 | 1 / 1 | 1 / 1 |
| Native screen pointer | 780,580 | 1093,362 | 1093,362 |
| Slate screen pointer | 780,579 | 1093,361 | 1093,361 |
| Red viewport cross | 664,462 | 1093,328 | 977,245 |
| Cyan native-pointer cross | 664,462 | 1093,329 | 977,246 |

Rounded values; stable native/Slate/viewport positions agree within one pixel. The backing scale and window DPI are different coordinate-system properties, not interchangeable multipliers. Window position and viewport geometry update across F11 transitions. A transient stale viewport sample during return from fullscreen resolved by the next one-second sample. Stable samples had active/focused viewport, no mouse capture and no raw/high-precision mode.

Installed UE 5.8.2 source confirms `FMacCursor` caches its position, normal Mac movement refreshes it from `NSEvent.mouseLocation`, mouse-down uses the cached Slate position, and SceneViewport converts screen coordinates using its geometry and pixel dimensions. The observed cache agrees with the independent native query; no persistent physical-pointer cache defect has been demonstrated.

**The user's earlier report that a physical click did not respond remains unconfirmed with the new diagnostics.** The tool marker result cannot settle that report. The requested actual-window mouse follow-up has not yet been answered. Continuous physical pointer tracking, arbitrary window dragging, other monitors/scaling configurations, and exclusive fullscreen are not certified.

Evidence: [coordinate/click samples](artifacts/evidence/input-20260915/cursor-samples.txt), [windowed screenshot](artifacts/evidence/input-20260915/cursor-windowed.png), [fullscreen screenshot](artifacts/evidence/input-20260915/cursor-fullscreen.png).

### Fix and scope

- Extended the existing F12 overlay with a cyan native-pointer X, Slate/viewport coordinates, geometry, actual resolution, DPI/backing scale, window mode, focus and capture. Read-only Mac code is isolated in `Private/Mac`; other platforms retain the Slate/viewport diagnostics.
- Fixed a separate selection defect: failed cursor queries/projection could read an uninitialized ground position or turn an outside-window release into a box ending at (0,0). Invalid releases now cancel without altering the previous selection, and invalid queries do not overwrite the last valid endpoint.
- Added a regression that first reproduced loss of a 10-formation selection for invalid click and box endpoints. No engine source, global settings, arbitrary coordinate correction, DomainCore logic, or later-milestone gameplay was changed.
- No physical shortcut conflict has been established. Source review confirms focused physical Control maps correctly. Existing inherited Unreal F-key conflicts remain cleared. Focus the game before pressing Control; UE's modifier synthesis when acquiring focus is a separately observed source-level edge, not physically verified here.

### Input verification

**No new human-operated input has been confirmed in this follow-up.** Tool-driven rendered checks performed: left-click reproduction, F12 diagnostics, F11 to window fullscreen and back, F10 evidence captures, Z/R fixture switching, and visible wheel zoom. After the final regression run, a click marker over the 4,000-soldier button selected the formation under the native/red/cyan position instead. This confirms selection processes the native coordinates while the tool marker is elsewhere. These are not a substitute for physical acceptance.

| Required physical input | Result |
|---|---|
| Held W, A, S, D (each direction) | Pending |
| Wheel zoom | Pending |
| Held Q and E rotation | Pending |
| Middle-button drag rotation | Pending |
| Shift + middle-button drag pan | Pending |
| Pan speed near and far zoom | Pending |
| 1,000 / 4,000 / 8,000 / 20,000 preset mouse buttons | Pending; automated click reproduces displaced marker |
| UI hover/click alignment and no offset | Pending |
| Individual formation selection | Pending |
| Box selection and Shift-add selection | Pending |
| Right-click move order | Pending |
| Right-drag facing change | Pending |
| Sensible orders for multiple selected formations | Pending |
| Ctrl+number group assignment | Pending |
| Number-key group recall/selection | Pending |
| Recalled group movement order | Pending |

The computer-control API exposes discrete keypresses and left-button dragging; it cannot hold WASD/QE or perform a middle-button drag. Actual mouse/keyboard operation in the Unreal window is required to close these entries. Previous rendered keyboard and benchmark evidence remains valid for its stated scope only.

### Automated verification for this follow-up

All commands below were rerun after the final input source changes:

| Exact command | Result |
|---|---|
| `python3 -m unittest discover -s tools/tests -v` | Exit 0; 21/21 passed |
| `python3 tools/dev.py core-test` | Exit 0; CTest 1/1 passed, 20 behavioral suites |
| `python3 tools/dev.py build` | Exit 0; ShoenEditor Mac Development succeeded |
| `python3 tools/dev.py editor-test --suite foundation` | Exit 0; 5/5 passed, zero errors/warnings; final report at 06:17:35 UTC |

The new `SelectionProjectionFailure` test first failed with 10 selected formations reduced to 1 for a failed click projection. The added invalid-box case then failed with selection reduced to 0. Both now pass. Evidence: [click red](artifacts/evidence/input-20260915/selection-red.txt), [box red](artifacts/evidence/input-20260915/selection-box-red.txt), [final Unreal report](artifacts/evidence/input-20260915/unreal-tests.json), [build](artifacts/evidence/input-20260915/unreal-build.txt), [tooling](artifacts/evidence/input-20260915/tooling-tests.txt), [core](artifacts/evidence/input-20260915/core-tests.txt).

`python3 tools/dev.py run --scenario foundation` was launched again after those tests. The rendered Metal SM5 game showed the 1,000-person fixture, wheel zoom, and selection at the native pointer position. [Final rendered selection](artifacts/evidence/input-20260915/final-selection-at-native-pointer.png), [final input log](artifacts/evidence/input-20260915/final-run-input.txt). It was reset to 200 workers and left open with F12 enabled for the physical button check.

Independent code review checked the selection fix, regression and diagnostic platform boundaries. These checks do not establish physical acceptance.

## Tests

Verified on 2026-09-15 using Unreal **5.8.2 / CL 56702186**, macOS **26.6.2**, Xcode **26.6.0**, Apple Clang **21.0.0**, Metal compiler **32023.883**, CMake **4.4.3** and Git LFS **3.8.0**. Machine: Apple **M1 Max, 10 CPU cores, 32 GPU cores, 32 GB RAM**. See [toolchain.lock.json](toolchain.lock.json).

Missing prerequisites were resolved using `brew install cmake git-lfs`, `xcodebuild -downloadComponent MetalToolchain`, and `git lfs install --local`. No global Git configuration was changed.

| Exact command | Result |
|---|---|
| `python3 tools/dev.py doctor` | Exit 0; required installed tools detected |
| `python3 -m unittest discover -s tools/tests -v` | 21 tests passed |
| `python3 tools/dev.py core-test` | Exit 0; CTest 1/1 passed, covering 20 behavioral suites |
| `/tmp/shoen-core-build/domain_core_tests` | 20/20 suites passed |
| `python3 tools/dev.py build` | Exit 0; ShoenEditor Mac Development succeeded |
| `python3 tools/dev.py create-map` | Exit 0; actual engine-generated map verified |
| `python3 tools/dev.py editor-test --suite foundation` | Exit 0; 5/5 Unreal tests passed, zero errors/warnings (06:17 UTC follow-up) |
| `python3 tools/dev.py run --scenario foundation` | Rendered Metal SM5 game launched; ledger, pause, F5/F9 and Z/X/C/V/R presets/reset verified visually |

The 20 portable suites cover all nine requested invariants, corruption and malformed-state rejection, overflow/atomic failure, stable IDs/RNG streams, all scale fixtures, compact army destinations and deterministic movement continuation. Initial failing tests were run before implementation; regression failures and current outputs are retained in [core evidence](artifacts/core/).

The Unreal tests are `ClockBinding`, `InputConfiguration`, `PopulationAndSave`, `ViewDoesNotResetPopulation`, and `SelectionProjectionFailure`. Input coverage catches missing plugin-class defaults, inherited debug shortcut collisions, and invalid selection endpoints. The final input follow-up automation run at 06:17 UTC was after the last source changes; its results are linked above. Earlier foundation results remain in `artifacts/evidence/`. Raw engine logs/reports remain local and ignored.

Earlier verification found and fixed invalid optional-plugin input classes, the cube's noisy world-grid material, inherited F-key render-mode shortcuts, population reset on view reentry, and excessively wide large-army move orders. Final claims above use the later passing results.

## Performance

All four runs completed with exit 0 and validated counts/metrics on the machine above. Each result is one run, not a statistical hardware certification.

| Soldiers | Formations | Measured seconds | Median FPS | Median / p95 frame ms | Peak process GiB | Report |
|---:|---:|---:|---:|---:|---:|---|
| 1,000 | 10 | 30 | 62.4 | 16.02 / 19.33 | 3.30 | [JSON](artifacts/tooling-benchmark-1000-20260915T054346Z-442dce59.json) |
| 4,000 | 40 | 30 | 64.2 | 15.59 / 18.32 | 3.32 | [JSON](artifacts/tooling-benchmark-4000-20260915T054507Z-865a3248.json) |
| 8,000 | 80 | 120 | 60.8 | 16.45 / 28.46 | 3.41 | [JSON](artifacts/tooling-benchmark-8000-20260915T054621Z-e420e408.json) |
| 20,000 | 200 | 120 | 59.9 | 16.71 / 19.33 | 3.38 | [JSON](artifacts/tooling-benchmark-20000-20260915T054856Z-1c94c197.json) |

Exact commands:

```sh
python3 tools/dev.py benchmark --soldiers 1000 --seconds 30
python3 tools/dev.py benchmark --soldiers 4000 --seconds 30
python3 tools/dev.py benchmark --soldiers 8000 --seconds 120
python3 tools/dev.py benchmark --soldiers 20000 --seconds 120
```

The p95 frame time is the threshold that 95% of recorded frames meet or beat. Minor differences between counts include run-to-run variation; no scaling or bottleneck conclusion is inferred.

Workload: installed editor executable in `-game`, Metal SM5, 1280×720 actual viewport, VSync disabled, ten-second warmup, alternating movement/facing every six seconds, changing selection and camera pan/zoom/rotation. The same finite ledger drives every preset. Normal visibility culling applies; registered instance count is not a claim that every soldier is simultaneously visible.

Frame times are real wall-clock frame intervals. Simulation CPU measures only the clock and formation-step call. Process memory includes editor/runtime overhead. GPU timings, input latency, final-art cost and a reference-machine scale certification are not measured. These are **primitive movement measurements only**.

## Known issues

1. **Physical input acceptance remains open.** The automated click-marker discrepancy is characterized above: native macOS and Unreal agree while the tool marker is elsewhere. The original human-click report still needs the actual-window F12 follow-up and the complete physical checklist. No engine patch or guessed coordinate adjustment is justified by current evidence.
2. The HUD targets at least 1280×720; smaller windows are not supported. Scene framing can place some formations behind the control panel; camera panning is intended for inspecting them.
3. Orders use straight-line rigid movement with no obstacle avoidance. Army movement is a laboratory and cannot establish full-battle performance.
4. Only the Mac editor/game workflow was built and launched. Standalone packaging, Windows/Linux builds, GPU profiling and input-latency measurements have not been performed.
5. Snapshot v1 has no migration from future formats and no authentication; its checksum detects accidental corruption. Recovery timing and returning prisoners/missing people require later gameplay rules.

## Next recommended task

**Complete the physical Milestone 1 checklist in the actual Unreal window.** First confirm that the red cross and cyan X follow the physical pointer and that the 1,000-soldier button responds. Then verify every pending control above. Milestone 1 is not accepted, so no Milestone 2 slice is recommended yet.
