# Kusazuri01 implementation plan

## Goal
Create only the requested modular waist armor, fitted to the unchanged Manny and existing Kabuto, Dō and Sode. Preserve the editable Blender source and commit verified exports, imports and evidence.

## Architecture
Seven separated rigid hanging sections: narrow front center, paired front quarters, paired sides and paired rear panels. A separate belt overlaps the existing Dō hem. Existing Dō atlas is packed without new pixels. A local finish variant preserves the established Sode palette and adds indigo textile treatment. Runtime combines parts into one native-Manny skeletal mesh with three LODs and one material section. A stateless armor-only pose controller may use existing pelvis, spine_01 and thigh/twist bone channels to hinge individual sections; body/rest skeleton/animation assets are untouched.

## Spec
[User request](kusazuri01-request.md). Primary visual authority: `SourceArt/References/Samurai/Kusazuri01/kusazuri_01_reference_sheet.png`.

## Progress
- [x] Read project instructions and inspect existing source, fit dimensions, native rig and pipeline.
- [x] Build and inspect the seven-panel silhouette; user confirms the design is correct.
- [x] Revise the rejected finish: full Dō detail tiles, sparse aligned relief cords, physically braided obi and masked indigo woven texture. Actual revised renders were shown; human approval remains pending.
- [x] Establish saved-source export and three closed LODs; final tail/material revision passes44/44checks at147408/44210/15734triangles.
- [x] Verify geometry, normalized weights, rigid panel behavior, skeleton identity and body/Dō clearance in native clips and diagnostics.
- [x] Import `/Game/Art/Characters/Samurai/Kusazuri01/`; build and run portable tests; capture combined outfit in real Unreal rendering.
- [x] Compare upper armor with/without Kusazuri in identical 100/500 static review groups; document limits rather than full battle capacity.
- [x] Independent review, README, STATUS and evidence; commit only task-owned files.

## Decisions
- Existing Sode files were initially another task's untracked work. Its owner has now committed the final source/import as `037170b`, then a unity-build symbol repair as `8ff7bb2`. Preserve those assets and the Sode STATUS note.
- Work in this checkout: untracked Sode source and imported native assets are required and the user explicitly requests the current pipeline. Keep new files isolated.
- Reuse atlas and helper functions from committed Dō/Kabuto code. No ImageGen needed for this geometry-only task.
- All Unreal processes serialize; no heavy work overlaps measured performance intervals.

## Discoveries
- Manny is 1.80524m, pelvis 0.95897m, thigh origin 0.93543m, knee 0.50266m. Root retains .01 scale and local centimetres, 88 Blender bones/89 native reference bones.
- Dō hem starts at 1.015m, with lower radius about .184m x .146m, and -Y front in Blender.
- The new graph initially rebuilt thousands of times during primitive operators after adding the shared material. A process sample confirmed dependency-graph rebuild time; batched evaluated mesh merging restored the full source+two renders to about29s.
- Blender requires an unsandboxed launch on this host; sandboxed launch crashed before reading the file, successful escalated probe exited zero.

## User finish feedback and functional evidence
The user explicitly rejected the first surface quality as amateurish while confirming the design is correct. The material error was using plain lacquer tile0 instead of the established Dō lamella tiles8/9/13/14. The correction retains the silhouette and improves actual geometry/UVs, not a generated review image. The revised braided obi uses woven tile3 with a binary vertex-color mask so the panel lacing remains red. All source meshes carry ArmorTint white, with the global obi object black. The one local material variant reuses existing textures.

Initial 25-pose motion probe preserves panel rigidity and has no inversion; it is not a fit pass. Body-weight classification identified finger contact in stock unarmed locomotion, thigh lining contacts up to about8mm, and high-knee thigh contact up to27.3mm. Upper fixed attachment contact remains to be evaluated against the unchanged Dō. Quick reports remain failure evidence; final measurements require the revised source and export.

