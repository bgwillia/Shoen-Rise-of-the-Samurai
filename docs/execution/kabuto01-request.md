We are building the art pipeline for **SHŌEN**, an Unreal Engine strategy game set initially around late-Heian / early-Kamakura Japan.

This task is deliberately narrow.

## TASK

Create **one game-ready samurai kabuto helmet asset** in Blender using the supplied reference images, fit it to the existing SHŌEN standard male mannequin, then import and verify it in Unreal Engine.

Do **not** model the entire samurai.

Do **not** create chest armor, shoulder armor, clothing, shoes, body anatomy, weapons, or additional equipment.

The helmet is the only production asset for this task.

We are using this task to determine whether a component-by-component Blender workflow produces better results than asking for an entire character at once.

---

# REFERENCES

Use these files as the primary visual target:

`SourceArt/References/Samurai/Kabuto01/male_human_base_reference_sheet.png`

`SourceArt/References/Samurai/Kabuto01/kabuto_01_samurai_helmet_reference_sheet.png`

`SourceArt/References/Samurai/Kabuto01/samurai_kabuto_3d_reference_sheet.png`

Inspect all reference views before modeling.

The reference images include:

* front
* back
* left/right side
* top
* bottom/interior
* 3/4 perspective
* human-head scale reference
* exploded construction reference
* material reference
* detail closeups

These images are visual design references, not exact engineering drawings.

Do not blindly reproduce inconsistent AI-generated micro-details.

Preserve the overall helmet design and silhouette consistently across all views.

---

# FIRST: INSPECT THE PROJECT

Before creating anything:

1. Read the repository instructions and current `STATUS.md`.
2. Inspect the existing Unreal project.
3. Find the current standard human/mannequin asset if one exists.
4. Determine the exact Unreal world scale and character head dimensions currently used.
5. Determine whether Blender is installed and accessible.
6. Inspect the existing `SourceArt` / Unreal `Content` organization.
7. Follow established naming conventions if they already exist.

Do not alter existing working gameplay systems.

Do not begin unrelated work.

---

# DEVELOPMENT MODE

SHŌEN is currently in **rapid feasibility/prototype mode**.

Do enough checking to produce a usable asset, but do not spend excessive time building an exhaustive validation framework.

Priorities:

1. visual quality
2. correct proportions
3. clean reusable geometry
4. good silhouette
5. reproducible Blender source
6. successful Unreal import
7. reasonable game performance

Do not spend hours creating tooling around this one helmet.

---

# VISUAL TARGET

The helmet should read immediately as an elite early-medieval Japanese samurai helmet at normal SHŌEN gameplay distances.

Prioritize the following silhouette features:

* rounded/ridged helmet bowl
* pronounced brow/front plate
* side turn-back elements
* layered neck guard
* strong frontal ornament/crest
* visible lacing pattern
* believable interior volume around a human head

The model should look convincing both:

* close up
* at typical tactical camera distance

Avoid exaggerated fantasy proportions.

Avoid obvious later Sengoku excess where practical.

---

# COMPONENT BREAKDOWN

Model the helmet as modular source components.

Use logically separate Blender objects for at least:

### Helmet bowl

`Hachi`

### Front ornament / crest

`Maedate`

### Left side turn-back

`Fukigaeshi_L`

### Right side turn-back

`Fukigaeshi_R`

### Layered neck guard

`Shikoro`

### Interior rim / padding

`Uchiwa`

### Chin cord

`ShinHimo`

If the current project naming convention differs, adapt names while preserving the logical separation.

Do not merge all source components permanently into one uneditable mesh.

---

# BLENDER SOURCE REQUIREMENTS

Create the source asset under something like:

`SourceArt/Characters/Samurai/Kabuto01/`

Expected files:

`Kabuto01.blend`

Optional supporting files:

`Scripts/`

`Textures/`

`Exports/`

`README.md`

If Blender Python is useful for reproducibility, use it.

Preserve any useful scripts.

The `.blend` file must remain the authoritative editable source asset.

---

# FIT TO THE MANNEQUIN

The helmet must be modeled around the actual SHŌEN male mannequin/head scale.

