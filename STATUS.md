# SHŌEN status

## G01–G05 mature olive-grass refinement — 2026-09-20

Completed and saved only G01–G05 with the verified existing M11 asset and exact M11/M6 target mixtures: 40/60, 45/55, 30/70, 25/75 and 28/72. Delivered XY cubics, priorities, influence and variable inward fades are retained, with a 0.52 m inward filtering reserve. M6/M11 source assets, all earlier material nodes, all 2,404 actor transforms and terrain are preserved. Actual Metal matching views show restrained green variation; [whole-map overview, comparisons and evidence](artifacts/grass-ground-refinement/README.md). Portable tests 7/7 and Unreal build passed. Initial sampler overflow was resolved by sharing the grass sampler; final height matches the verified hill-pass readback (initial asynchronous zero readback is documented as invalid). Existing rock grain and terrain edges remain outside this pass. No further IDs started.

## H01–H09 ground-material refinement — 2026-09-20

Nine hill treatments applied in six local groups with the completed M10 and existing M6/M8 branches. Delivered cubic boundaries, target ratios, ascending priorities and broad inward widths are preserved. H01/H03/H05/H07/H08 influence was locally reduced to 0.62 after full strength produced an artificial green separation from older outer rock margins. Shared materials, previous river/pond/road coverage, physical terrain and placed objects are unchanged. Original M8 repetition/bright grain and pale traces outside the envelopes remain documented limitations. Portable tests 7/7 and Unreal build passed; matched strategy and lower-oblique renders and preservation checks are in [the hill-pass evidence](artifacts/hills-ground-refinement/README.md). No G treatments or new geometry were added.


## Unreal-MCP local editor integration — 2026-09-17

Installed Unreal-MCP 0.17.0 with a local Codex-managed server. UE build and 7 portable targets passed; real stdio tool discovery returned 61 tools, editor state identified SettlementMap_01, and a rendered viewport capture was inspected. Four upstream plugin files needed narrow Mac compilation fixes. Codex restart is required to load its new tools; setup, patch and evidence are in [the integration note](docs/execution/unreal-mcp.md).

## Terrain suitability foundation — 2026-09-16

TerrainSuitability_01 now queries the existing native TerrainBase_01/WaterBase_01 for slope, footprint unevenness/water, wet/dry farming and infantry/cavalry costs. F8 cycles the optional 10 m overlay; B uses shared terrain rules in the existing placement transaction, and Home frames the village. Thresholds are in `game/Config/TerrainSuitability_01.json`. Session-only, with no terrain redesign or pathfinding. Final build, two focused portable targets and one live-map Unreal test passed; actual Metal overlay captures are separate. [Controls, brief terrain note and evidence](artifacts/terrainsuitability01/README.md).

## Kusazuri 01 waist armor note — 2026-09-15

Kusazuri01 now has seven independently hinged leaves in a 30-mesh editable Blender source, with revised Dō-matched plate detail, red lacing, restrained brass, braided indigo obi and dark padded lining. It imports on unchanged native Manny with one opaque material, the existing three 2K Dō textures and 147,408 / 44,210 / 15,734 triangle LODs. Existing Kabuto/Dō/Sode geometry and gameplay remain unchanged.

The 372-pose sweep preserves rigidity with no inversion. Idle/walk/attack are leg-clear; two run frames retain shallow contact (shell up to .896 mm, lining 2.261 mm), and the extreme knee lift retains approximately 6.425 mm shell contact. Stock unarmed hand contact and shallow Dō attachment contact remain documented. Forty-eight source renders and twenty actual Metal views support inspection. Final build, 67 tooling tests, 6 portable targets and all 21 Unreal tests pass, including Blender/Unreal hinge parity and terrain regression.

The reserved 1280×720 Metal static comparison measured approximately +3.63 ms at 100 figures and +3.72 ms at 500 figures on M1 Max / 32 GB. These short trials do not establish animated-army or combat capacity; single-character variation prevented isolating a reliable incremental cost, and frame hitches remain. [Editable asset/workflow](SourceArt/Characters/Samurai/Kusazuri01/README.md), [verification, captures and costs](artifacts/kusazuri01/verification.md). The revised finish has not been approved by the user. Next recommendation: **Kote_L_01 + Kote_R_01**; it has not been started.

## Sode 01 paired armor note — 2026-09-15

