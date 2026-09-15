We are continuing the modular samurai armor pipeline for **SHŌEN**.

For this task, create **both shoulder armor pieces**:

- `Sode_L_01`
- `Sode_R_01`

These are the **left and right samurai shoulder armor components**.

This task should be completed in **one pass**, because the two shoulder pieces must match each other and match the existing armor set.

The shoulder armor must visually and structurally match the already established samurai equipment, especially:

- `Kabuto_01`
- `Do_01`

Do not create the full character.
Do not create new helmet/chest armor variants.
Do not create sleeves, waist armor, shin armor, weapons, or clothing.
This task is for the two shoulder armor components only.

---

# 1. REFERENCES

Use the supplied reference sheets as the primary design targets for the two shoulder armor pieces.

Reference images:

- ``
- ``

These correspond to:
- `Sode_R_01`
- `Sode_L_01`

Inspect all visible views and details before modeling.

The reference sheets include:
- front
- back
- outer side
- inner side
- 3/4 front
- 3/4 rear
- mannequin fit views
- detail closeups
- exploded construction
- materials palette
- design notes

Treat the sheets as the authoritative visual target for this task.

If small contradictions exist between image panels, prioritize:
1. overall 3/4 view silhouette
2. front view
3. outer side view
4. back view
5. exploded construction
6. minor decorative details

Do not produce distorted geometry just to satisfy contradictory tiny details.

---

# 2. READ THE PROJECT FIRST

Before changing anything:

1. Read repository instructions.
2. Read the current `STATUS.md`.
3. Inspect the current character pipeline.
4. Inspect the current standard mannequin / skeleton in use.
5. Inspect the current approved or in-progress:
   - `Kabuto_01`
   - `Do_01`
6. Determine the existing Blender → Unreal workflow.
7. Determine naming conventions and folder conventions already used by the project.
8. Preserve existing working systems.

Do not alter the mannequin proportions.
Do not remodel Kabuto or Dō.
Do not create a new incompatible skeleton or body standard.

---

# 3. GOAL

Create two clean, game-ready modular shoulder armor pieces that:

- match the visual language of `Kabuto_01` and `Do_01`
- are fitted to the current SHŌEN mannequin
- are suitable for a high-status late-Heian / early-Kamakura samurai
- attach properly near the shoulder/clavicle area
- allow the arms to move
- work with animation
- remain modular in the Blender source
- can be imported into Unreal and viewed on the mannequin

The pieces should clearly read as a matching pair.

They should not look like generic fantasy shoulder pads.

---

# 4. HISTORICAL / VISUAL TARGET

The intended style is:

- late Heian / early Kamakura inspired
- around c. 1180
- mounted warrior / elite samurai
- same visual family as the existing helmet and chest armor

The shoulder armor should show:

- layered lamellar construction
- lacquered dark armor plates
- muted gold/bronze/brass fittings
- dark red cord/lacing
- subtle leather and interior padding
- believable weight and plate thickness

The two shoulder pieces should be a mirrored pair in role, but each should be authored correctly for its actual side.

Left and right are not to be confused or mislabeled.

---

# 5. SOURCE-ASSET STRUCTURE

Create the source files under something like:

`SourceArt/Characters/Samurai/Sode01/`

Expected main Blender source:
- `Sode01.blend`

Suggested supporting structure:
- `SourceArt/Characters/Samurai/Sode01/Textures/`
- `SourceArt/Characters/Samurai/Sode01/Exports/`
- `SourceArt/Characters/Samurai/Sode01/Scripts/`
- `SourceArt/Characters/Samurai/Sode01/README.md`

If useful, use Blender Python scripts and preserve them.

The `.blend` file must remain the authoritative editable source.

---

# 6. BUILD BOTH IN ONE TASK

Create both:

- `Sode_L_01`
- `Sode_R_01`

You may build one side first and derive the other side where appropriate, but the final result must be validated as a correct left/right pair.

Do not ship only one side and mirror it sloppily without verifying fit and handedness.

The left and right pieces must:
- share the same design language
- share the same materials
- share the same proportional system
- match the same construction logic
- fit their respective sides correctly

---

# 7. FIT TO EXISTING ARMOR AND MANNEQUIN

