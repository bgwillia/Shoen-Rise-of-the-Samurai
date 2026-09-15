We are continuing the modular character-art pipeline for **SHŌEN**.

The previous component was **Kabuto 01**.

For this task, create **one game-ready Dō chest armor component** in Blender, fit it precisely to the existing SHŌEN male mannequin, verify that it works with normal character animation, and import it into Unreal Engine.

This is a deliberately narrow asset-production task.

Do NOT model the entire samurai.

Do NOT model the helmet again.

Do NOT create shoulder armor, sleeves, waist armor, shin armor, weapons, trousers, footwear, or other unrelated components.

The only new production asset in this task is:

**Dō 01 — torso/chest armor**

---

# 1. READ THE PROJECT FIRST

Before changing anything:

1. Read the repository instructions.
2. Read the current `STATUS.md`.
3. Inspect the existing SHŌEN male mannequin.
4. Inspect the approved/current `Kabuto01.blend` and Unreal Kabuto asset.
5. Determine the existing Blender-to-Unreal character pipeline.
6. Find the exact skeleton and mannequin dimensions currently in use.
7. Inspect current naming, material, texture, and SourceArt conventions.
8. Preserve all existing working gameplay and art systems.

Do not modify the mannequin proportions.

Do not remodel the Kabuto.

Do not create a second incompatible character standard.

---

# 2. REFERENCES

Use the Dō reference pack as the primary visual target.

Expected location:

`SourceArt/References/Samurai/Do01/`

Inspect every supplied view before modeling.

The reference pack may contain:

* front
* back
* left side
* right side
* 3/4 view
* close-up details
* construction breakdown
* material reference
* mannequin-fit reference

Treat the supplied images as visual references, not exact engineering drawings.

AI-generated reference images may contain minor inconsistencies.

When views conflict, prioritize:

1. 3/4 hero view
2. front
3. side
4. back
5. construction/detail views
6. decorative micro-details

Do not create distorted geometry trying to reconcile impossible image inconsistencies.

---

# 3. HISTORICAL / VISUAL TARGET

The visual target is a high-status Japanese warrior around:

**Late Heian / early Kamakura, approximately c. 1180**

The Dō should visually belong to the same warrior as Kabuto 01.

It should evoke an early samurai armor system appropriate to a mounted-warrior tradition rather than a later Sengoku infantry cuirass.

Prioritize:

* broad armored torso silhouette
* layered lamellar construction
* believable lacing
* sufficient rigidity
* protection without modern plate-armor appearance
* visual compatibility with the helmet reference
* room for future shoulder armor and waist armor

Avoid obvious fantasy armor.

Avoid excessively late-period aesthetics where possible.

---

# 4. FIT TO THE EXISTING MANNEQUIN

This is one of the most important requirements.

Build the Dō around the **actual SHŌEN standard male mannequin**.

Do not estimate body dimensions only from the concept art.

The armor must:

* fit the chest and upper abdomen correctly
* leave believable padding/clothing clearance
* avoid intersecting the torso
* allow shoulder motion
* allow arm movement
* allow torso rotation
* allow moderate forward bending
* leave sufficient mounting space for future Sode
* leave sufficient transition space for future Kusazuri
* not intersect Kabuto 01 when the head/neck moves normally

Do not alter the mannequin to accommodate poor armor proportions.

Fix the armor.

---

# 5. SOURCE-ASSET STRUCTURE

Create the Blender source under:

`SourceArt/Characters/Samurai/Do01/`

Expected main file:

`Do01.blend`

Suggested supporting structure:

`SourceArt/Characters/Samurai/Do01/`

* `Do01.blend`
* `Textures/`
* `Exports/`
* `Scripts/`
* `README.md`

If Blender Python is used, preserve the useful scripts.

The `.blend` file is the authoritative editable source.

---

# 6. MODULAR CONSTRUCTION

Do not permanently collapse the entire source armor into one uneditable object.

Keep major construction components logically separable.

At minimum consider distinct source objects or clearly separated geometry for:

### Main torso armor

`Do_Main`

### Upper chest / frontal reinforcing area

`Do_Upper`

### Rear torso armor

`Do_Back`

### Left side closure / side plate if appropriate

`Do_Side_L`

### Right side closure / side plate if appropriate

`Do_Side_R`

### Edge / border reinforcement