Both Sode shoulders now have an editable sixteen-part Blender source and imported assets on native Manny, with a revised Dō-matched lacquer/lacing finish, fitted ornament, twisted cords and quilted lining. The pair uses one shared material with the existing Dō textures; runtime LODs total 72,116 / 26,388 / 7,976 triangles. Fourteen actual Unreal views/motions and sixteen source pose samples are recorded. The required pose controller preserves rigid panels; flexible tie contact and simplified raised-arm lift remain. Single-character comparisons measured +0.446 ms close and +0.249 ms tactical frame median versus Kabuto+Dō. Build, 67 tooling tests, 6 portable targets and Sode native automation passed; the shared full suite had one known missing-fixture failure in the separate in-progress Kusazuri task. [Asset/workflow](SourceArt/Characters/Samurai/Sode01/README.md), [verification and captures](artifacts/sode01/verification.md). Human visual approval remains pending.

## Dō 01 / official Manny art-pipeline note — 2026-09-15

The user's follow-up replaces the custom art-fit body with Epic's official Manny. Dō01 now has ten editable Blender components, an imported skeletal mesh on Manny's unchanged native skeleton, three LODs (81,392 / 32,556 / 5,504 triangles), one 2K atlas and fourteen rendered Unreal fit/animation views. Static full-outfit review crowds measured 58.6 / 36.4 / 28.5 median FPS at 100 / 500 / 1,000 figures on this Mac; this is an asset-cost probe, not full battle performance. The revised finish, smooth strap weighting and rear lining correction are preserved in the source. Neutral/raised/bend/turn/head samples are clear; stock unarmed attacks retain documented shoulder/helmet contact. [Asset/workflow](SourceArt/Characters/Samurai/Do01/README.md), [verification and incremental cost evidence](artifacts/do01/verification.md). Kabuto geometry and gameplay are preserved; this task adds no further armor component.

## Kabuto 01 art-pipeline note — 2026-09-15

Kabuto 01 now has a modular Blender source, three runtime LODs (Unreal: 94,608 / 31,238 / 7,062 triangles), one opaque material atlas, and an isolated Unreal review on the unchanged prototype mannequin. The revised construction and materials passed source/import checks, a current Unreal build, portable tests, and rendered idle/walk/head-turn checks; static 100 / 500 / 1,000 helmet crowds measured 108.3 / 89.4 / 63.5 median FPS, with timing outliers and remaining visual regularity documented in the [evidence](artifacts/kabuto01/verification.md). [Asset and workflow](SourceArt/Characters/Samurai/Kabuto01/README.md); visual approval and full-army performance certification are not claimed, and no next armor component was started.

## Prototype B — constrained battlefield and repeated warfare

**Prototype B is complete and committed as a playable feasibility prototype.** Prototype A was accepted at `60ca49fb0416d12423eb8c57ed3e234eba17dedb`; its evidence is archived in [Prototype A status](docs/execution/prototype-a-status.md). M1, M2A and M2B remain accepted. This work follows the [Prototype B request](docs/execution/prototype-b-request.md), on `codex/prototype-b-terrain`. It does not start Prototype C or restore production-hardening approval milestones.

### What is playable

