# Sode01 textures and shared material

Both shoulders use one **`M_Sode01`** material. It samples the existing three Dō texture assets; the import does not create or modify texture images.

| Texture source | Size / interpretation | Unreal asset |
|---|---|---|
| [T_Do01_BaseColor.png](../../Do01/Textures/T_Do01_BaseColor.png) | 2048×2048, sRGB | `/Game/Art/Characters/Samurai/Do01/T_Do01_BaseColor` |
| [T_Do01_Normal.png](../../Do01/Textures/T_Do01_Normal.png) | 2048×2048, linear OpenGL tangent normal | `/Game/Art/Characters/Samurai/Do01/T_Do01_Normal` |
| [T_Do01_ORM.png](../../Do01/Textures/T_Do01_ORM.png) | 2048×2048, linear: R occlusion, G roughness, B metallic | `/Game/Art/Characters/Samurai/Do01/T_Do01_ORM` |

The existing Unreal normal texture flips the green channel. Texture pixels are packed in `Sode01.blend`; external originals remain in Dō01. Source validation records dimensions, hashes and color spaces. Dō01 and Kabuto01 document the texture provenance.

## Atlas use

The 4×4 atlas uses `floor(U*4) + 4*floor(V*4)` in Blender coordinates. Unreal palette classification uses `floor(U*4) + 4*floor((1-V)*4)` to recover the source row after FBX import flips V; texture sampling keeps the imported UVs. Main lamella faces use the full tiles **8, 9, 13 and 14**, with local tile coordinates `(.06 + .88*u, .04 + .92*(1-f))`. Two short braided fastening tiers are separated by lacquer. Geometric ties on every fourth lamella align with the upper tier only. Lacquer uses tiles 0 and 10; brass 2 and 11; cord 3; leather 4; padding 12.

The current palette revision responds to the user's quality feedback while retaining the supplied shoulder design:

| Atlas tiles | Base-color multiplier |
|---|---|
| 0, 10 — lacquer | `(0.28, 0.29, 0.30)` |
| 3 — cord | `(0.38, 0.30, 0.28)` |
| 2, 11 — brass | `(0.85, 0.78, 0.67)` |
| All others | `(0.85, 0.85, 0.85)` |

`M_Sode01` multiplies the existing base color by that tile tint. Roughness is `clamp(ORM.G + 0.08, 0, 1)`; occlusion and metallic remain `ORM.R` and `ORM.B`. Normal strength is `0.65`, implemented as a normalized blend from flat tangent normal to the existing normal sample. Specular is `0.30`. The material is opaque and one-sided, with one section per shoulder mesh per LOD.

[import_unreal.py](../Scripts/import_unreal.py) creates this material only under Sode01, assigns it to both skeletal and static assets, and records shader parameters and dependency hashes. Current revision shader compilation and rendered appearance still require Unreal verification.

Major rows, the conforming medallion, twisted suspension ties and quilted padding relief are geometry. Atlas detail supplies the fine surface pattern. No new image generation or texture bake is part of this revision.