`Do_Edge`

### Major visible cord/lacing groups

`Do_Lacing`

You may simplify the exact breakdown if the reference construction suggests a better structure.

The important principle is:

**source modularity, efficient runtime asset.**

---

# 7. LAMELLAR CONSTRUCTION

The Dō must not look like a smooth plastic shell with a lamellar texture painted onto it.

The armor should have visible physical layering.

Model major plate rows or larger structural layers as geometry.

Use textures / normal maps / masks for small repetitive detail.

Do NOT individually model thousands of:

* tiny cords
* knots
* holes
* stitches
* rivets

Use enough geometry to communicate construction at normal tactical camera distance.

---

# 8. SILHOUETTE FIRST

Before adding fine details, make the major shape correct.

Evaluate:

* chest width
* waist taper
* armor depth
* shoulder opening
* neck opening
* side profile
* back profile
* lower edge shape
* overall proportion relative to head and hips

If the silhouette is wrong, do not hide it under detailed textures.

Fix proportions first.

---

# 9. THICKNESS

Give armor components believable physical thickness.

Avoid:

* infinitely thin planes
* armor sitting directly on the skin
* huge unrealistic gaps
* excessive bulk

The Dō should look like a constructed defensive garment with padding/clothing beneath it.

---

# 10. ARM MOVEMENT / SHOULDER CLEARANCE

Test the armor with the mannequin arms in several poses.

At minimum inspect:

* neutral A-pose
* arms forward
* arms raised modestly
* bow-drawing-type shoulder position if an existing pose is available
* basic melee posture if available

The chest armor must not prevent reasonable upper-body movement.

Do not solve clipping by making the armor absurdly oversized.

---

# 11. MATERIALS

Reuse compatible materials from Kabuto 01 where sensible.

The armor should visually belong to the same equipment family.

Target material families such as:

### Lacquered armor

Dark black / blue-black lacquer

### Lacing

Dark red, muted red, dark blue or other reference-supported cord color

### Fittings

Aged bronze / brass / subdued gold-toned metal

### Leather

Weathered but maintained leather

### Cloth/padding

Muted historically inspired fabric tones

Avoid excessive material slots.

Prefer reusable material instances.

Do not create unique shaders for tiny components.

---

# 12. TEXTURE STRATEGY

Use practical game textures.

2K-class textures are sufficient unless an existing character-art convention requires otherwise.

Prioritize:

* normal detail
* roughness variation
* lacquer variation
* edge wear
* subtle dirt/use
* lacing detail

Do not make the armor look:

* brand new plastic
* heavily rusted archaeological debris
* excessively shiny
* fantasy-polished

It should look maintained and actively used.

---

# 13. TOPOLOGY

Create clean game-ready topology.

Requirements:

* clean normals
* no accidental duplicate faces
* no non-manifold garbage
* no hidden high-density geometry accidentally exported
* sensible edge flow where deformation occurs
* sensible object origins
* consistent transforms
* correct scale

The Blender source may retain nondestructive modifiers.

The exported Unreal version must be clean.

---

# 14. SKINNING / RIGGING

The Dō must follow the existing SHŌEN character skeleton.

Do not create a separate incompatible skeleton.

This torso armor should be appropriately skinned/weighted to the existing character rig.

Because much of the armor is structurally rigid:

* minimize rubbery deformation
* avoid plate sections bending like cloth
* weight rigid sections appropriately
* allow enough controlled deformation for torso animation

Test at least:

* idle
* walk
* run
* basic attack
* upper-body turn if available

If existing prototype animations are available, use them.

Do not create a new animation library.

---

# 15. FUTURE COMPONENT COMPATIBILITY

Dō 01 will eventually need to connect visually with:

* Sode shoulder armor
* Kusazuri waist armor
* Kote arm armor
* undergarments
* Kabuto 01

Leave appropriate space and sensible anchor regions.

Do not add those pieces now.

But make sure this armor does not make them impossible to add later.

---

# 16. RUNTIME VERSION

The Blender source should remain modular.

For Unreal runtime, produce an efficient representation.

Record:

* source triangle count
* runtime triangle count
* number of material slots
* number of mesh sections
* whether components were combined for runtime
* bone influence count where relevant

Do not optimize away important silhouette features.

Do not ship an absurdly dense sculpt.

---

# 17. UNREAL IMPORT