Run `python3 tools/dev.py run --scenario terrain` after `python3 tools/dev.py build`. [Controls and two-war walkthrough](README.md#play-prototype-b-terrain-and-repeated-warfare).

- One authored west/east battlefield: impassable river, narrow bridge, distant ford, open ground, slowing woods and a defensive hill. Shared geometry controls movement, height, selection and passive rendering.
- A real 6,000-person settlement fields **16×100 polearms, 6×100 bows and 3×40 samurai: 25 formations / 2,320 people**. Recruitment removes workers from their occupations and consumes gear. The opposing finite army has comparable mixed roles.
- Individual/box selection remains available. Tab/category keys select armies or roles; group line destinations reserve separate spaces, preserve approximate frontage order and accept facing rotation. Ctrl+1–9 assigns groups; 1–9 recalls. Y chooses bridge, O ford, G nearest-enemy attack, I western deployment line.
- Formation-level reservations produce real queues without soldier Actors or per-person pathfinding. Bows have range and weaker melee; samurai have stronger combat/higher morale but finite estate manpower and elite gear. Facing, flank, woods and hill modifiers matter. Simple enemies guard the east bank, position bows behind infantry and react to nearby flank threats.
- H ends an active battle as a retreat, or returns the army after a result. Casualties return transactionally to their original occupations. P advances recovery; U remusters from the same diminished World. N is the explicit whole-session reset and must not be used between wars.

### Crossing failure found and fixed

The first rendered run exposed a genuine opposing-traffic deadlock: at 109 seconds, routed troops returning through the single-lane ford blocked all outgoing samurai. At 183 seconds it remained stalled, with zero friendly overlap. [Preserved failure and gameplay evidence](artifacts/terrain/rendered-demo.md).

The cause was a one-cell ford plus retreating formations sharing a final home-exit destination. The fix is confined to the authored terrain/navigation model: a three-row ford, separate eastbound/westbound lanes, unique reserved retreat exits and no repeated orders for settled retreats. Renderer and simulation consume the same widened geometry. Mid-transit retargeting keeps its committed adjacent leg; facing rotation preserves a common chosen crossing. The Unreal attack helper also moves invalid bow standoff points out of impassable river terrain. No engine patch or mouse-coordinate adjustment was made.

Targeted results: **30/30 one-way bridge formations cross by 209.1 simulated seconds**, with zero overlaps and no remaining stuck formations at the 360-second budget; **12/12 opposing ford formations cross**, also without overlap or a remaining stall. The actual 2,320-person command sequence gets all three elite formations across. [Core evidence, including RED failures](artifacts/terrain/core-evidence.md).

### First war → recovery → second war, in the final rendered build

The final ordinary game fought for 129.7 seconds, then H explicitly retreated: **482 dead, 232 wounded, 1,606 healthy returned**. The dead were 388 farmers, 39 laborers, 1 smith and 54 retainers. After P recovered the wounded, U raised a second army and F deployed it, with **no reset or resource refill**.

| Capability | First army | Second army |
|---|---:|---:|
| Soldiers | 2,320 | 2,266 |
| Samurai | 120 | 66 |
| Food produced/day while away | 4,800 | 3,636 |
| Food deficit/day while away | 1,200 | 1,882 |
| Basic equipment produced/day while away | 20 | 19 |

Elite replacement was limited by the 66 surviving retainers, despite sufficient gear. Ordinary reserves still supplied 2,200 levies; the first war damages economic support before exhausting all ordinary recruitment. The unsupported elite flank was expensive. The final combat snapshot had 9 ford completions (including returning troops), zero friendly overlap, and real melee/ranged/flank/hill activity; bridge congestion still left 14 reserved-cell waits over ten seconds. [Full rendered sequence, snapshots and images](artifacts/terrain/rendered-demo.md#final-rendered-verification-after-the-correction).

### Commands and input evidence

Rendered keyboard play exercises pause/resume, muster, deployment, army/category selection, bridge/ford commands, attack, line deployment/facing rotation, return, recovery, second muster and optional F7/F10 capture. Automated integration additionally covers line rotation preserving route, hill-aligned formation rendering and population conservation. Benchmark setup selects and assigns main/elite control groups through the authoritative command path.

Prior **human physical input acceptance** remains recorded: cursor alignment, camera/formation controls, UI clicks and building interactions worked. This B run uses computer-controlled keyboard input; it is **not new human physical mouse acceptance**. Synthetic mouse/modifier delivery limitations remain, including an unsuccessful synthetic Ctrl+1 attempt. No reproducible physical pointer regression was established. The user's slight UI delay remains non-blocking; no speculative latency fix was applied.

F7 snapshots, F6 profiling and F12 cursor diagnostics are optional. Normal play has no permanent profiling or diagnostic cursor overlay. F7 records software state, not physical input-to-display latency.

### Final rendered combat performance

Final corrected build, 120 seconds per size after three-second warmup, one Unreal process at a time. Actual 1280×720 windowed Metal, Mac Development editor-game, M1 Max / 32 GB. Both runs exited 0 and validated real combat, both crossings and navigation samples.

| Per side | Median FPS | Frame p95 / worst ms | Simulation CPU p95 ms | Navigation p95 / worst ms | Peak overlaps |
|---|---:|---|---:|---|---:|
| 1,000 | 109.4 | 10.002 / 54.785 | 0.0308 | 0.0428 / 0.1435 | 0 |
| 2,000 | 108.6 | 10.083 / 43.295 | 0.0863 | 0.1131 / 0.2947 | 0 |

Navigation is not the measured frame-budget bottleneck; its largest sample is 0.295ms. Simulation samples are per render tick, navigation samples per 20Hz step, so their percentiles are not directly comparable. Frame hitches remain, with no established cause. Peak reserved-cell waits over ten seconds were 8 / 17 formations; low CPU cost does not remove tactical congestion. [Full measurement methodology, queue counts, raw reports and limitations](artifacts/terrain/measurements.md).

### Automated verification

Final code passed on 2026-09-15:

| Exact command | Result |
|---|---|
| `python3 -m unittest discover -s tools/tests -v` | 51/51 passed |
| `python3 tools/dev.py core-test` | 6/6 CTest targets passed, including ten terrain suites and accepted A invariants |
| `python3 tools/dev.py build` | ShoenEditor Mac Development succeeded, 22.66 seconds |
| `python3 artifacts/terrain/run-unreal-smoke.py` | 18/18 Shoen Unreal tests passed; zero errors/warnings, including foundation, placement, inspection, profiling, A and B |
| `python3 tools/dev.py combat-benchmark --terrain --per-side 1000 --seconds 120` | Exit 0, 13,041 rendered frames; validated |
| `python3 tools/dev.py combat-benchmark --terrain --per-side 2000 --seconds 120` | Exit 0, 12,957 rendered frames; validated |

[Tooling log](artifacts/terrain/tooling-tests.log), [core log](artifacts/terrain/core-tests.log), [build log](artifacts/terrain/build.log), [Unreal summary](artifacts/terrain/unreal-summary.json), [exact Unreal command](artifacts/terrain/unreal-command.json), [bounded integration review](artifacts/terrain/review-integration.md). Unreal regression automation uses NullRHI and makes no rendering claim; rendered gameplay and benchmarks are separate.

### Remaining limits and risks

- The navigation model is an authored four-neighbor grid with visible snapping/cardinal travel. A 30-formation unopposed bridge queue takes about 3.5 minutes. Opposing manual orders on the single-lane bridge can still require regrouping or the ford; contact deliberately stops traffic. Passing is a corridor rule, not general crowd avoidance.
- A formation holding outside enemy range needs another attack/order. The simple AI does not guarantee every battle resolves without further commands. The next enemy scales to the newly raised army; there is no persistent opposing society yet. H retreat is a valid finish. This prototype does not establish polished attack-move behavior or enjoyable command pacing.
- UI labels are selected-only and capped to limit clutter; the temporary sidebar/status panel occupies substantial screen space. Automatic frontage and coarse target reservations need human tactical playtesting. Physical B-specific mouse and modifier usability has not been newly accepted.
- Frame outliers require investigation; no GPU, engine or input-latency cause is assumed. These are placeholder, Development editor-game measurements on one Mac, not packaged/final-art capacity claims.
- Terrain and both prototype sessions are session-only; F5/F9 protect the legacy save slots. Economy remains the deliberately coarse A model: free immediate prototype construction, simplified recovery/production, no final balance or extended samurai politics.

### Feasibility and recommended Prototype C

The results reinforce technical feasibility of formation-scale navigation and a shared population/economy/combat ledger. They also expose the larger design risk: affordable computation does not ensure readable orders or satisfying congestion and flank timing.

**Recommended C:** a bounded combined-arms command and battle-pacing playtest on this same map. Make attack/hold intent and queue feedback clear, test line width and supported flanks with a human, and profile the observed frame hitches. Keep the same society and terrain; do not add campaign systems or final art. **C has not begun.**

## T03 terrain-form refinement — 2026-09-18

Implemented only the lower-middle hill from `SHOEN_Terrain_Form_Refinement_Package.zip` on native additive layer `T03_LowerMiddleHill`. The crest rises up to 7.992 m and the side saddle lowers up to 3.383 m, with the package’s asymmetric shoulder support and smooth intervention boundary. Live baseline differed from package source by <0.003 m in T03; newer changes elsewhere (up to 2.421 m) remain intact. Existing ground material and scene placements are preserved.

Final native readback: 5,265 changed vertices, zero height changes outside T03, exact layer-off rollback and exact layer-on restoration. Portable tests 7/7; Unreal editor build succeeded. Matched actual Metal strategy/oblique views, section A, control-point comparison, rollback instructions and limitations are in [T03 evidence](artifacts/terrain-t03/README.md). No other intervention started; awaiting the user’s visual review of this hill.

## T01 terrain-form refinement — 2026-09-18

Implemented only the upper-left bent ridge and side hollow on native additive layer `T01_UpperLeftRidge`, preserving completed T03. Live/source discrepancy within T01 was <0.003 m. The isolated package field uses its actual smooth boundary, 30 m inward fade and unequal shoulders; native changes range from -3 to +9 m across 9,999 vertices.

Readback confirms zero height changes outside T01, exact T03 preservation, exact layer-off rollback and exact layer-on restoration. Existing material and 2,313 non-camera actor locations are preserved. Portable tests 7/7 and Unreal editor build passed. Matched rendered strategy/oblique images, controls, an explicitly authored local profile (the package has no T01 section), and rollback instructions are in [T01 evidence](artifacts/terrain-t01/README.md). T01 and T03 are saved enabled. No other intervention started.

## T02 terrain-form refinement — 2026-09-18

Implemented only the upper-middle tapered spur and side hollow on native additive layer `T02_UpperMiddleSpur`, preserving completed T01/T03. Live/source mismatch inside T02 was <0.002 m. The isolated field retains the package’s smooth boundary, 28 m fade, asymmetric shoulders and tapered lower end. Changes range from -2.367 to +6.5 m over 4,295 vertices.

Native readback confirms zero changes outside T02, exact T01/T03 preservation, exact layer-off rollback and layer-on restoration. Existing material and all 2,313 non-camera actor transforms are unchanged. Portable tests 7/7 and Unreal build passed. Matched actual Metal strategy/oblique renders, controls, a labelled local profile (no T02 section exists in the package), and rollback instructions are in [T02 evidence](artifacts/terrain-t02/README.md). T02/T01/T03 are saved enabled. No other intervention started.

## T04 terrain-form refinement — 2026-09-18

Implemented only the lower-right connected ridge and side hollow on native additive layer `T04_LowerRightRidge`, preserving completed T01/T02/T03. Live/source mismatch inside T04 was <0.003 m. The isolated field follows the package’s curved boundary, 30 m inward fade, asymmetric shoulders and connected crest. Changes range from -2.602 to +7 m over 6,186 vertices.

Native readback confirms zero changes outside T04, exact T01/T02/T03 preservation, exact layer-off rollback and layer-on restoration. Existing material and all 2,313 non-camera actor transforms are unchanged. Portable tests 7/7 and Unreal build passed. Matched actual Metal strategy/oblique renders, controls, a labelled local profile (no T04 section exists in the package), and rollback instructions are in [T04 evidence](artifacts/terrain-t04/README.md). All four completed layers are saved enabled. No other intervention started.

## T05 terrain-form refinement — 2026-09-18

Implemented only the isolated lowland rib adjustment on native additive layer `T05_LowlandRib`, preserving completed T01–T04. Live/source mismatch was <0.002 m. The isolated proposal retains its actual curved boundary and 22 m fade, with added protection around current road mesh bounds and local cap-transition smoothing after visual review. Changes range from -4 to +1 m over 4,051 vertices.

Native readback verifies zero height changes outside T05 or within current road bounds plus 6 m, exact preservation of all prior landforms, exact layer-off rollback and layer-on restoration. Existing material and all 2,313 non-camera actor transforms are unchanged. Portable tests 7/7 and Unreal build passed. Matched actual Metal strategy/oblique renders, section B, slope measurements, controls and rollback instructions are in [T05 evidence](artifacts/terrain-t05/README.md). The map is saved with all five layers enabled. No other intervention started.

## T06 terrain-form refinement — 2026-09-18

Implemented only the main river bend bank adjustment on native additive layer `T06_MainRiverBanks`, preserving T01–T05. Live/source discrepancy reached 1.008 m, so the old target was locally adapted to current water geometry and recent terrain improvements. The inner shelf, submerged bed and water-contact guard remain fixed; the eligible outer shoulder rises up to 0.75 m over 564 native vertices. The source cutting targets were not forced into newer river work.

Native readback verifies zero changes outside T06, at wet contacts/submerged ground, inside road protection or on newer improvements of at least 0.25 m. Water mesh exports are byte-identical and wet classification, water material/transform, all 2,313 non-camera actor transforms and prior landforms are unchanged. Exact layer rollback/restoration passed. Portable tests 7/7 and Unreal build passed. Matched strategy, two oblique and detail renders, section C, rebase evidence and rollback instructions are in [T06 evidence](artifacts/terrain-t06/README.md). All six completed layers are saved enabled. No other intervention started.

## T07 terrain-form refinement — 2026-09-18

Implemented only tributary bank shoulders on native additive layer `T07_TributaryShoulders`, preserving T01–T06 and the repaired river mouth. Live/source discrepancy reached 1.353 m, requiring local adaptation. The remaining subtle shoulder edit ranges -0.1953 to +0.125 m over 156 vertices; the stream bed, crossing and protected junction ground are unchanged. The project layer limit is now nine so earlier layers remain separate.

Native readback verifies zero changes outside T07, exact prior-landform preservation and exact layer rollback/restoration. A 0.5 m contact check found zero changed wet classifications or shoreline/submerged terrain changes. Water mesh exports are byte-identical; materials and all 2,313 non-camera actor transforms are unchanged. Portable tests 7/7 and Unreal build passed. Matched strategy, opposite oblique and junction-detail renders, T07-only section D, adaptation evidence and reversal instructions are in [T07 evidence](artifacts/terrain-t07/README.md). All seven terrain layers are saved enabled. No other intervention started.

## T08 terrain-form refinement — 2026-09-18

Implemented only the eastern-road hump and surrounding ground on native additive layer `T08_EasternRoadHump`, preserving T01–T07. The profile was adapted to the actual shifted/widened road rather than the package's stale reference line. Current 5.730–6.270 m width settings and exact centreline XY are retained. Native terrain changes range -5.5703 to +1.3984 m over 2,526 vertices, with zero changes outside the true boundary.

110 existing spline segments were fitted vertically; maximum rendered road grade reduces from 25.638% to 8.050% (ground under live route: 7.995% final). Fully adjusted fitted tread clearance is 2.0–3.9 cm. Existing materials, assets and actor transforms are unchanged; a dense current-shoreline check reports zero contact/submerged changes. Combined terrain-and-road rollback and restoration passed. Portable tests 7/7 and Unreal build passed. The project now permits ten separate edit layers. Matched strategy/along-road renders, adapted profile E, controls, verification and coordinated reversal scripts are in [T08 evidence](artifacts/terrain-t08/README.md). All eight completed terrain edits are saved enabled. No other intervention started.

## T09 terrain-form refinement — 2026-09-18

Saved the village-to-bridge ramp on native additive layer `T09_VillageBridgeRamp`, preserving T01–T08 and fixed bridge connections. Current route and widened road were retained. Native terrain changes range -3.58594 to +0.46094 m over 827 vertices; 87 existing spline segments received vertical fitting, including local village junctions. Maximum main approach road grade reduces from 19.719% to 13.707%, retaining the short bridge-side transition. Between-endpoint contact was refined and checked densely. Combined rollback/restoration, prior terrain preservation, water contacts, 7/7 portable tests and Unreal build passed. Matched captures and reversal instructions: [T09 evidence](artifacts/terrain-t09/README.md).

## T10 terrain-form refinement — 2026-09-18

Saved only the crossing-approach adjustment on native additive layer `T10_DryCrossingApproach`, preserving T01–T09, current route/width, fixed crossing and water. Source-to-live discrepancy reaches 1.2265 m, so the isolated proposal was locally attenuated around current terrain and water contacts. Final edit: -0.21875 to +0.234375 m over 186 vertices; 25 approach splines follow the small displacement. The protected 22.669% road transition remains unchanged; changed approach segments remain below 3.815% grade. No new submersion or tread intersections were found. The protected core has pre-existing water-mesh overlap, which remains unchanged; an entirely dry crossing is not certified.

Exact native readback, T01–T09 preservation, combined terrain/road rollback and restoration, fixed crossing geometry, actor/material invariants and unchanged water export passed. Portable tests 7/7 and Unreal build passed. All ten interventions are saved enabled, with 12 separate layers including base and water. Matched comparisons, profile, crossing limitation and reversal: [T10 evidence](artifacts/terrain-t10/README.md). The final whole-map review has not begun.
