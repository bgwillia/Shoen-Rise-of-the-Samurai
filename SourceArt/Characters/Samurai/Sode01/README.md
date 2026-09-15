# Sode_L_01 + Sode_R_01

Matching modular shoulder armor for SHŌEN, fitted to the existing Manny, Kabuto01 and Dō01. This revision follows the user's visual-quality feedback: retain the reference design and improve the finish to match the established armor set. The revised source, import and rendered checks are complete; [verification and captures](../../../../artifacts/sode01/verification.md) record the evidence and remaining limits.

## Editable source and construction

[Sode01.blend](Sode01.blend) is the editable source. Blender +X is anatomical left (`Sode_L_01`); −X is anatomical right (`Sode_R_01`); −Y is forward. Each side uses its corresponding native Manny bones.

`Sode01_Source` retains eight construction regions per side: `MainPlateRows`, `LowerEdgeRow`, `UpperAttachment`, `Lacing`, `InteriorPadding`, `Bindings`, `Fittings` and `Suspension`.

- Five overlapping courses contain **22 lamellae per row**, with crowned faces, visible thickness and narrow rolled edges.
- Main faces use the full Dō atlas tiles 8, 9, 13 and 14, with two short braided fastening tiers separated by lacquer. Sparse geometric ties on every fourth lamella reinforce only the upper tier and align with the atlas fastening holes. The continuous wavy red face cord has been removed.
- The raised forward tab carries a layered floral medallion that follows the header curvature. Small peened fasteners and narrow side staples support the construction.
- Twisted suspension ties, compact wrapped knots and gathered tassel ends provide local relief.
- Interior padding has modeled quilted lobes, inset seams and leather piping.

Existing Manny, Kabuto and Dō objects remain fit fixtures. Manny's native root scale of `.01` and local centimetre mesh/bone coordinates are intentional. Hidden export copies live in `Sode01_Runtime`.

## Materials and runtime geometry

Both sides share **`M_Sode01`**, which references the existing three Dō 2048×2048 BaseColor, Normal and ORM textures. It applies restrained atlas-region color multipliers, a `.08` roughness bias and `.30` specular. The Dō material and texture assets are read-only dependencies; no new texture images are allocated. See [texture and shader details](Textures/README.md).

Each side combines into one skeletal runtime mesh with one material section per LOD. LOD0, LOD1 and LOD2 target **60%, 22% and 7% of the evaluated source triangles**, respectively. The pair totals **120,196 source triangles** and **72,116 / 26,388 / 7,976 runtime triangles**. The export writes counts and hashes to [asset-manifest.json](asset-manifest.json); Unreal import and rendered mesh inventory provide separate readback.

## Attachment and motion

Rigid panel regions use full weight on `upperarm_l` or `upperarm_r`. Only the suspension braids blend between `spine_05` at the Dō strap and the corresponding upper arm. **Equipping these assets requires the supplied suspension controller.**

The controller copies the complete native pose into each Sode component, refreshes it, and overrides that side's upper-arm transform. It removes axial twist, follows arm swing, and adds controlled opening and lift for lateral elevation. The existing body pose, reference skeleton, Dō follower and Kabuto head attachment remain separate.

- Blender: [sode_motion.py](Scripts/sode_motion.py), used by [measure_sode_poses.py](Scripts/measure_sode_poses.py).
- Unreal: `SodeSuspensionTarget` and `ASodeReviewGameMode` in [SodeReviewGameMode.cpp](../../../../game/Source/Shoen/Private/SodeReviewGameMode.cpp).
- [Runtime notes](Runtime.md) describe the pose update, numerical reference tests and reporting limits.

Review motions include native idle, walk, jog (`run` alias) and unarmed attack. Raised-arm, forward-arm and bow-use checks are diagnostic poses; no native bow clip or weapon is supplied. Bone agreement and import success do not establish surface clearance. Sixteen source pose samples preserve rigid shape and clear rigid panels; flexible suspension contacts remain in bow, jog and attack samples. See the verification report for limits.

## Unreal review and commands

The import targets `/Game/Art/Characters/Samurai/Sode01/`: `SK_Sode_L_01`, `SK_Sode_R_01`, shared `M_Sode01`, and static review copies plus `Sode01_Review` under `Review/`.

The review equips one native `SKM_Manny_Simple` with Kabuto, Dō and both shoulders. It is an isolated art fixture; production army equipment integration is outside this task.

From the repository root:

```sh
python3 tools/sode.py export
python3 tools/sode.py validate
python3 tools/dev.py build
python3 tools/sode.py import
python3 tools/sode.py review --mode sode --camera close --animation idle
python3 tools/sode.py review --mode sode --camera back --animation walk
python3 tools/sode.py review --mode sode --camera close --pose bow
```

`close` and `rear` provide three-quarter views; `front`, `back`, `left`, `right`, `detail` and `tactical` provide the other review cameras. `--seconds 0` leaves the review open. Comparison modes are `mannequin`, `armor` (Kabuto + Dō) and `sode`. Use one Unreal process at a time and stop other heavy work during timing captures.

`source` rebuilds the procedural design and replaces manual source edits. Save manual Blender changes, then use `export` to rebuild runtime copies from that saved source. Export checks preservation of editable geometry, fixtures, rig and saved pose.

Functional Blender review:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python-exit-code 1 --python SourceArt/Characters/Samurai/Sode01/Scripts/measure_sode_poses.py -- --controlled --render
/Applications/Blender.app/Contents/MacOS/Blender --background --python-exit-code 1 --python SourceArt/Characters/Samurai/Sode01/Scripts/render_sode.py
```

The [final evidence](../../../../artifacts/sode01/verification.md) includes counts, sampled clipping, fourteen Unreal views/motions and the basic incremental runtime cost. Human visual approval is pending. **Kusazuri** is recommended next and is already being pursued in the user’s separate task.
