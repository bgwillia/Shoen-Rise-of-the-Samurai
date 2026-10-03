# Tachi 01

Editable source: `Tachi01.blend`. The twelve named component meshes retain the blade, fittings, wrap, saya and cords separately. Textures are packed. Black lacquer, woven silk and aged brass derive from the existing Dō material atlas.

Unreal: open `/Game/Art/Characters/Samurai/Tachi01/Tachi01_Fitted`. It contains the existing samurai with the sheathed Tachi attached to `pelvis`. To preview the drawn setup, hide the sheathed actor and show the separate saya and drawn actors; the drawn sword attaches to `hand_r`. All three reusable static meshes share the guard-center pivot and real metre-to-centimetre scale. The original skeleton is unchanged.

Source views are in `Review/`; the actual Unreal on-character image is `artifacts/tachi01/unreal-on-character.png` at the repository root. The Unreal import and capture completed on 2026-09-15.

Remaining visual limitations: engraving is sparser and the finish cleaner than the reference; the hamon is somewhat regular; sageo knots retain a posed appearance. The existing neutral hand pose is not a gripping or drawing animation.