This is one of the most important requirements.

The shoulder armor must be fitted to the actual SHŌEN mannequin and tested together with `Kabuto_01` and `Do_01`.

Requirements:
- attaches correctly around the shoulder region
- sits naturally over the upper arm/shoulder
- visually connects with the upper edge of the Dō
- does not intersect badly with the helmet or neck area
- does not float too far away from the body
- does not bury into the chest armor
- allows practical shoulder and arm movement
- allows enough clearance for animation

Do not solve fit issues by scaling the shoulder armor absurdly large.

Fix placement, spacing, and structure properly.

---

# 8. SOURCE MODULARITY

Keep the source armor logically modular.

For each sode, preserve major construction regions as separable source objects where helpful.

Example logical breakdown:

For left:
- `Sode_L_01_Main`
- `Sode_L_01_UpperAttachment`
- `Sode_L_01_MainPlateRows`
- `Sode_L_01_LowerEdgeRow`
- `Sode_L_01_Lacing`
- `Sode_L_01_InteriorPadding`

For right:
- `Sode_R_01_Main`
- `Sode_R_01_UpperAttachment`
- `Sode_R_01_MainPlateRows`
- `Sode_R_01_LowerEdgeRow`
- `Sode_R_01_Lacing`
- `Sode_R_01_InteriorPadding`

This does not mean the runtime asset must remain split into many draw-call-heavy sections.
It means the Blender source should stay understandable and editable.

---

# 9. SILHOUETTE PRIORITY

Before fine detail, get the major shape correct.

Evaluate:
- width
- height
- curvature
- distance from shoulder
- row count
- top profile
- side profile
- how the armor hangs
- how it frames the upper arm
- how it reads from the front and 3/4 view

If the silhouette is wrong, do not waste time polishing tiny cords or rivets.

Fix proportions first.

---

# 10. LAMELLAR CONSTRUCTION

The shoulder pieces must read as layered lamellar armor, not a smooth surface with a texture slapped onto it.

Model:
- major plate rows
- visible plate thickness
- major edge shapes
- main structural layering

Use textures/normal maps/material detail for:
- fine lacing detail
- tiny repeated surface pattern
- small fasteners
- minor wear

Do not model thousands of tiny cords or knots individually if they create unnecessary complexity.

---

# 11. INTERIOR SIDE

The inside/interior view matters.

The shoulder armor should include a believable inner surface with:
- lining or padding
- visible structure
- attachment relationship to the upper straps
- a practical way it could rest on the shoulder

Do not leave the inside looking unfinished or like a hollow shell with no thought behind it.

---

# 12. MATERIALS

Match the existing armor set.

Use a restrained, reusable material set compatible with `Kabuto_01` and `Do_01`.

Target material families such as:
- dark lacquered iron / steel
- aged bronze / brass fittings
- dark red cord / lacing
- leather
- muted interior cloth / padding

Avoid excessive material slots.
Prefer material reuse and consistency across both shoulder pieces.

The two sode must match each other and the rest of the armor.

---

# 13. TEXTURE STRATEGY

Use practical game-appropriate textures.

Prioritize:
- normal detail
- roughness variation
- lacquer wear
- subtle edge wear
- lacing detail
- material separation

Do not create unnecessary giant textures.

Keep texture strategy consistent with the current samurai armor pipeline.

---

# 14. TOPOLOGY

Create clean, game-ready topology.

Requirements:
- clean normals
- no accidental duplicate faces
- no non-manifold garbage
- sensible transforms
- sensible origins/pivots
- no absurd hidden density
- correct scale

The source file may retain nondestructive modifiers if useful.
The exported runtime asset must be clean.

---

# 15. RIGGING / ATTACHMENT / DEFORMATION

These shoulder pieces must work with the existing character animation system.

They may be:
- rigidly attached to shoulder/clavicle/head-adjacent support if appropriate, or
- lightly skinned to the existing skeleton, depending on the current project architecture

Choose the method that best supports believable motion with minimal distortion.

Requirements:
- follows shoulder/upper-arm movement convincingly
- does not lag behind the body
- does not rubber-bend like cloth
- maintains overall rigid armor feel
- remains stable during idle / walk / run / attack motions

