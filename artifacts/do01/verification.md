# Dō01 — official Manny fit and rendered evidence

Scope: one torso armor component, following [the production brief](../../docs/execution/do01-request.md) and the user's later instruction to replace the custom fit body with Epic's official Manny. The existing strategy prototype remains intact. This is an asset prototype with documented motion limitations, not user visual approval or a full-army performance certification.

## Result and visual corrections

The editable [Do01.blend](../../SourceArt/Characters/Samurai/Do01/Do01.blend) has ten source objects and one 2K material atlas. Six physical lamellar rows, woven red cord detail, raised fittings and restrained brass edging preserve the requested design. A denser lining profile removed the brown strip protruding through the rear waist. Smooth chest/clavicle strap weights reduced the sharp folds in the stock attack.

[Blender hero](../../SourceArt/Characters/Samurai/Do01/Review/Captures/blender-hero.png), [front](../../SourceArt/Characters/Samurai/Do01/Review/Captures/blender-front.png), [back](../../SourceArt/Characters/Samurai/Do01/Review/Captures/blender-rear.png), [left](../../SourceArt/Characters/Samurai/Do01/Review/Captures/blender-left.png), [right](../../SourceArt/Characters/Samurai/Do01/Review/Captures/blender-right.png), [interior](../../SourceArt/Characters/Samurai/Do01/Review/Captures/blender-interior.png). These are actual source renders. The generated flat material sources are identified in the asset README; no generated beauty image substitutes for asset evidence.

The finish and ornamentation remain simpler and more regular than the reference. Broad bib reflections can appear pale under Blender studio lighting. [Independent visual review](visual-review.md).

## Geometry, source preservation and import

| Representation | Triangles | Material slots / sections |
| --- | ---: | --- |
| Editable source, ten objects | 81,392 | One shared material |
| Combined runtime LOD0 | 81,392 | 1 / 1 |
| Runtime LOD1 | 32,556 | 1 / 1 |
| Runtime LOD2 | 5,504 | 1 / 1 |

[Source validation](source-validation.json) passes: closed geometry, finite data, no zero-area or duplicate faces, valid atlas UVs, packed 2K textures and normalized armor weights with at most four influences. The editable source retains armature modifiers; constructed thickness is applied geometry. Export reads the saved source and verifies it did not change editable geometry, weights or fit fixtures.

Manny is the original `SKM_Manny_Simple` from the installed Epic UE5.8 template: 1.80524m tall, 92,178 LOD0 triangles, two native materials. Source geometry, topology, world rest bones and the 89-bone native hierarchy are preserved. Blender represents the root with its .01-scale armature object plus 88 bones; data remains in centimetres, world placement in metres. [Provenance](../../SourceArt/Characters/Mannequins/Manny/README.md), [original package inventory](manny-template-files.json), [native export validation](manny-unreal-source.json), [FBX roundtrip](manny-roundtrip-probe.json).

`/Game/Art/Characters/Samurai/Do01/SK_Do01` reuses `/Game/Characters/Mannequins/Meshes/SK_Mannequin`. The imported skeleton hierarchy matches; reference-transform comparison permits only .01cm translation, .0001 scale and .000001 quaternion-dot error to account for FBX precision. Native Manny packages are not resaved. [Import report](unreal-import.json). Runtime follows Manny's pose; Kabuto remains a rigid head attachment.

Approved `Kabuto01.blend` SHA256 remains `8e7a80e3e36c6b2acbd19fa0385d49da476140864370e53ea6f6c85d4f3f45f1`; its geometry and Unreal packages were not remodeled.

M_Do01 is opaque, single-sided, with sRGB BaseColor and linear Normal/ORM textures. The first NullRHI import produced gray fallback materials in the actual game. A separate real-Metal material preflight compiled the required shader permutations and verified native Manny material files stayed unchanged. [Material report](material-compilation.json), [preserved failed capture](iterations/first-unreal/README.md). Imported mesh validity alone was not treated as material-rendering evidence.

## Motion and remaining contact

[Pose samples](pose-review.json) use native Epic idle, forward walk, forward jog and unarmed attack. `A_Run` is the export alias for the existing jog. Temporary review copies remove root motion for stationary comparison; original clips remain unchanged. Diagnostic poses are temporary bone rotations, not a new animation library. No existing bow-draw clip was available.

Neutral, modest raised arms, 25° torso turn, 20° bend and 32° head turn have zero measured body/armor and helmet/armor surface intersections. Forward arms still produce 488 body/armor triangle-pair intersections around the bib/straps. Stock idle/walk/jog/attack retain contact during parts of their cycles. Jog has zero helmet/armor intersections in the three sampled frames after the strap correction; attack retains 826–1,123 helmet/armor pairs and 193–2,989 body/armor pairs.

These counts are intersecting triangle pairs, not penetration depth, area or visible severity. The worst [attack20](../../SourceArt/Characters/Samurai/Do01/Review/Captures/stress-a_attack-20.png), [attack28](../../SourceArt/Characters/Samurai/Do01/Review/Captures/stress-a_attack-28.png) and [jog23](../../SourceArt/Characters/Samurai/Do01/Review/Captures/stress-a_run-23.png) are retained. Sharp strap folding is reduced, but pale shoulder contact beneath the helmet guards remains during attack. Crossing arms can obscure contact. This asset is not certified clipping-free for arbitrary stock unarmed animations.

