# Kusazuri01 — asset verification

## Visual quality and fit

The user's correction was to preserve the design and bring the finish up to the standard of Kabuto and Dō. The revised mesh uses Dō's detailed lamella atlas, aligned raised ties, crowned overlapping plates, narrow bindings, restrained chased brass and a physically braided indigo obi. The seven-leaf silhouette and proportions are retained. These are real Blender and Unreal assets; the review images are actual renders.

The skirt hangs below Dō's 1.015 m hem, with authored waist pivots at 1.006 m. A thin upper belt and obi support the panels. The original lower belt interfered with an extreme knee lift; its lower edge now ends at 1.009 m. The lining extends behind the attachment gap without restoring that rigid obstruction. Dō, Manny, Kabuto and Sode geometry remain unchanged.

The source and every runtime LOD pass neutral body clearance. The permitted Dō attachment overlap is confined to belt/obi/upper attachment regions between z .9895–1.030 m and checked against a 3 mm projected local depth limit. Observed maximum depth is approximately **1.690 / 1.755 / 1.634 mm** at LOD0/1/2. This deliberate shallow tuck is not a claim that every surface is disjoint. [Source validation](source-validation.json), [visual revision review](visual-review.md).

## Blender construction, counts and materials

Authoritative source: [Kusazuri01.blend](../../SourceArt/Characters/Samurai/Kusazuri01/Kusazuri01.blend). The `Kusazuri01_Source` collection contains **30 editable meshes**: seven hanging leaves, each with shell/lacing/trim/interior, plus the belt and global obi. The rear is split into left/right leaves to follow hip movement. Fit fixtures, runtime copies and review lights are in separate collections. The source retains Armature deformation modifiers; plate crown/thickness, cords and fittings are editable mesh geometry. Export applies simplification only to generated runtime copies.

| Representation | Triangles | Material sections |
| --- | ---: | ---: |
| Editable source | 147,408 | One shared material across 30 objects |
| Runtime LOD0 | 147,408 | 1 |
| Runtime LOD1 | 44,210 | 1 |
| Runtime LOD2 | 15,734 | 1 |

LOD1 uses a .30 collapse ratio. LOD2 uses a selective policy: retain every closed plate island and the lower hems; dissolve shallow shell/lining/belt face angles; simplify the obi separately; remove the repeated physical stitches but keep their texture detail. A global .035 reduction was rejected because it erased the lacquered shells. Final validation checks lacquer-atlas faces for every panel, closed topology, outward volume, finite unit corner normals, UVs, normalized weights and color masks. The export explicitly preserves editable source/fixture geometry, reference rig, weights, UVs and the saved pose. [Manifest and policies](../../SourceArt/Characters/Samurai/Kusazuri01/asset-manifest.json).

One opaque **M_Kusazuri01** material derives from final M_Sode01. It uses the existing three 2048² Dō BaseColor, Normal and ORM textures; **zero new texture images**. Indigo lining uses atlas tile 12, with a cloth-only metallic value of 0, roughness .90 and specular 0 to remove an excessive grazing sheen. An opaque binary `ArmorTint` vertex-color mask selects woven indigo for the obi while preserving red panel lacing. [Material details](../../SourceArt/Characters/Samurai/Kusazuri01/Textures/README.md).

## Rigging and animation

The asset uses the exact existing native Manny skeleton: 88 Blender bones plus the object root, matching 89 Unreal reference bones. The body's proportions, reference hierarchy and animations are unchanged. Each rigid leaf has one full-weight influence using existing spine/thigh/twist channels on the armor component; the belt and obi use pelvis.

**Equipping requires the supplied armor pose controller.** It copies the native pose into an armor-only instance of the same skeleton, then overrides seven rigid leaf transforms around their waist pivots. The center responds to the greater forward thigh flexion; each remaining panel responds to its corresponding leg. Front quarter opening normals blend toward the thigh's horizontal direction between 50° and 75° of sagittal flexion. That blend fades out as lateral direction increases from 15° to 35°, retaining the radial swing for sideways lifts. Side panels have a small opening floor of .08 times forward hip flexion. A .02-radian deadband and 90° cap bound opening. No physics, extra skeleton asset, plate stretching or body animation changes are used.