Test at minimum with:
- idle
- walk
- run
- basic melee pose
- basic bow-use pose if available
- arm raise / shoulder motion

If a hybrid method is appropriate, document it clearly.

Do not create a brand-new skeleton.

---

# 16. MATCHING LEFT AND RIGHT

Confirm clearly that:
- `Sode_L_01` is the left shoulder armor
- `Sode_R_01` is the right shoulder armor

Do not accidentally export or import them swapped.

In your final report, explicitly confirm the left/right assignment and show proof views.

---

# 17. UNREAL IMPORT

Import the finished assets into the existing SHŌEN Unreal project under an organized location such as:

`Content/Art/Characters/Samurai/Sode01/`

Use the project’s actual conventions if different.

Verify:
- correct scale
- correct orientation
- correct left/right placement
- correct materials
- correct attachment / skinning
- visual compatibility with Kabuto and Dō
- acceptable motion under animation
- no major clipping against body, Dō, or neck

Review them on the mannequin wearing at least:
- base mannequin/body
- `Kabuto_01`
- `Do_01`
- `Sode_L_01`
- `Sode_R_01`

---

# 18. REVIEW OUTPUTS

Inspect or capture:
- front
- back
- left side
- right side
- 3/4 front
- 3/4 rear
- close-up detail
- tactical distance
- one or more animation poses

Do not build a cinematic render setup.
Keep it functional and clear.

---

# 19. TRIANGLES / MATERIALS / RUNTIME

Record for each shoulder piece and/or the pair:
- source triangle count
- runtime triangle count
- number of material slots
- whether the pair uses shared materials
- whether the runtime version combines anything for efficiency

Do not aggressively optimize away silhouette quality.

Do not produce something absurdly heavy for a battlefield strategy game.

---

# 20. PERFORMANCE SANITY CHECK

This is not a huge optimization milestone.

Perform a reasonable sanity check by equipping the mannequin/samurai prototype and confirming that adding both sode does not create an obvious issue.

If practical, compare roughly:
- mannequin only
- mannequin + Kabuto + Dō
- mannequin + Kabuto + Dō + both Sode

We only need a basic incremental cost sanity check.

Do not turn this into a full battlefield benchmark.

---

# 21. DO NOT BUILD

Do NOT create:
- sleeves
- Kote
- Kusazuri
- Suneate
- weapons
- clothing
- horse gear
- new helmet variants
- chest armor variants
- full completed samurai

This task is only:
- `Sode_L_01`
- `Sode_R_01`

---

# 22. ITERATION RULE

If the first result looks poor, identify the largest issues first.

Examples:
- too bulky
- hangs too low
- sits too close to neck
- intersects Dō
- row spacing wrong
- outer silhouette incorrect
- lacing looks inconsistent
- pair does not match

Fix the biggest 2–5 issues first.

Do not waste time polishing tiny decorative details while the overall shape is wrong.

---

# 23. DELIVERABLES

Provide:

1. `Sode01.blend`
2. runtime exports for left and right
3. textures/materials
4. Unreal-imported assets
5. mannequin wearing Kabuto + Dō + both Sode
6. front/back/side/3-4 review captures
7. at least one animation pose capture
8. source triangle counts
9. runtime triangle counts
10. material count
11. attachment/weighting method
12. known clipping issues
13. known deviations from reference
14. README
15. any Blender scripts used

Commit the verified asset set and supporting files.

---

# 24. FINAL REPORT

Report:

## Visual quality
How closely both shoulder pieces match the references.

## Left / right correctness
Confirm which asset is left and which is right.

## Fit
How they fit the mannequin and Dō/Kabuto.

## Animation
What motions were tested and what clipping/deformation issues remain.

## Blender asset
Objects, triangles, materials, source path.

## Unreal asset
Import path, attachment/skinning method, runtime setup.

## Performance
Basic incremental cost versus the previous armor state.

## Limitations
What is still imperfect.

## Pipeline assessment
Whether building the pair together improved consistency.

## Recommended next component
Recommend only one of:
- `Kusazuri`
- `Kote_L` + `Kote_R`

Do not begin the next component automatically.

Stop after both `Sode_L_01` and `Sode_R_01` are complete.