## Actual Unreal review

Fourteen real Metal captures passed the CLI's technical checks at **1280×720 actual viewport size** (the command requested 1600×900). [Summary](rendered-review-summary.json). All four native clips advanced; maximum armor/body bone-position disagreement was 0cm, rotation disagreement 0.00279°, and world-scale error below 0.000001. These checks confirm attachment and pose following, not surface clearance.

[3/4 neutral](unreal-neutral.png), [front](unreal-front.png), [back](unreal-rear.png), [left](unreal-left.png), [right](unreal-right.png); [idle](unreal-idle.png), [walk](unreal-walk.png), [jog](unreal-run.png), [attack](unreal-attack.png); [arms forward](unreal-arms-forward.png), [raised arms](unreal-arms-raised.png), [turn](unreal-turn.png), [bend](unreal-bend.png), [head turn](unreal-head.png). Each image has a same-stem JSON report, per-frame CSV and exact command record.

The final Unreal views show the actual dark lacquer/red cord/brass material and Epic's native Manny materials. Shoulder and neck openings remain readable; armor keeps its layered shape during the captured motions. Remaining stock-animation surface contact is described above and in the stress views rather than hidden behind successful transform checks.

Native roundtrip and early ring/geometry inspection reports include one-off diagnostics. Normal source, export, validation, import, material compilation and review workflows are preserved as production scripts and do not depend on those temporary diagnostic scripts.

## Incremental asset cost

Actual Mac Metal, UE5.8.2 Development editor game, Apple M1 Max / 32GB, **1280×720**, fixed 110m camera at 60° elevation, 55° horizontal FOV. Each run warms for 3 seconds and samples 12 seconds with shadows. Runs are sequential, with no concurrent Blender rendering, builds or heavy tests. Static figures use instanced meshes grouped by 100; generated static Manny LODs are review approximations, not edits to native skeletal Manny.

| Figures / representation | Manny FPS | + Kabuto FPS | + Dō FPS | Added Dō median frame ms |
| --- | ---: | ---: | ---: | ---: |
| 100 / static | 60.2 | 59.1 | 58.6 | +0.14 |
| 500 / static | 46.2 | 40.2 | 36.4 | +2.65 |
| 1,000 / static | 35.4 | 30.6 | 28.5 | +2.49 |
| 100 / skeletal | 53.3 | 53.6 | 55.9 | -0.76 |

| Full outfit run | Frame p95 / worst ms | Median game / GPU ms | Peak process GiB |
| --- | ---: | ---: | ---: |
| 100 static | 23.22 / 96.29 | 1.11 / 16.63 | 2.97 |
| 500 static | 34.88 / 213.48 | 1.02 / 26.54 | 3.01 |
| 1,000 static | 49.65 / 61.92 | 1.02 / 34.57 | 3.03 |
| 100 skeletal | 52.66 / 225.67 | 6.28 / 16.85 | 3.58 |

[All measurements and deltas](cost-summary.json). Tactical images: [100](cost-static-100-armor.png), [500](cost-static-500-armor.png), [1,000](cost-static-1000-armor.png), [100 animated](cost-skeletal-100-armor.png). Every source report has exact commands and per-frame CSV samples.

The Dō adds measurable rendering cost. At 1,000 static figures the full outfit is below 30 median FPS on this machine; these settings are not established as a suitable full-battlefield budget. The single-run deltas vary with LOD selection, frame scheduling and shadow cost, so they are approximate rather than a linear per-soldier cost.

The animated 100 run has a negative median Dō delta amid substantial frame-time spikes; that is measurement variability, not evidence that adding armor improves speed. Its full-outfit interval average is 42.95 FPS despite a 55.9 median, with 52.66ms p95 frames. This short probe cannot isolate a reliable added skinning cost.

Static crowds do not measure skinning. The 100-person skeletal probe uses actual native walk animation, body skinning and armor pose following, and includes review-validation CPU overhead. It is not a 1,000-person animated battle or a combat/population simulation benchmark. Mesh LOD inventory does not identify the selected GPU LOD. Draw-call and primitive counters were unavailable and are recorded as null, not estimated from material sections. Peak process memory includes the editor and assets; it is not GPU memory or isolated per-armor allocation.

## Software checks

- Portable CMake/core suite: 6/6 passed, 13.63 seconds. No DomainCore or combat changes in this task.
- Unreal Development editor build after review-code changes: succeeded, 15.73 seconds.
- Final Blender export and source validation: passed.
- Final Unreal import and real-device material preflight: passed.
- Python syntax checks: passed for the production scripts and CLI.

These software checks are separate from actual rendered review and timing evidence below.

## Reproduction

    python3 tools/do.py export
    python3 tools/do.py validate
    python3 tools/dev.py build
    python3 tools/do.py import
    python3 tools/do.py materials
    python3 tools/do.py review --camera close --animation idle
    python3 tools/do.py review --camera tactical --count 1000 --mode armor --seconds 12
    python3 tools/do.py review --camera tactical --count 100 --crowd skeletal --animation walk --mode armor --seconds 12

Run one Unreal process at a time. No simultaneous Blender renders, builds or heavy tests during cost measurements. `tools/do.py source` intentionally regenerates the procedural design and should not be used to preserve later manual Blender edits; export operates on the saved file.