Native clips: idle, walk, forward jog (`run` alias), and unarmed attack. Nine separate diagnostic poses cover neutral, crouch, large forward step, knee lift, wide stance, combat stance, hip rotation, torso rotation and bow use. There is no native bow, mounted or crouch clip in the fixture.

The final sweep measures **372 poses: 363 native integer frames plus 9 diagnostics** on the frozen source. All leaves retain rigid transforms, with maximum pair-distance error .00101 mm, maximum all-vertex transform error .000481 mm, and zero inverted or collapsed triangles.

| Native clip | Frames | Frames with leg contact | Largest shell / lining estimate |
| --- | ---: | ---: | --- |
| Idle | 229 | 0 | 0 / 0 mm |
| Walk | 47 | 0 | 0 / 0 mm |
| Run (forward jog) | 55 | 2 | .896 / 2.261 mm |
| Unarmed attack | 32 | 0 | 0 / 0 mm |

The remaining run contacts occur at frame 31 (left front shell .896 mm, lining 2.261 mm) and frame 40 (right front shell .003 mm, lining 1.179 mm). The five earlier regression frames—walk frame 19, run frames 22/32/39 and attack frame 13—are now leg-clear. The extreme knee-lift diagnostic retains shell 6.425 mm / lining 6.094 mm estimated contact; belt and tassels clear the leg. The other eight diagnostics are body-clear. Stock unarmed hand motion still crosses the waist armor in idle/walk/run, with estimated maximum 11.22 mm in walking; body clips remain unchanged.

This is **not an all-clear motion result**. [Measured contacts and limitations](motion-contact-summary.md), [full JSON](motion-validation.json), [frozen hinge targets](hinge-reference-poses.json). Body regions come from dominant native skin influences. Integer-frame checks do not prove continuous or subframe clearance; signed nearest-surface depth estimates are not exact solid-Boolean measurements.

A separate [closed-island containment check](do-final-outlier-solid-containment.json) examined the largest Dō signed-nearest outlier in each native clip. All four reported points reproduce exactly and lie outside the candidate closed Dō solids, so the 9–17.5 mm signed-nearest values do not demonstrate solid penetration of that depth. Actual crossing triangles remain. Contained vertices sampled from those affected components measured 1.964 / 1.587 / 1.960 / 1.993 mm for idle/walk/run/attack, with the deepest points in Dō's lining. Eight ray-edge vote disagreements were resolved with closed-island solid-angle winding. This bounded check covers those outliers; it is not a global solid-clearance proof for every frame. [Reproducible probe](../../SourceArt/Characters/Samurai/Kusazuri01/Scripts/diagnose_do_contacts.py).

## Unreal assets and rendered views

Runtime export: [SK_Kusazuri01.fbx](../../SourceArt/Characters/Samurai/Kusazuri01/Exports/SK_Kusazuri01.fbx), with separate LOD1/LOD2 exports in the same folder. Target package: `/Game/Art/Characters/Samurai/Kusazuri01/`. It contains `SK_Kusazuri01`, `M_Kusazuri01`, the static review mesh and `Review/Kusazuri01_Review`. The isolated review fixture equips native Manny with existing Kabuto, Dō and both Sode pieces, retaining the Sode suspension controller.

The final [import readback](unreal-import.json) validates source SHA, all three LOD counts, 89 native reference bones, one material section per LOD, shared material texture graph references and the tile 12-only cloth response. Existing body, skeleton, animation and armor dependency hashes remain unchanged. This NullRHI import is separate from actual rendering.

**20 final real Metal captures** cover front/back/left/right, both three-quarter views, waist detail, overhead outfit and low-angle outfit, four advancing native clips, and seven diagnostic poses. They render at the actual **1280×720** viewport; the requested 1600×900 is not claimed. [Capture manifest with source and image hashes](final-captures.json), [waist detail](final-detail.png), [front](final-front.png), [back](final-back.png), [left](final-left.png), [right](final-right.png), [three-quarter](final-close.png), [run](final-run.png), [knee lift](final-knee-lift.png).

The first underside camera fell below the review floor and was rejected. Its corrected low-angle outfit view is valid, but Manny's legs obscure much of the lining. The overhead view is also a full outfit view; the isolated saved-source [underside](underside-final-cloth.png) and [top/interior](../../SourceArt/Characters/Samurai/Kusazuri01/Review/Captures/top-interior.png) provide direct lining evidence.

