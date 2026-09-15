# Dō 01

One modular torso armor component for SHŌEN. The user's follow-up replaces the former custom fit body with **Epic's official Manny**. The approved Kabuto geometry is reused as a rigid head attachment.

## Source and fit

- [Do01.blend](Do01.blend) is the editable authority. Ten source objects separate front/back lamellae, side closures, upper panels, straps, bindings, lacing, fittings, and lining.
- [Manny fixture](../../Mannequins/Manny/README.md): native SKM_Manny_Simple, 1.80524 m tall, native SK_Mannequin skeleton. No body proportions, topology, or reference bones were remodeled.
- Blender uses metres, −Y forward. The root object represents Unreal's root bone: 88 Blender bones plus the object root = 89 native mesh reference bones. Its persisted scale is 0.01; mesh and bone data are in centimetres.
- The helmet preserves Kabuto geometry and unit scale. Its rest pivot is (0, −0.025, 1.598) m. The manifest records the equivalent native Manny head-relative attachment.
- Six physical rows overlap; upper side rows scoop beneath the armpits. Padding clearance, flexible shoulder mounts, and an open lower transition reserve space for later components.

Each lamella island shares a consistent blend derived from Manny's torso skin. Upper panels use spine_05; strap arches blend smoothly from chest anchors to the same-side clavicle. Armor vertices use at most four normalized bone influences. Generated distance LODs retain the four largest influences and renormalize them; source skinning remains unchanged.

## Finish and textures

One opaque M_Do01 material uses a 2K atlas: BaseColor is sRGB; tangent Normal and packed occlusion/roughness/metallic are non-color. Unreal import flips normal green for its convention.

The finish combines the Kabuto material family with denser woven cord detail, maintained dark lacquer, thin brass tracers over black rolled bindings, and raised floral fittings. Repeated detail uses atlas tiles; representative cords and ornaments have physical relief.

[Material source image](Textures/Source/Do01_MaterialSources.png) was generated with the built-in ImageGen tool from the supplied Dō reference and Kabuto swatches. [Exact prompt](Textures/Source/prompt.txt). The texture script assembles those flat sources into the game atlas. Normal and roughness detail are artist-controlled image-derived estimates, not scans or a high-poly bake. Review captures are actual Blender or Unreal renders.

## Runtime and evidence

SK_Do01 lives under /Game/Art/Characters/Samurai/Do01 and uses the existing /Game/Characters/Mannequins/Meshes/SK_Mannequin skeleton. Source parts combine into one skeletal mesh with one material section per LOD. Manny leads the pose; the armor follows it; Kabuto attaches to the fitted head transform.

A real-renderer material preflight compiles the active Mac shader permutations after import; a NullRHI import alone does not verify material rendering.

Native Epic idle, forward walk, forward jog, and unarmed attack clips are reused. Temporary review copies lock root motion in place; original clips are preserved. Static Manny LOD1/2 are generated crowd-review approximations; native skeletal Manny and its own LODs remain unchanged.

Exact counts, hashes, LOD weight pruning, and fit parameters are in [asset-manifest.json](asset-manifest.json). Source, import, rendered review, and performance evidence are recorded separately in [verification](../../../../artifacts/do01/verification.md).

## Current counts and motion limits

Source and runtime LOD0 are **81,392 triangles**; runtime LOD1/2 are **32,556 / 5,504**, with one material section at each LOD. Ten source objects stay independently editable.

Neutral, raised arms, moderate bend/turn and head-turn samples have zero measured body/helmet intersections. Native unarmed motion still has contact, especially the attack at the shoulders beneath Kabuto. Smooth strap weights reduce sharp folding; the asset is not certified clipping-free for arbitrary animations. Worst-frame captures and measured limits are retained in verification.

## Workflow

From the repository root:

    python3 tools/do.py export
    python3 tools/do.py validate
    python3 tools/dev.py build
    python3 tools/do.py import
    python3 tools/do.py materials
    python3 tools/do.py review --mode armor --camera close --animation idle
    python3 tools/do.py review --mode helmet --camera close --animation walk
    python3 tools/do.py review --mode armor --camera tactical --count 1000

Export reads the saved .blend, preserves editable source geometry, fit fixtures, and skinning, and rebuilds hidden runtime copies. It temporarily evaluates the reference pose, then restores the saved animation, frame, and root transform. The source command intentionally rebuilds the procedural design and overwrites manual source edits; use it only when rebuilding from the scripts.

Scripts/review_do.py reopens the source for diagnostic poses and captures without saving changes. Use one Unreal process at a time. Crowd timing comparisons require no simultaneous Blender rendering, builds, or other heavy tests.

## Scope

Only the torso armor was built. Historical styling follows the supplied reference; it is not a reconstruction claim. The fixture and isolated review do not replace the accepted strategy prototype's battlefield representation. See verification for measured clearance and remaining motion limitations. Visual approval and full-army performance certification are not assumed.
