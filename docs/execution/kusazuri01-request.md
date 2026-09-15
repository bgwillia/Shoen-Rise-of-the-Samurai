We are continuing the modular samurai armor pipeline for **SHŌEN**.

For this task, create one complete modular waist-armor assembly:

- `Kusazuri_01`

This is the hanging waist / skirt armor that fits below `Do_01`.

The design must visually and structurally match the established armor set:

- `Kabuto_01`
- `Do_01`
- `Sode_L_01`
- `Sode_R_01`

Do NOT model the full samurai.
Do NOT remodel existing armor pieces.
Do NOT create Kote, Suneate, clothing, weapons, shoes, or other unrelated components.

This task is for **Kusazuri_01 only**.

---

# 1. REFERENCES

Use the supplied Kusazuri reference sheet as the primary visual target.

Expected reference location:

`SourceArt/References/Samurai/Kusazuri01/`

Primary reference image:

`kusazuri_01_reference_sheet.png`

The sheet includes:

- front
- back
- left side
- right side
- top / interior
- bottom / underside
- close-up construction details
- material references
- exploded construction
- on-character fitting examples

Inspect the complete reference before modeling.

Treat the reference sheet as the authoritative visual direction.

If small inconsistencies exist between generated views, prioritize:

1. on-character fit
2. front silhouette
3. 3/4 / side silhouette
4. back silhouette
5. exploded construction
6. top/interior view
7. minor decorative details

Do not create distorted geometry trying to reconcile impossible micro-details.

---

# 2. READ THE PROJECT FIRST

Before changing anything:

1. Read repository instructions.
2. Read the current `STATUS.md`.
3. Inspect the current SHŌEN mannequin / skeleton.
4. Inspect the existing:
   - `Kabuto_01`
   - `Do_01`
   - `Sode_L_01`
   - `Sode_R_01`
5. Determine the existing Blender → Unreal workflow.
6. Inspect current SourceArt and Unreal folder conventions.
7. Reuse existing armor materials where practical.
8. Preserve all working gameplay systems.

Do not alter mannequin proportions.

Do not alter the existing skeleton simply to make the armor fit.

Do not remodel `Do_01`.

---

# 3. GOAL

Create a clean, game-ready Kusazuri waist-armor assembly that:

- visually matches the current SHŌEN samurai armor
- fits directly underneath `Do_01`
- wraps naturally around the waist and hips
- protects the front, sides, and rear
- maintains the layered lamellar design language
- permits walking and running
- permits large leg movement
- permits mounted-warrior-style hip movement
- does not behave as one giant rigid skirt
- remains modular and editable in Blender
- imports correctly into Unreal
- works with the existing character animations

The final result should read immediately as part of the same armor set.

---

# 4. HISTORICAL / VISUAL TARGET

The intended visual direction is:

**Late Heian / Early Kamakura inspired**
**approximately c. 1180**
**high-status mounted samurai**

Match the established armor language:

- dark lacquered lamellar plates
- dark red lacing
- subdued brass / bronze / gold-toned fittings
- dark blue / indigo textile
- maintained but used leather
- layered protective construction

Avoid:

- fantasy plate skirts
- exaggerated spikes
- oversized modern-fantasy armor
- obvious later Sengoku styling where practical
- one-piece rigid metal skirt construction

The Kusazuri should look like armor designed to protect the hips and upper legs while still allowing movement.

---

# 5. SOURCE-ASSET STRUCTURE

Create the source asset under:

`SourceArt/Characters/Samurai/Kusazuri01/`

Expected main Blender source:

`Kusazuri01.blend`

Suggested structure:

`SourceArt/Characters/Samurai/Kusazuri01/`
- `Kusazuri01.blend`
- `Textures/`
- `Exports/`
- `Scripts/`
- `README.md`

If Blender Python is useful, preserve the scripts.

The `.blend` file must remain the authoritative editable source.

---

# 6. MODULAR PANEL CONSTRUCTION

The Kusazuri must NOT be modeled as one monolithic solid skirt.

Create it from logically separate hanging armor sections.

Use the supplied reference to determine the final panel count and proportions.

At minimum preserve logical source objects such as:

- `Kusazuri_01_Belt`
- `Kusazuri_01_Front_Center`
- `Kusazuri_01_Front_L`
- `Kusazuri_01_Front_R`
- `Kusazuri_01_Side_L`
- `Kusazuri_01_Side_R`
- `Kusazuri_01_Rear`
- `Kusazuri_01_Lacing`
- `Kusazuri_01_Interior`

If the final design uses a different historically/visually coherent panel arrangement, adjust names accordingly.

