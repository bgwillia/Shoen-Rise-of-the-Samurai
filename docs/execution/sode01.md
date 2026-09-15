# Sode01 paired component implementation

## Goal

Create, import, review and commit `Sode_L_01` and `Sode_R_01` using the supplied sheets and existing Manny/Kabuto/Dō standard. The user's quality follow-up retains the design direction and asks for a stronger finish matching the existing helmet and chest armor. The visual revision is complete with recorded source/runtime counts, imported assets and actual rendered checks. [Final evidence](../../artifacts/sode01/verification.md).

## Architecture

[Sode01.blend](../../SourceArt/Characters/Samurai/Sode01/Sode01.blend) remains the editable authority, with eight modular source regions per side. Each side exports one skeletal mesh with three LODs and one material section per LOD. Reduction targets are 60%, 22% and 7% of the evaluated source, with actual counts recorded after export.

Both shoulders share `M_Sode01`, which references the unchanged three Dō 2048×2048 atlas textures. Native Manny reference bones, body proportions and existing armor assets remain dependencies. Rigid panels use their corresponding upper-arm bone; suspension braids blend it with `spine_05` at the Dō strap.

The suspension controller copies the whole native pose, then controls only the Sode component's upper-arm transform. It filters axial twist and provides authored opening and lift. The C++ helper is `SodeSuspensionTarget` in [SodeReviewGameMode.cpp](../../game/Source/Shoen/Private/SodeReviewGameMode.cpp). The review is isolated from settlement/combat systems; production army equipment integration is outside this task.

## Spec

[Original user request](sode01-request.md); supplied sheets under `SourceArt/References/Samurai/Sode01/`; subsequent user feedback requesting improved visual quality. Reference priority is three-quarter silhouette, front, outer side, inner/back, construction, then decorative details.

## Current construction decisions

- Five overlapping rows, 22 crowned lamellae per row, with visible plate thickness and narrow rolled edges.
- Full Dō tiles 8, 9, 13 and 14 give each main face two short braided fastening tiers separated by lacquer. Sparse geometric ties on every fourth lamella reinforce only the upper tier and align with its atlas holes. The wavy red cord across the faces has been removed.
- A floral medallion conforms to the curved upper header; small fasteners and narrow side staples support the plate construction.
- Twisted suspension ties, wrapped knots and gathered tassels replace the coarse cord finish.
- Modeled quilt lobes, inset seams and leather piping develop the interior surface.
- `M_Sode01` applies the documented atlas tints, roughness bias `.08`, normal strength `.65` and specular `.30`, using existing Dō texture objects. [Exact shader settings](../../SourceArt/Characters/Samurai/Sode01/Textures/README.md).

## Progress

- [x] Read repository guidance, status, design package and existing armor pipeline.
- [x] Inspect both sheets, existing Dō fit and native Manny joints.
- [x] Implement the paired source, saved-source export, importer and isolated review tooling.
- [x] Establish numerical Blender/Unreal suspension reference tests and portable CLI validation.
- [x] Finish the quality revision and export its final source/runtime counts.
- [x] Revalidate current source, handedness, fixture preservation, weights, LODs and sampled pose clearance.
- [x] Import the revised material/meshes and inspect required Unreal views and motions serially.
- [x] Record the three-state incremental runtime comparison at identical settings.
- [x] Complete final checks, documentation and evidence; include this plan in the scoped asset commit.

## Preservation and workflow

The original one-pass request authorizes integrated work without separate subsystem approval milestones. Preserve unrelated working-tree changes. Dō and Manny became the committed dependency baseline at `6dbc613` during this task. Preserve the separate concurrent Kusazuri work and stage only Sode paths. Blender +X is anatomical left, −X right and −Y forward. Manny's native root scale `.01` is intentional.

`source` rebuilds procedural construction and replaces manual source edits. `export` reads the saved blend, regenerates runtime copies and checks source/fixture/rig/pose preservation. No new skeleton, body standard, armor variants, clothing or weapons are authorized.

## Validation and handoff

Required evidence includes source/runtime validation, actual geometry intersection sampling, Blender and Unreal visual inspection, native idle/walk/jog/attack, and diagnostic arm-raise and bow poses. There is no native bow clip. Build and portable checks remain separate from rendered evidence. The native suspension test compares 32 frozen targets across sixteen poses and checks exact lateral elevation.

Run one Unreal process at a time; keep builds and other heavy tasks outside timing captures. NullRHI import or automation does not measure rendering. Re-run the relevant export/import/visual gates for this quality revision. Final reporting must distinguish measured clearance, visible remaining defects, actual runtime counts and performance from human visual approval, which is pending.