Import the asset into an organized location such as:

`Content/Art/Characters/Samurai/Do01/`

Use existing project naming conventions if different.

Equip the Dō on the current SHŌEN mannequin.

Also equip Kabuto 01 if available so the two approved assets can be reviewed together.

Verify:

* scale
* orientation
* skeleton compatibility
* material rendering
* torso fit
* shoulder clearance
* animation deformation
* no obvious body clipping
* no major helmet interaction problems

---

# 18. REVIEW VIEWS

Create a simple review setup showing the mannequin wearing:

* base body/clothing placeholder
* Kabuto 01
* Dō 01

Capture or inspect:

### Front

### Back

### Left

### Right

### 3/4

### Tactical camera distance

Also inspect at least one animation pose.

Do not spend time making a cinematic scene.

---

# 19. VISUAL ACCEPTANCE PRIORITIES

Evaluate the asset in this order:

1. correct overall torso silhouette
2. correct scale on mannequin
3. believable armor construction
4. compatibility with Kabuto
5. clean shoulder/neck openings
6. layered depth
7. materials
8. fine decorative details

If the silhouette is bad, do not proceed as if the asset is finished just because it technically imports.

---

# 20. ITERATION RULE

If the first version looks poor, identify the largest visual problems first.

For example:

* torso too wide
* torso too short
* armor too bulky
* shoulder openings too small
* neck opening incorrect
* plate rows too flat
* lower edge shape incorrect

Fix the 2–5 largest issues.

Do not repeatedly tweak tiny details while major proportions remain wrong.

---

# 21. PERFORMANCE SANITY CHECK

This is not a full battlefield benchmark.

Use the armor on representative mannequin counts if practical:

* 100
* 500
* 1,000

Look for obvious problems from:

* triangle count
* material sections
* skeletal deformation
* draw calls

Compare roughly to:

* mannequin alone
* mannequin + Kabuto
* mannequin + Kabuto + Dō

We want to understand incremental asset cost.

Do not spend a full development milestone optimizing this.

---

# 22. DO NOT BUILD

Do NOT create:

* Sode
* Kusazuri
* Kote
* Suneate
* shoes
* bow
* sword
* quiver
* horse armor
* multiple Dō variants
* decorative alternative skins
* general armor
* complete samurai character

This task is **Dō 01 only**.

---

# 23. QUALITY BAR

The completed asset should:

* clearly resemble the supplied reference
* look compatible with Kabuto 01
* fit the mannequin properly
* read clearly as samurai torso armor
* have convincing physical depth
* animate without severe clipping
* remain editable and modular in Blender
* remain practical for strategy-game use

Visual quality matters.

A technically valid but visibly poor asset is not a successful result.

---

# 24. VALIDATION PHILOSOPHY

Remain in rapid asset-prototype mode.

Verify:

* Blender opens
* geometry is valid
* textures/materials work
* export works
* Unreal import works
* rig works
* animation does not catastrophically clip
* tactical-distance silhouette reads properly

Do not build a huge automated validation framework for this single asset.

Spend effort on the model itself.

---

# 25. DELIVERABLES

Provide:

1. `Do01.blend`
2. runtime export
3. textures/materials
4. Unreal-imported asset
5. mannequin wearing Dō 01
6. mannequin wearing Kabuto 01 + Dō 01
7. front/back/side/3-4 review captures
8. at least one animation-pose capture
9. source triangle count
10. runtime triangle count
11. material count
12. skeleton/weighting method
13. known clipping issues
14. known deviations from reference
15. README
16. preserved Blender scripts if used

Commit the verified asset and supporting files.

---

# FINAL REPORT

Report:

## Visual quality

How closely Dō 01 matches the reference.

## Fit

How it fits the SHŌEN mannequin.

## Animation

What poses/animations were tested and any clipping.

## Blender asset

Objects, triangles, materials, modifiers and source path.

## Unreal asset

Import path, skeleton, runtime setup and material configuration.

## Performance

Incremental cost compared with mannequin and mannequin + Kabuto.

## Limitations

What remains imperfect.

## Pipeline assessment

Whether the component-by-component approach continues to produce substantially better results than attempting a full samurai at once.

## Recommended next component

Recommend only one of:

* Sode
* Kusazuri

Do not start that component automatically.

Stop after **Dō 01**.