The production motion uses a .02-radian deadband and front-quarter opening normals that blend toward forward between 50° and 75° of sagittal hip flexion. This removed thigh contacts from all twenty quick native samples without introducing the attack clipping seen in a rejected ungated alternative. The belt's lower edge was raised to 1.009 m after its 16.37 mm high-knee contact was measured; the revised belt is clear. Obi height was also corrected. A high-knee diagnostic still has approximately 7 mm panel contact; full final-frame checks remain authoritative.

The updated Unreal build passed in 24.98 seconds after the separate Sode task repaired four colliding helper names in the shared unity build. Portable core tests passed 6/6 and tooling tests passed 67/67. Final source export validation, Unreal import/rendering and cost checks remain separate steps.

## Full sweep findings and corrections

The first full 372-pose sweep disproved clearance inferred from quick samples. Idle was leg-clear; walk had one lining contact, run eight leg-contact frames, and attack frame13 had up to15.09mm of lining penetration. These results and39captures are archived as `pre-lateral`. A sideways right-thigh lift was receiving too much forward-only hinge blending.

Bounded probes show that blending toward the actual horizontal thigh direction, with the existing50–75° sagittal gate multiplied by a15–35° lateral fade, clears the failing attack and run front-panel frames. A side-panel angle floor of.08times sagittal flexion clears the side lining. These formulas are now promoted in Python and C++; native regression tests changed from six failures to zero. A final full sweep is still required. The sole run32 leg contact came from the tassel tip, so the tail path has been shortened13mm; the belt/rings remain unchanged.

The initial finalized export passed44/44checks at147648/44282/15782triangles and correct official skeleton/color readback. Its LOD2 uses protected plate-island dissolve and separately triangulated obi collapse. The tail revision now has147408source triangles and awaits export refresh. A source underside view exposed a pale grazing-angle lining appearance; an albedo-only probe confirms the indigo color is correct, and material response is being checked before the refresh.

Unreal import and a real1280×720Metal close/detail render succeeded. The front bow is present and correctly oriented; native static readback places its vertices at positiveY18.00–20.58cm and preserves69252black/373692white color corners, no other colors. The earlier concern that it was behind the character was a visibility misreading; no orientation edit was made. Imported static counts matched all three source LODs. Importer fixes accommodate comments before the Sode HLSL tile declaration, the Desaturation unnamed input pin, and unavailable shader-resource texture lists underNullRHI by reading actual graph references. Dependencies remain unchanged.

## Validation
Commands and measured outputs will be retained under `artifacts/kusazuri01/`. NullRHI import is distinct from real Metal captures. Available native clips: idle, forward walk, forward jog (run alias), unarmed attack. Bow/crouch/knee lift are explicit diagnostic poses, not invented native clips.

## Handoff
Stop after Kusazuri01. Do not begin another component. Final report identifies exact source/import paths, counts, movements, cost, remaining clipping and one recommended next component.

## Final source freeze

Saved-source SHA is`cf7c0ec0578b7fe2aca7d1b30439c521e8cecc3e63d4f36b0c8820b31dc9eb9e`. The13mm tail shortening and tile12-only cloth response are included. All44source checks pass, with147408/44210/15734triangles. A fresh saved-source underside render confirms dark indigo padding; no source changes are pending. The full372pose sweep and final Unreal reimport/captures use this version.

## Final evidence

The frozen source passes 44/44 checks. The complete 372-pose sweep preserves rigidity without inversion; final native leg contact is confined to two run frames (shell .896 mm / lining 2.261 mm maximum). Extreme knee lift retains 6.425 mm shell contact; stock hand contact and shallow attachment contact are documented. Final maximum Dō signed-nearest outliers were checked against closed solids and are not demonstrated deep penetration.

Twenty actual Metal views and forty-eight source renders are verified. The final build, 67 tooling tests, 6 portable targets and all 21 Unreal tests pass. Reserved static comparisons record +3.63 ms at 100 figures and +3.72 ms at 500 figures; reversed single-character trials expose variation rather than a reliable speedup. Full evidence and remaining limitations are in `artifacts/kusazuri01/verification.md`. The historical discoveries above are superseded by these frozen results.
