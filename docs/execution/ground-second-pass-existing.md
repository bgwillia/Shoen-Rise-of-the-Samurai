# Existing-material fork and river refinement — 2026-09-20

## Goal
Apply only W01/W02, R01/R02, R04/R05, R06/R07, R09/R10, R12/R13 and R15/R16 from the user's SHOEN_Ground_Second_Pass_Design.zip. No M9 placements or geometry edits.

## Architecture
Reuse the live M_VillageEntrance_ConnectedRoad composite and its existing M2/M4/M5/M6 colour, normal and roughness branches. A world-XY coverage texture resolves the requested ordered mixtures over the unchanged composite. No raised mesh or new surface material family.

## Spec
The package README, placement.json and transition studies are authoritative. Explicit cubic Beziers are sampled at <=4 cm intervals; nearest-boundary variable widths control inward smoothstep fades. World centimetres become metres with XY*.01. Atlas rows increase Y and columns X. All source protection shapes and the exported live water footprint with 1.2 m collar are excluded. Visible solid contacts are guarded. The current road-mask branch adds live tread/shoulder protection.

## Progress
COMPLETE — all 14 selected IDs applied, reviewed and saved. Live graph, scene inventory, original material package and matched camera specifications retained under artifacts/ground-second-pass-existing. Initial inspection found no existing second-pass nodes; older road joins, material refinements and terrain work are retained. Fork first, followed by local river pairs in requested order.

## Decisions
Store coverage only, never diagram albedo. Four atlas channels encode M2/M4/M5/M6, with residual baseline weight. Cubic outlines are maximum limits. A 0.12 m interior reserve prevents bilinear sampling leakage; protected contacts have a 0.18 m reserve, a 0.75 m initial fade and a final 3 m smooth approach. River vegetation additionally recedes from the protected water collar by 1.5 m with a 4 m smooth approach, after close views exposed disconnected green bank slivers. These adaptations only reduce influence inside the supplied maximum limits. Material texture pixels remain unmodified. No source gameplay changes or unrelated staging.

## Discoveries
The local editor bridge was unavailable. A recovered bridge initially retried long shader operations at its 10-second timeout, causing duplicate captures and an editor exit. Recovered using the saved map, live graph comparison, a single file-driven runner and no API retries for edits. Capture artifacts from interrupted attempts are not final evidence unless recaptured and reviewed.

## Validation
Passed: 7/7 portable tests; Unreal editor build; 24 matching before/after camera pairs at overview/strategy/close distances; zero active mask pixels beyond the cubic limits or within source exclusions; normalized coverage and unchanged earlier groups; all 2,404 live actors retained without authored transform changes; all 84 original custom nodes unchanged, exactly five pass nodes. Targeted material and final coverage texture saves succeeded. The saved map package is byte-identical to its pre-pass backup. See artifacts/ground-second-pass-existing/README.md and verification JSON files.

## Handoff
Complete this pass only. M9 sediment additions and all pond/hill/grass-age treatments remain outside scope.

## Remaining visual limits
Residual gravel beyond the maximum envelopes and inside protected bank/road footprints remains, including the upper R15 shoulder. Existing gravel repetition is unchanged. No M9 was added.

## User-requested edge revision — 2026-09-20
The user flagged sharp fork/bridge cuts and river grass tips. Smoothed the existing coverage atlas locally for W01/W02, R01/R02, R04/R05, R06/R07, R09/R10, R12/R13 and R15; R16 retained exactly. This explicit revision widens blends beyond the original narrow feather settings where visually needed, without expanding the prior coverage footprint. R12/R13 uses a tighter smoothing distance to preserve green tips. No graph, terrain, water, actor or gameplay changes. Saved and verified; 27 matching before/after views (including bridge ramp detail) are indexed in artifacts/ground-edge-smoothing/README.md. Original pass images remain archived.

## Bridge corner follow-up — 2026-09-20
User feedback on the edge revision requested tighter coverage at the R04/R05 right corner and softer bridge-adjacent grass. Restored stronger local reclamation at the corner with a narrower blend, while smoothing current bridge-contact coverage separately. Saved the coverage texture; all other treatment pixels remain identical. Verified 12 matching camera pairs, unchanged map/material graph packages and all 2,404 actors. Evidence: `artifacts/bridge-ground-tightening/README.md`.