Do not estimate scale only from the image.

Use the current game's actual character dimensions if available.

The helmet must:

* sit naturally on the head
* clear the skull
* not intersect the face
* not float excessively above the head
* leave sensible room for padding
* cover the back/sides appropriately
* permit normal head rotation

Use the reference mannequin for fit checks.

Do not modify the base mannequin simply to make the helmet fit.

---

# MODELING PRIORITIES

Spend geometry where it affects silhouette.

Important geometric features:

* helmet bowl curvature
* major bowl ridges
* brow/front plate
* neck guard plate layers
* side turn-backs
* frontal crest
* plate thickness
* visible edge profiles

Do NOT model every:

* cord fiber
* scratch
* tiny rivet irregularity
* decorative engraving
* woven thread

Those details belong primarily in textures/materials/normal maps.

---

# HELMET BOWL

The bowl should be clean and symmetrical unless the reference clearly requires asymmetry.

Create believable radial segmentation/ridges.

Avoid:

* faceted low-poly sphere appearance
* perfectly smooth modern motorcycle helmet appearance
* paper-thin geometry
* excessive ornamentation

The bowl should appear constructed from armored sections.

---

# NECK GUARD

The layered neck guard is visually important.

Create several overlapping curved plate rows.

Requirements:

* believable overlap
* consistent plate thickness
* correct downward/backward flare
* side coverage matching references
* enough separation to read at moderate camera distance

Do not model every individual lacing cord as geometry.

Use a simplified lacing treatment.

---

# CREST / MAEDATE

The frontal ornament should remain a separate source object.

Preserve the strong crescent/horn-like silhouette shown in the reference.

The crest should:

* be visually prominent
* remain proportionate to the helmet
* attach believably to the frontal mounting area
* not intersect the helmet shell

This piece may eventually be swapped for other samurai variants, so keep it modular.

---

# MATERIALS

Use a restrained material set.

Target approximately:

### Material 1

Dark lacquered armor/metal

### Material 2

Aged bronze/brass/gold-toned fittings

### Material 3

Dark red or blue-black lacing/cord

### Material 4

Interior leather/padding

Avoid giving every component its own unique material.

Prefer reusable materials suitable for future armor pieces.

Create subtle variation for:

* lacquer wear
* edge wear
* metal roughness
* aged fittings

Do not make it look freshly chrome-plated.

Do not over-weather it into archaeological ruin.

It should look like equipment currently being used and maintained.

---

# TEXTURE STRATEGY

Keep prototype textures reasonable.

Prefer:

* 2K or similarly practical working textures
* reusable material masks
* normal/roughness detail

Do not create unnecessary 8K textures.

Fine lacing and decorative surface detail should primarily come from textures/normal maps rather than dense geometry.

---

# TOPOLOGY

Create clean game-appropriate topology.

Requirements:

* no obvious non-manifold geometry
* no accidental internal duplicate faces
* sensible normals
* sensible transforms
* correct object origins
* no absurdly dense subdivision left in runtime export

The source file may retain nondestructive modifiers where useful.

Apply/export clean runtime geometry separately.

---

# TRIANGLE BUDGET

Do not optimize to an arbitrary ultra-low number at the expense of silhouette.

This is an elite unit helmet and can carry more detail than ordinary levy equipment.

However, it must remain practical for an RTS battlefield.

Record:

* source triangle count
* exported triangle count
* number of runtime materials
* number of component objects

If the asset is unexpectedly expensive, explain why.

---

# RUNTIME VERSION

Keep the Blender source modular.

For Unreal, choose the most efficient appropriate representation.

The runtime asset may combine some rigid helmet components if that reduces unnecessary render overhead.

Preserve modularity in the `.blend` source regardless.

Do not sacrifice future crest/helmet variation unnecessarily.

---

# SKELETON / ATTACHMENT

The helmet should ultimately attach to the character's head bone/socket.

Do not make the helmet its own complicated skeletal character.

For this prototype, use a rigid attachment to the existing head bone/socket unless project architecture requires something else.

Verify that it follows:

* head rotation
* basic locomotion
* idle animation

