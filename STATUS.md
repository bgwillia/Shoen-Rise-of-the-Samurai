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
| `python3 tools/dev.py editor-test --suite foundation` | Exit 0; 4/4 Unreal tests passed, zero errors/warnings |
| `python3 tools/dev.py run --scenario foundation` | Rendered Metal SM5 game launched; ledger, pause, F5/F9 and Z/X/C/V/R presets/reset verified visually |

The 20 portable suites cover all nine requested invariants, corruption and malformed-state rejection, overflow/atomic failure, stable IDs/RNG streams, all scale fixtures, compact army destinations and deterministic movement continuation. Initial failing tests were run before implementation; regression failures and current outputs are retained in [core evidence](artifacts/core/).

The Unreal tests are `ClockBinding`, `InputConfiguration`, `PopulationAndSave`, and `ViewDoesNotResetPopulation`. The input test catches missing plugin-class defaults and inherited debug shortcuts colliding with speed keys. The final automation run at 05:51 UTC was after the last source changes. Curated results: [Unreal tests](artifacts/evidence/unreal-tests.json), [build](artifacts/evidence/unreal-build.txt), [tooling tests](artifacts/evidence/tooling-tests.log). Raw engine logs/reports remain local and ignored.

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

1. **Mouse acceptance is unresolved on this Mac session.** The user initially reported that the preset button did not respond. Diagnostic runs showed Unreal routing clicks to a cached position different from the visible pointer, sometimes outside the HUD. Installed Mac/Slate source confirms mouse-down uses cached cursor state. No HUD-coordinate multiplier or engine patch was added without evidence. F12 toggles a red cross and coordinates for a physical-pointer follow-up. Mouse click/box selection, right-drag facing, mouse pan/rotation, and physical group shortcuts are not reported as manually verified. Keyboard Z/X/C/V opens the four presets; R resets the accounting fixture; M/O/Backspace drives its proof; F5/F9 saves/loads.
2. The HUD targets at least 1280×720; smaller windows are not supported. Scene framing can place some formations behind the control panel; camera panning is intended for inspecting them.
3. Orders use straight-line rigid movement with no obstacle avoidance. Army movement is a laboratory and cannot establish full-battle performance.
4. Only the Mac editor/game workflow was built and launched. Standalone packaging, Windows/Linux builds, GPU profiling and input-latency measurements have not been performed.
5. Snapshot v1 has no migration from future formats and no authentication; its checksum detects accidental corruption. Recovery timing and returning prisoners/missing people require later gameplay rules.

## Next recommended task

**Complete the Mac input acceptance pass and resolve any remaining cursor-delivery defect:** verify that the F12 cross follows the physical pointer, then test preset buttons, held-key camera movement, drag pan/rotation, individual/box selection, move/facing and control groups. Keep this within Milestone 1; review the foundation before authorizing any settlement or combat milestone.
