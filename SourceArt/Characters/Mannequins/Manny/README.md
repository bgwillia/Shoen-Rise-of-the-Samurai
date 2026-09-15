# Official Manny fit fixture

Manny is the user-requested fit standard for Dō01. It comes from Epic's installed **Unreal Engine 5.8 High/Characters template**, using `SKM_Manny_Simple` and its shared `SK_Mannequin` skeleton. The native packages were copied into `game/Content/Characters/Mannequins/`; source paths, sizes and SHA-256 hashes are recorded in [the original template inventory](../../../../artifacts/do01/manny-template-files.json).

## Preserved source

- Body LOD0: **92,178 triangles**, with two native materials (`MI_Manny_01_New` and `MI_Manny_02_New`).
- Native mesh reference hierarchy: **89 bones**. Blender represents the Unreal root bone with the `root` armature object and the other **88 bones** inside that armature.
- `Manny.blend` retains the exported body geometry, skin weights and rest skeleton. Detaching the FBX wrapper preserves the body and rig's rest-world placement: mesh and bone data remain in centimetres under the root object's **0.01 scale**, giving metre-sized Blender world coordinates. Do not apply a second centimetre-to-metre conversion.
- Blender preview materials use simplified neutral metal shaders. Unreal retains the native Epic materials and textures.

The fixture imports four existing template clips for fit review; these are not a newly authored animation library:

| Fixture alias | Native template clip |
| --- | --- |
| `A_Idle` | `Unarmed/MM_Idle` |
| `A_Walk` | `Unarmed/Walk/MF_Unarmed_Walk_Fwd` |
| `A_Run` | `Unarmed/Jog/MF_Unarmed_Jog_Fwd` — the original forward jog |
| `A_Attack` | `Unarmed/Attack/MM_Attack_01` |

Clip paths are relative to `/Game/Characters/Mannequins/Anims/`. `A_Run` is only an export alias; it does not claim a separate native run clip.

## Rebuild workflow

1. With the native template packages present, run [prepare_manny.py](../../Samurai/Do01/Scripts/prepare_manny.py) in ShoenEditor using a real rendering interface. It inspects the native mesh/skeleton and exports the body and existing clips into `Exports/`, without saving or retargeting the source packages. Run Unreal processes serially in this checkout.
2. Run [Scripts/build_fixture.py](Scripts/build_fixture.py) in Blender. It imports those FBXs with automatic bone orientation disabled, removes temporary animation-import objects and the FBX wrapper, installs the preview shaders, and writes `Manny.blend` plus [fixture-manifest.json](fixture-manifest.json).

Epic's assets retain their applicable Unreal Engine/Epic content terms. This fixture does not assign them a new license.
