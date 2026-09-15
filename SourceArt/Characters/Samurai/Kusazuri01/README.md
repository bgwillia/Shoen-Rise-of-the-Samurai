# Kusazuri_01

Seven hanging waist-armor panels fitted beneath the existing Dō on the unchanged native Manny. This source follows the supplied reference and the user's finish correction: retain the accepted design and improve the surfaces to match Kabuto and Dō.

## Editable source

[Kusazuri01.blend](Kusazuri01.blend) is authoritative. `Kusazuri01_Source` retains 30 editable meshes: seven leaves with separate shell, lacing, trim and interior objects, plus the belt and braided obi. Blender +X is anatomical left, −Y is forward, and world dimensions are metres. Native Manny's .01 armature scale and local centimetres remain intentional.

| Hanging section | Native bone channel on the armor instance |
| --- | --- |
| Front_Center | spine_01 |
| Front_L / Front_R | thigh_l / thigh_r |
| Side_L / Side_R | thigh_twist_01_l / thigh_twist_01_r |
| Rear_L / Rear_R | thigh_twist_02_l / thigh_twist_02_r |
| Belt and obi | pelvis |

Each leaf has seven overlapping horizontal courses. Crowned lamellae have modeled thickness; the established Dō atlas supplies the small fastening and surface detail. Sparse raised ties align with the atlas. Narrow side bindings, chased fittings and a reinforced diamond-pattern hem support the shared design language. Indigo padded interiors close the underside. The obi has two braided cords, wrapped knots and gathered tassels.

The split rear pair and seven-leaf arrangement resolve inconsistencies among the reference sheet's views while preserving its front silhouette, flare and coverage. No existing armor or body geometry is remodeled.

## Fit and materials

The panel hinges sit at 1.006 m, directly below the Dō hem. The upper belt tucks under that hem. Its lower edge and obi height were revised after a high-knee clearance check. Source fixtures contain the existing Manny, Kabuto, Dō and final Sode pair for inspection.

One opaque material, `M_Kusazuri01`, derives from the final `M_Sode01` finish. It references the same three Dō 2048×2048 BaseColor, Normal and ORM images; no new texture pixels are allocated. Tile 12 is tinted indigo for the lining. The `ArmorTint` vertex-color attribute is white on the panels and black on the global obi, selecting woven indigo cord while keeping the panel lacing red. See [material details](Textures/README.md).

## Runtime and motion

The editable source has **147,408 triangles**. Runtime copies combine it into one skeletal mesh with **147,408 / 44,210 / 15,734 triangles** across three LODs and one material section per LOD. The distant LOD preserves each closed lamellar shell and the lower hems, simplifies the lining and obi, and removes repeated physical stitches while retaining their atlas detail. A blanket reduction that erased the shells was rejected.

The native reference hierarchy remains unchanged: 88 Blender bones plus the armature object root, matching 89 Unreal reference bones. Each rigid region has one full-weight influence. The body animation remains untouched.

**The supplied armor pose controller is required when equipping the asset.** A plain body pose follower would turn the waist leaves with individual thigh and twist bones incorrectly. The controller copies the native pose into an armor-only instance of that same skeleton, then sets seven rigid leaf transforms around their waist pivots. The independent belt follows the pelvis. There is no extra skeleton asset, physics simulation, lag or rubber bending within a leaf.

Forward thigh movement opens the corresponding panels. Front quarter panels blend toward the thigh's horizontal direction above 50° of sagittal hip flexion, reaching full influence at 75°. That influence fades out as lateral direction increases from 15° to 35°, preserving the radial swing during sideways attack motion. Side panels have a small opening floor equal to .08 of forward hip flexion to clear their leading edges. All leaves use a .02-radian deadband and a 90° opening limit. The center responds to the greater forward movement of either leg.

- Blender controller: [kusazuri_motion.py](Scripts/kusazuri_motion.py).
- Unreal implementation: [KusazuriHinges.h](../../../../game/Source/Shoen/Private/KusazuriHinges.h).
- Combined outfit fixture: [KusazuriReviewGameMode.cpp](../../../../game/Source/Shoen/Private/KusazuriReviewGameMode.cpp). It also preserves the existing Sode suspension behavior.

## Reproduction

From the repository root:

```sh
python3 tools/kusazuri.py export
python3 tools/kusazuri.py validate
python3 tools/dev.py build
python3 tools/kusazuri.py import
python3 tools/kusazuri.py review --camera close --animation walk
python3 tools/kusazuri.py review --camera rear --pose wide-step
python3 tools/kusazuri.py review --camera tactical --count 100 --mode existing --seconds 20
python3 tools/kusazuri.py review --camera tactical --count 100 --mode kusazuri --seconds 20
```

`source` rebuilds the procedural design and replaces manual source edits. Save manual Blender changes and run `export` to regenerate runtime copies from that saved file. Export checks that the editable source, fixtures, rig and saved pose survive unchanged.

The import writes only `/Game/Art/Characters/Samurai/Kusazuri01/`, including `SK_Kusazuri01`, `M_Kusazuri01`, static review copies and `Review/Kusazuri01_Review`. Manny, its skeleton and animations, Kabuto, Dō and Sode packages are read-only dependencies checked by hashes. Use one Unreal process at a time in this checkout. Stop other heavy work during measured comparisons.

`close` and `rear` are three-quarter cameras; straight front/back/left/right, detail, top and interior views are also available. Native animations are idle, walk, jog (`run`) and unarmed attack. Bow, crouch, knee lift and other diagnostic poses are explicitly synthetic checks. `--seconds 0` leaves the fixture open.

Full source review:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --threads 2 --python-exit-code 1 --python SourceArt/Characters/Samurai/Kusazuri01/Scripts/review_kusazuri.py -- --render
```

## Evidence and limitations

[Verification report](../../../../artifacts/kusazuri01/verification.md) records the final counts, import, rendered views, motion contact measurements and incremental cost. [asset-manifest.json](asset-manifest.json) records export counts, hashes and source preservation.

This remains a prototype armor fixture. Seven rigid leaves approximate suspension; they do not simulate flexible lamellar courses or secondary cloth motion. The final 372-pose sweep found no leg contact in idle, walk or attack. Two run frames retain shallow contact (shell up to .896 mm, lining 2.261 mm); the extreme knee lift retains approximately 6.425 mm shell contact. Stock unarmed hand motion still enters the skirt. All panels remain rigid without inversion. Bow review uses a diagnostic pose because no native bow clip is supplied. Static 100/500 outfit groups measure a narrow rendering comparison, not animated armies or combat capacity. Production army equipment integration is outside this asset task.

Recommended next component: **Kote_L_01 + Kote_R_01**. It has not been started by this task.