## Pond-only follow-up — 2026-09-20

P01/P02 then P04/P05 are saved and visually inspected. P03 remains deferred to M9. The existing composite reuses M3/M5/M6 via five uniquely tagged pond coverage nodes and a local coverage texture; all 205 original graph nodes and the current fork/river atlas are preserved. No new surface materials, geometry, foliage, terrain or water-shader changes.

The wet-contact exclusion was locally fitted from current Unreal overhead renders within the native lake/terrain intersection, retaining a 1.2 m collar. Native lake outlines include translucent dry shore and were too conservative by themselves. Inward tip attenuation, reduced detached damp tails and separate endpoint tapers remove the largest visible cuts. P04's broad landward fades were locally tightened from 5–7 m to 2.5–3.5 m, smoothly transitioning to its narrow widths, to reduce an outer gravel strip. All changes stay inside the supplied cubic treatment limits; proportions and priorities are retained.

Evidence: `artifacts/pond-ground-refinement/README.md`, with 18 matching actual Unreal overhead/strategy/close camera pairs. Final checks confirm unchanged terrain height readback, map package, water assets, 2,404 actor transforms, original graph nodes and original fork/river atlas. Targeted material and coverage saves returned true. Portable tests 7/7 and Unreal build passed. The translucent wet-contact fit is approximate; gravel/sediment outside the four envelopes remains. No other treatment started.

## Five M9 placements — 2026-09-20

R03/R08/R11/R14/P03 are saved using the live-verified completed M_M9_FineSandyAlluvium asset's existing texture, metre scale and shader expressions. Explicit cubic boundaries, inward widths, priorities and specified mixtures are retained; colour, normal and roughness coverage fade together. R08 uses a locally fitted visible wet edge because the river mesh's transparent fringe extends over dry gravel. P03 remains a small pocket clipped by the verified pond shoreline collar. No new surface materials, geometry, foliage or earlier treatment reapplication.

15 matching before/after camera pairs, five metre-scale details and 150 rendered pan/zoom samples were inspected. All 2,404 actors, terrain height readback, original 210 graph nodes, prior coverage textures and completed M9 packages remain unchanged. Portable tests 7/7 and Unreal build passed. Evidence and local adaptations: `artifacts/m9-placements/README.md`. Existing gravel repetition and pond-edge faceting remain. Stop after these five IDs.

## M9 tip and P03 geometry revision — 2026-09-20

User feedback requested softer river-deposit tips and actual bank smoothing at P03. Saved locally softened R03/R08/R11/R14 coverage without expansion, and the reversible P03_BankSmoothing landscape layer. It modifies 163 local dry-bank vertices by −0.625..+0.50 m; submerged vertices, water geometry/level, all actor transforms and the current 242-node material graph are unchanged. P03's material coverage is unchanged. Small visible shallow-contact changes arise from the explicitly requested physical grading. Updated comparisons, exact height readback, successful saves, 7/7 portable tests and Unreal build evidence: `artifacts/m9-softening/README.md`.

### P03 waterline notch follow-up — 2026-09-20

Rounded the shallow terrain contact across the waterline in the existing P03_BankSmoothing layer after the user's marked screenshot. The accepted upper-bank smoothing and all five M9 material placements are preserved. 96 vertices changed locally (-9.4cm to +29.7cm); all other vertices remain exact. Water spline/level, actor transforms and material graphs are unchanged. Saved map, matching rendered comparisons and movement captures, exact height verification, 7/7 portable tests and successful Unreal build are recorded in `artifacts/p03-contact-smoothing/`.

## Left pond organic correction — 2026-09-20

User feedback rejected the left pond's inorganic patterns. Saved a local coverage-only correction that also softens the older angular gravel contacts around that pond, beyond the earlier P01/P02 envelopes. Replaced the hard rim with unequal variable-width coarse sectors, softened green transitions and reduced the damp stripe to a small pocket. No M9 addition. The right pond's pixels, original fork/river atlas, material graph package, map, water and all 2,404 actor transforms remain unchanged. Nine matching rendered camera pairs and save verification are in `artifacts/left-pond-organic-refinement/README.md`; final views are in `after-v2/`. The prior pond images remain archived.
