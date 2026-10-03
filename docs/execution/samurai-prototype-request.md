We are continuing development of **SHŌEN**.

For this task, create the first **game-ready samurai character prototype** using **Blender for asset creation** and **Unreal Engine for integration/testing**.

This is a feasibility/prototype task, not final AAA character production.

Read the current repository instructions and `STATUS.md` first.

The visual references are located under:

`design-handoff/assets/references/samurai/`

Use the front, back, left, right, top/bottom and detail views as the primary visual reference.

# GOAL

Create one convincing late-Heian / early-Kamakura inspired samurai character that can replace a placeholder elite unit in SHŌEN.

The character should be:

* recognizable as a high-status samurai
* visually readable from the strategy-game camera
* modular enough to support future equipment variation
* reasonably optimized for displaying many instances
* rigged and capable of basic animation in Unreal
* imported into the actual SHŌEN Unreal project

Do not attempt to create every future samurai type.

This is one representative production-quality prototype.

---

# 1. Inspect the pipeline first

Before modeling:

1. Inspect the existing Unreal project.
2. Determine the current character/animation setup.
3. Check whether Blender is installed and usable from the development environment.
4. Determine the Unreal skeletal standard currently available.
5. Identify the cleanest Blender → Unreal export/import workflow for this repository.
6. Preserve existing working gameplay systems.

Do not redesign the game architecture.

---

# 2. Historical/visual target

The visual target is approximately **late Heian / early Kamakura, circa 1180**.

The reference art should guide the overall:

* silhouette
* armor layering
* proportions
* colors
* bow/quiver placement
* helmet silhouette
* cloth/armor relationship

Do not interpret every AI-generated decorative detail as a guaranteed historical fact.

For this feasibility asset, prioritize a believable period-inspired silhouette and internally consistent equipment.

Avoid obvious later Sengoku visual conventions where practical.

The samurai should primarily read as a **mounted-archer-era elite warrior**, even though the initial prototype may be tested on foot.

---

# 3. Base character

Create a human base suitable for strategy-game viewing.

Target:

* realistic adult Japanese male proportions
* neutral standing pose suitable for rigging
* believable hands and feet
* face readable at close inspection but not excessively detailed

Do not spend disproportionate time sculpting pores, eyelashes, or cinematic facial detail.

This character will often be viewed from significant camera distance.

---

# 4. Modular equipment

In the Blender source file, keep major components logically separated.

At minimum:

## Body / clothing

* underlying body
* undergarment
* trousers / hakama-style lower clothing
* footwear

## Armor

* chest armor
* shoulder guards
* armored sleeves
* waist armor sections
* shin guards
* helmet

## Equipment

* bow
* quiver
* arrows
* sword
* sheath

Preserve meaningful object names.

Example:

* `SK_Body`
* `ARM_Chest`
* `ARM_Shoulder_L`
* `ARM_Shoulder_R`
* `ARM_Kote_L`
* `ARM_Kote_R`
* `ARM_Kusazuri`
* `ARM_Suneate_L`
* `ARM_Suneate_R`
* `ARM_Kabuto`
* `WPN_Yumi`
* `WPN_Tachi`
* `PROP_Quiver`

Exact naming may follow existing project conventions.

---

# 5. Source modularity versus runtime performance

I want future equipment variation, but I do not want dozens of draw calls per soldier.

Therefore:

* preserve modular pieces in the `.blend` source
* keep materials organized for future swapping
* for the initial Unreal prototype, combine/skinning components where appropriate to create an efficient runtime skeletal mesh

Do not sacrifice the source asset's modularity simply because the Unreal prototype uses a combined render mesh.

Document this distinction.

---

# 6. Geometry target

This is not a cinematic hero character.

Choose a sensible medium-detail target suitable for an RTS/strategy game.

Prioritize silhouette where polygons actually matter:

* helmet
* shoulders
* armor skirt
* bow
* quiver
* large armor layers

Reduce geometry in areas that rarely affect silhouette.

Do not use millions of polygons in the shipped Unreal mesh.

Record:

* Blender source triangle count
* exported runtime triangle count
* number of materials
* number of skeletal bones
* number of separate runtime mesh sections

Do not optimize blindly to an arbitrary number; measure the result.

---

# 7. Armor construction

The armor should visually communicate layered construction.

Model enough depth that the armor does not look painted directly onto clothing.

Important silhouette elements include:

* broad shoulder armor
* layered torso protection
* segmented waist protection
* substantial helmet
* armored sleeves and shins
* cloth visible beneath armor

The small lacing does NOT need to be modeled as thousands of individual cords.

Use geometry only where needed for silhouette.

Use textures/normal maps/material treatment for finer repeated lacing details.

This is important for battlefield performance.

---

# 8. Materials and textures

Create a restrained material set based on the reference:

* dark lacquered armor
* dark red/red-brown lacing
* dark blue patterned cloth
* weathered leather
* bronze/brass/gold-toned fittings
* wood bow
* steel weapon surfaces
* natural rope/cord

Prefer texture reuse and material instances.

Avoid giving every tiny armor component a unique material.