The important requirement is:

**The individual hanging sections remain understandable and editable in the Blender source.**

---

# 7. FIT TO DŌ 01

This is one of the most important requirements.

The Kusazuri should appear to continue naturally from the lower edge of `Do_01`.

Check:

- waist circumference
- vertical position
- overlap with Dō
- belt/attachment region
- plate spacing
- front alignment
- rear alignment
- left/right symmetry where appropriate

There should not be:

- a large floating gap between Dō and Kusazuri
- severe mesh intersection
- an implausibly thick waist
- visible body exposure caused by poor positioning

Do not resize the mannequin to fit the armor.

Fit the armor to the mannequin and Dō.

---

# 8. HIP AND LEG CLEARANCE

This is the most important functional difference from the previous armor components.

The Kusazuri must allow substantial lower-body movement.

Test clearance for:

- standing
- walking
- running
- stepping forward
- wide stance
- crouched combat stance
- torso rotation
- hip rotation
- knee lift

The front armor should not block the thighs from moving forward.

Side panels should not bury deeply into the legs during a normal stride.

Rear armor should not prevent hip extension.

Do not solve clipping by placing the armor absurdly far away from the body.

Use panel separation and sensible weighting/rigging.

---

# 9. SILHOUETTE FIRST

Before adding decorative detail, make the major shape correct.

Evaluate:

- overall width
- overall length
- front panel proportions
- side panel proportions
- rear coverage
- waist taper
- outward flare
- space between hanging panels
- distance from thighs
- relationship to torso armor

Review from:

- front
- back
- left
- right
- 3/4 front
- 3/4 rear

If the silhouette is wrong, fix it before working on micro-details.

---

# 10. LAMELLAR CONSTRUCTION

The Kusazuri must visibly share the construction language of the rest of the armor.

Model enough geometry to show:

- major horizontal plate rows
- overlapping construction
- plate thickness
- lower-edge reinforcement
- major side edges
- believable attachment areas

Do NOT individually model thousands of:

- tiny cord fibers
- microscopic knots
- holes
- scratches
- stitch details

Use texture / normal-map detail for those.

The physical geometry should communicate structure at normal tactical camera distance.

---

# 11. BELT / UPPER ATTACHMENT

Create a believable upper attachment system where the Kusazuri connects to the armor/waist.

The reference includes an upper belt / cord region.

This should:

- visually support the hanging panels
- align with the lower Dō
- avoid intersecting the stomach/hips
- preserve enough space for underlying clothing

Keep it modular enough that the attachment method can be adjusted later.

Do not permanently bake it into the body mesh.

---

# 12. INTERIOR

Model a simplified but believable interior.

The player may rarely see it, so do not overbuild it.

Include enough structure to communicate:

- lining/padding
- attachment straps/cords
- inside plate surfaces
- panel construction

Avoid leaving the interior as obviously unfinished single-sided geometry.

---

# 13. MATERIALS

Reuse the established SHŌEN samurai materials wherever practical.

Target:

### Lacquered armor
Dark black / blue-black lacquer

### Lacing
Dark red

### Metal fittings
Aged bronze / brass / muted gold

### Leather
Dark maintained leather

### Cloth / padding
Dark blue / indigo textile

Do not create unnecessary new materials if the existing Kabuto / Dō / Sode materials can be reused.

Material consistency across the armor set is more important than unique shaders for every component.

---

# 14. TEXTURES

Use practical game-ready textures.

Prioritize:

- roughness variation
- subtle lacquer wear
- normal-map lamellar/lacing detail
- lower trim pattern
- leather variation
- textile variation

Do not create unnecessary 8K textures.

Follow the existing armor texture strategy.

---

# 15. TOPOLOGY

Create clean game-appropriate topology.

Requirements:

- clean normals
- no accidental duplicate faces
- no non-manifold garbage
- sensible object origins
- consistent transforms
- reasonable plate thickness
- no hidden high-density geometry accidentally exported
- correct game scale

Use nondestructive modifiers in Blender where beneficial.

Export clean runtime geometry.

---

# 16. RIGGING / SKINNING

The Kusazuri must use the existing SHŌEN skeleton.

Do NOT create a separate skeleton.

Because the Kusazuri consists of hanging armor panels, preserve the sense that the panels are relatively rigid.

Avoid rubber-like bending through the middle of armor plates.

Use the simplest suitable approach consistent with the current character pipeline.

Potential approaches may include:

- weighted panels using pelvis / thigh influences
- dedicated secondary bones if already compatible with the project
- rigid sections with controlled skeletal influence