without visible sliding or detachment.

The chin cord does not need sophisticated cloth simulation.

Avoid expensive cloth simulation for this prototype.

---

# UNREAL IMPORT

Import into an organized location such as:

`Content/Art/Characters/Samurai/Kabuto01/`

Use the project's actual naming convention if different.

Verify:

* correct scale
* correct orientation
* correct materials
* correct normals
* correct attachment
* correct head fit
* correct shadows
* no obvious clipping

Place it on the existing mannequin or samurai prototype.

---

# VISUAL REVIEW SCENE

Create or use a simple asset-review scene.

Show the helmet:

### Close

Character inspection distance.

### Tactical

Normal SHŌEN battle camera distance.

### Far

Large-army camera distance.

The goal is to determine which details remain visible.

Do not spend time making this scene beautiful.

---

# REQUIRED COMPARISON

Compare the Blender/Unreal result against the supplied references.

Specifically evaluate:

* front silhouette
* side silhouette
* rear shape
* top shape
* neck guard width
* crest proportions
* helmet-to-head proportion
* side element angle
* major material colors

If something cannot be matched reliably because the generated reference views contradict each other, prioritize:

1. 3/4 hero view
2. front view
3. side view
4. back view
5. top view
6. minor decorative details

Document the choice.

Do not create bizarre geometry trying to reconcile impossible image inconsistencies.

---

# PERFORMANCE CHECK

This is not a full battlefield certification.

Perform only a useful sanity check.

Show the helmet on representative character counts using the existing scalable presentation system where practical:

* 100
* 500
* 1,000

Determine whether the helmet/material setup creates an obvious performance problem relative to the current character representation.

Do not spend a full milestone optimizing it.

Record obvious issues such as:

* excessive material sections
* too many draw calls
* expensive transparency
* excessive geometry

If performance is healthy enough for a feasibility asset, continue.

---

# DO NOT CREATE

Do NOT create:

* full samurai armor
* chest armor
* shoulder armor
* sleeves
* trousers
* shoes
* bow
* sword
* quiver
* horse
* multiple helmets
* multiple crests
* generals
* animation library
* facial detail

This task is **Kabuto 01 only**.

Do not expand scope because another component appears easy.

---

# OUTPUT QUALITY BAR

The result should be clearly better than the previous attempt to generate a complete samurai at once.

I expect:

* recognizable reference match
* clean silhouette
* convincing helmet volume
* sensible modular construction
* good fit on the mannequin
* reusable source asset
* reasonable game-ready geometry

If the helmet clearly does not resemble the reference, do not hide that behind technical success.

Visual resemblance is a primary acceptance criterion.

---

# ITERATION

If the first result is visibly poor:

Do not immediately proceed to Unreal integration as though it is finished.

First identify the 2–5 largest visual problems.

Examples:

* bowl too tall
* crest too wide
* neck guard too flat
* side pieces incorrect
* helmet oversized relative to head

Correct the major proportions in Blender.

Prioritize silhouette before small details.

Limit iteration to what materially improves the prototype.

---

# DELIVERABLES

At completion provide:

1. `Kabuto01.blend`
2. runtime export
3. textures/materials
4. Unreal-imported asset
5. mannequin wearing the helmet
6. close/tactical/far review captures
7. triangle count
8. material count
9. attachment method
10. known visual differences from reference
11. any Blender scripts used
12. concise asset README

Update `STATUS.md` only with a short art-pipeline note.

Do not turn this into another major gameplay milestone.

---

# FINAL REPORT

Report:

## Visual result

How closely it matches the reference and major deviations.

## Blender asset

Objects, triangles, materials, modifiers, and source location.

## Unreal asset

Import location, scale, attachment, and runtime setup.

## Performance

Basic 100/500/1,000-character sanity result.

## Pipeline

Which steps were automated versus manual.

## Problems encountered

Anything Codex/Blender struggled to reproduce.

## Recommendation

Whether component-by-component asset construction appears significantly more viable than generating an entire samurai at once.

Commit the asset and supporting files when verified.

Stop after **Kabuto 01**.

Do not start the next armor component automatically.