The source review additionally records 44 main views plus 4 contact close-ups, including separated construction, isolated top/underside, tactical distance and measured worst poses. [Main source capture manifest](capture-manifest.json), [all 48 image hashes and dimensions](final-capture-validation.json), [motion view inspection](motion-visual-review.md).

The native render batches are visual/attachment checks. Their frame timings overlap coordinated source rendering and are not used for the reserved cost comparison.

## Incremental performance

The reserved narrow comparison uses one advancing native-idle character and 100/500 static outfit groups, with identical cameras for existing upper armor versus upper armor plus Kusazuri. Actual 1280×720 Metal on Apple M1 Max / 32 GB, Development editor-game, no VSync, three-second warmup, 15-second single-character and 20-second crowd sample commands. All timing intervals are reserved from other coordinated heavy work. [Raw trials, timing distributions and commands](performance-runs.json).

| Static figures | Existing median frame / FPS | With Kusazuri median frame / FPS | Median increase |
| --- | --- | --- | --- |
| 100 | 10.428 ms / 95.9 | 14.062 ms / 71.1 | +3.634 ms (+34.8%) |
| 500 | 19.283 ms / 51.9 | 22.999 ms / 43.5 | +3.716 ms (+19.3%) |

Both groups rendered correctly, but the waist has a measurable cost. These single trials are a sanity check, not a stable production budget. Static groups do not measure skinning, animation, population simulation or combat capacity. Review-validation overhead remains; driver/thermal/background variation is not eliminated. Mesh-instance counts are not GPU draw-call measurements.

The first single-character pair was unexpectedly faster with Kusazuri (14.131→11.241 ms). A [reversed-order repeat](performance-close-repeat.json) measured existing 11.238 ms versus Kusazuri 10.951 ms, a −.287 ms difference. The existing-outfit median varied by 2.894 ms across trials, much more than the repeated difference. These short runs do not isolate a reliable single-character incremental cost, and no speedup is claimed.

At 100 figures, frame p95 increased 11.716→17.080 ms; at 500 it increased 24.685→30.049 ms. Isolated frame hitches remain: the 500-figure Kusazuri run reached 162.96 ms and the 100-figure baseline reached 145.50 ms. These runs do not establish their cause or certify smooth frame pacing. No further benchmark milestone or optimization was started.

## Verification and preservation

- **44/44** final source checks pass: [JSON](source-validation.json), [log](source-validation-cloth-final.log).
- Saved-source export passes: [log](source-export-cloth-final.log), [hashes](../../SourceArt/Characters/Samurai/Kusazuri01/FILES.sha).
- **67/67** tooling tests pass: [log](tooling-tests.log).
- **6/6** portable CTest targets pass: [log](core-tests.log).
- Final Unreal build, including corrected review camera, passes: [log](build.log), [result](build-result.json), [command](build-command.json).
- **21/21** complete Shoen Unreal tests pass, zero errors/warnings, including frozen Blender-to-Unreal hinge parity, Sode suspension, and accepted A/B gameplay regressions: [summary](unreal-tests-summary.json), [log](unreal-tests.log). This NullRHI suite is logic evidence only.

Final source SHA-256: `cf7c0ec0578b7fe2aca7d1b30439c521e8cecc3e63d4f36b0c8820b31dc9eb9e`.

The separate Sode task committed its final asset as `037170b` and the unity-build helper correction as `8ff7bb2`. This task preserves those assets and the existing gameplay, supplied design package and asset workbook. Files named `initial`, `quick`, `probe`, `r035`, `pre-lateral`, or `failed` are historical diagnosis, not final passes. [Independent code/hash review](review-code.md) found no remaining actionable defects. Earlier build failures are preserved separately from the passing final build.

## Limitations and pipeline assessment

The regular atlas pattern, ornament and knot are simpler than the reference illustration. The seven rigid leaves approximate suspension and do not flex like individual leather-laced courses. Extreme poses and stock unarmed hands can still contact the armor; final measured cases are listed above. Human approval of the revised finish is not claimed.

The modular approach continues to support editable construction, one-section runtime assets, shared textures and predictable motion without changing Manny or existing armor. Waist armor needs its own controlled suspension and clearance checks; ordinary thigh weighting or one rigid skirt would not reproduce the intended behavior. Production army equipment wiring and full animated-army performance are outside this asset task.

Recommended next component: **Kote_L_01 + Kote_R_01**. This task does not begin it.