Do not add a complex physics simulation unless absolutely necessary for the feasibility prototype.

Prefer predictable animation behavior first.

---

# 17. MOVEMENT TESTS

Test the Kusazuri with existing character motions.

At minimum:

- idle
- walk
- run
- basic melee stance
- attack
- bow stance if available
- moderate crouch
- large forward step

Look specifically for:

- thigh clipping
- panel inversion
- panel collapsing
- rear panel intersection
- side panel intersection
- armor penetrating Dō
- excessive swinging
- unnatural stretching

Correct major problems before considering the asset complete.

---

# 18. UNREAL IMPORT

Import into an organized Unreal location such as:

`Content/Art/Characters/Samurai/Kusazuri01/`

Use existing project conventions if different.

Review it on the mannequin together with:

- `Kabuto_01`
- `Do_01`
- `Sode_L_01`
- `Sode_R_01`
- `Kusazuri_01`

Verify:

- correct scale
- correct orientation
- skeleton compatibility
- materials
- panel placement
- animation behavior
- no major Dō intersection
- reasonable leg clearance

---

# 19. REVIEW VIEWS

Produce or inspect:

- front
- back
- left
- right
- 3/4 front
- 3/4 rear
- top / interior
- underside if useful
- tactical-camera distance
- walking pose
- wide-step/run pose

Do not build a cinematic review environment.

Functional asset review is sufficient.

---

# 20. EXPLODED / COMPONENT CHECK

Compare the Blender source with the exploded construction reference.

Make sure the source remains understandable as:

- upper belt / attachment
- front panel(s)
- left-side panel(s)
- right-side panel(s)
- rear panel(s)
- lacing / trim
- interior / padding

Do not simply merge all geometry into one object and lose the construction logic.

Runtime merging may still be used where beneficial.

---

# 21. RUNTIME EFFICIENCY

Record:

- source triangle count
- runtime triangle count
- material slots
- mesh sections
- number of major panels
- skeleton/bone influences used

Do not optimize away the silhouette.

But remember SHŌEN may display thousands of soldiers.

Avoid unnecessary:

- translucent materials
- unique material slots
- extreme geometry
- physics-heavy secondary motion

---

# 22. PERFORMANCE SANITY CHECK

Perform only an incremental sanity check.

Compare approximately:

- mannequin + current upper armor
- mannequin + current upper armor + Kusazuri

If practical, inspect representative groups such as:

- 100
- 500

We are only checking that the new component does not introduce an obvious rendering/animation problem.

Do not make this a full performance milestone.

---

# 23. DO NOT BUILD

Do NOT create:

- Kote
- Suneate
- footwear
- trousers
- Yumi
- Quiver
- Tachi
- alternate Kusazuri styles
- additional Dō
- new character body
- complete finished samurai

This task is only:

`Kusazuri_01`

---

# 24. ITERATION RULE

If the first attempt looks poor, identify the largest visual/functional issues first.

Examples:

- too long
- too short
- too wide
- panels too close together
- panels too far apart
- front coverage looks wrong
- side panels collide with thighs
- rear panel clips during running
- waist belt does not align with Dō
- lamellar rows do not match the rest of the armor

Fix the largest 2–5 issues first.

Do not polish microscopic lacing while the silhouette or movement is wrong.

---

# 25. DELIVERABLES

Provide:

1. `Kusazuri01.blend`
2. runtime export
3. textures/material setup
4. Unreal-imported asset
5. mannequin wearing current armor + Kusazuri
6. front/back/left/right review captures
7. 3/4 review capture
8. top/interior capture
9. walking/running or wide-step pose
10. source triangle count
11. runtime triangle count
12. material count
13. rigging/skinning method
14. panel breakdown
15. known clipping issues
16. known visual deviations
17. README
18. any Blender scripts used

Commit the verified asset and supporting files.

---

# FINAL REPORT

Report:

## Visual quality
How closely `Kusazuri_01` matches the supplied reference.

## Fit
How it connects visually and physically to `Do_01`.

## Panel construction
Describe the number and organization of hanging sections.

## Animation
What movements were tested and any remaining clipping.

## Blender asset
Objects, triangles, materials, modifiers and source location.

## Unreal asset
Import location, skeleton setup, runtime representation.

## Performance
Basic incremental cost compared with the previous armor state.

## Limitations
What remains imperfect.

## Pipeline assessment
Whether this modular approach continues to work well.

## Recommended next component
Recommend only one:

- `Kote_L_01 + Kote_R_01`
- `Suneate_L_01 + Suneate_R_01`

Do not begin the next component automatically.

Stop after `Kusazuri_01` is complete.