Prepare textures at a sensible prototype resolution.

Do not produce huge 8K texture sets unless there is a demonstrated reason.

---

# 9. Rigging

Rig the samurai for normal human animation.

Prefer compatibility with the existing Unreal animation system if practical.

Required motions eventually include:

* idle
* walk
* run
* melee attack
* bow attack
* hit reaction
* death

For this task, do not create a giant animation library.

At minimum prove:

* neutral pose
* idle
* walk/run or locomotion
* one simple attack or test animation

If an existing Unreal-compatible skeleton/retargeting solution can be reused, prefer that over creating an unnecessarily proprietary skeleton.

Armor should deform acceptably during movement.

Rigid armor pieces should not visibly melt/stretch.

---

# 10. Weapons

Model a representative:

* yumi bow
* quiver and arrows
* tachi/sword and sheath

Weapons should be separate source assets or logically separable objects.

Set sensible origins/pivots and attachment points.

Do not permanently merge the sword or bow into the body geometry.

Future gameplay will swap weapons based on equipment quality.

---

# 11. Unreal import

Import the resulting asset into the existing SHŌEN Unreal project under an organized location such as:

`Content/Art/Characters/Samurai/Prototype01/`

Integrate it into one existing samurai/elite formation.

Do not replace every soldier in the game yet.

Verify:

* correct world scale
* correct orientation
* materials load
* skeleton works
* animation plays
* weapon attachments make sense
* shadows behave reasonably
* camera-distance readability is acceptable

---

# 12. LOD strategy

Create an initial reduced-detail strategy for distance rendering.

At minimum evaluate:

* close version
* medium-distance version
* distant representation

This may use Unreal-generated LODs initially if appropriate.

The distant samurai does not need tiny armor details that occupy only a few pixels.

Do not spend extensive time manually perfecting LODs in this first pass.

---

# 13. Battlefield performance test

This is one of the main purposes of the task.

Use the samurai prototype in increasingly large rendered groups.

Test approximately:

* 100
* 500
* 1,000
* 2,000

Do not assume every instance needs to be a full independent heavyweight Character Actor.

Use the existing scalable SHŌEN formation/presentation architecture where practical.

Measure:

* median FPS
* p95 frame time
* approximate GPU/CPU behavior available from existing tooling
* memory if easy to gather
* obvious animation cost
* obvious material/draw-call cost

Compare against the placeholder-unit baseline.

This does not need to certify the final game.

It exists to determine whether representative real character art changes the feasibility assessment.

---

# 14. Camera-distance evaluation

Capture or inspect the samurai at:

* close inspection range
* normal tactical combat range
* zoomed-out large-army range

Ask:

* Can the player identify that it is a samurai?
* Can samurai be distinguished from ordinary levy troops?
* Do expensive details disappear entirely at normal gameplay distance?
* Are helmet/shoulder/bow silhouettes doing most of the visual work?

Use the answers to guide future art production.

---

# 15. Preserve a reproducible asset pipeline

Store the Blender source in the repository's source-art structure, but use Git LFS where appropriate.

Suggested organization:

`SourceArt/Characters/Samurai/Prototype01/`

Include:

* `.blend`
* exported FBX or appropriate interchange file
* textures
* any Blender scripts used
* brief README describing export settings

If the asset is substantially generated through Blender Python, preserve the script so the model can be regenerated or adjusted.

Do not rely on undocumented manual steps.

---

# 16. Do not build yet

Do NOT create:

* ten different samurai
* every armor tier
* general characters
* civilian characters
* every animation
* mounted combat system
* cloth simulation for hundreds of soldiers
* complex facial animation
* final cinematic-quality textures
* elaborate customization UI

We need one good representative asset first.

---

# 17. Feasibility questions to answer

At completion, I want an answer to these questions:

1. Can Codex reliably create a usable SHŌEN character through Blender?
2. Does the model visually resemble the supplied reference closely enough?
3. Is the Blender → Unreal pipeline reproducible?
4. Can the armor be modular in source while efficient at runtime?
5. How expensive is this character compared with our placeholder soldier?
6. How many can we display/animate before performance becomes concerning?
7. Which character details actually remain visible at SHŌEN's normal camera distance?
8. What should we simplify before producing the rest of the army?

---

# Validation philosophy

Remain in feasibility mode.

Do enough verification to establish:

* Blender file opens
* export works
* Unreal import works
* materials work
* skeleton/animation works
* representative battlefield test runs

Do not create an exhaustive production acceptance process yet.

If something is visibly imperfect but does not block evaluating feasibility, document it and continue.

---

# Deliverable

Stop when there is:

* one Blender samurai source asset
* one Unreal-ready samurai
* modular source components
* basic materials
* working skeleton/animation proof
* weapons
* imported Unreal asset
* one formation using the real model
* scale/performance test results

Then report:

* source files created
* Blender version
* triangle/material/bone counts
* Unreal import setup
* visual limitations
* performance results
* comparison with placeholder soldiers
* recommended improvements
* whether this pipeline is suitable for producing SHŌEN's larger character library

Commit the prototype when verified.
