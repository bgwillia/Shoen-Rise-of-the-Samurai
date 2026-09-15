# Dō 01 production plan

Scope: one torso armor asset following [the brief](../../docs/execution/do01-request.md). The user's subsequent instruction replaces the original custom fit mannequin with Epic's official Unreal Manny. Use the native Manny skeleton and existing template animations as the new character fit standard. Preserve the approved Kabuto geometry and existing gameplay.

1. Measure actual torso and bone dimensions; inspect all supplied reference views and available prototype clips.
2. Build separately editable overlapping front/back/side rows, upper chest, shoulder straps, edge bindings, lacing and lining. Review silhouette and fit in actual Blender renders before surface detailing.
3. Reuse Kabuto material-family bases in one 2K Dō atlas. Use physical row layering and representative cord geometry; smaller lamella grooves, holes, stitches and decorative engraving belong in textures.
4. Weight rigid plate islands consistently to Manny spine bones, with controlled transition at shoulders and row overlaps. Inspect neutral, forward/raised arms, bend/turn, native idle/walk/jog/attack. Record any diagnostic substitutes explicitly.
5. Export saved source to combined skeletal runtime plus distance LODs and static review geometry. Import on the existing Unreal skeleton; verify actual rendered combined Kabuto/Dō fit and movement, then short 100/500/1,000 comparisons and a bounded skeletal-cost probe if practical.
6. Save captures and concise evidence, record counts/materials/weights/limits, run appropriate portable/build checks, commit only Dō files and short STATUS note. Recommend one next component, then stop.

Main files: SourceArt/Characters/Samurai/Do01/{Do01.blend,Scripts/,Textures/,Exports/,README.md}; game/Content/Art/Characters/Samurai/Do01/; new opt-in DoReviewGameMode and tools/do.py; artifacts/do01/.

Finish revision: preserve the approved Dō design, improve lacquer and woven cord detail, give bronze ornaments real raised construction, and replace thin metallic row wires with rolled black bindings and restrained brass edges. New flat material sources are generated with ImageGen and assembled into the actual game atlas; all asset review images must be actual Blender or Unreal renders.
