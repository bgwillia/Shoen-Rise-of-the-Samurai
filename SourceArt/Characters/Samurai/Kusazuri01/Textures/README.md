# Shared texture setup

Kusazuri01 uses the existing 2048² Dō BaseColor, tangent Normal and ORM images at `SourceArt/Characters/Samurai/Do01/Textures/`. They are packed into the authoritative `.blend`. No new raster texture was generated.

`M_Kusazuri01` derives from the established `M_Sode01` finish. Lamella tiles8/9/13/14 carry the same woven fastenings, punched holes, small fittings, worn borders, roughness and normal detail as Dō01. Real geometry supplies plate thickness/overlap, representative matching cords, bindings and hem ornament.

Two textile changes follow the supplied Kusazuri reference:

- Tile12 receives an indigo multiplier `(0.10,0.18,0.48)` for the quilted lining. Only this tile overrides metallic to0, roughness to.90 and specular to0; the shared normal strength remains.65. This suppresses the pale grazing sheen observed in the underside review. Other atlas regions retain their original material inputs. Unreal accounts for the imported UV-V flip when selecting the tile.
- The obi uses the existing woven cord tile3, with actual two-strand braiding. The binary `ArmorTint` vertex-color R channel selects indigo for this object: black0 selects desaturated source color times `(0.08,0.18,0.50)`; white1 retains the existing palette. Thus panel laces remain red.

The variant has one opaque material section, no new texture allocation, and no transparency or cloth physics. The existing material and texture packages are preserved. BaseColor is sRGB; Normal and ORM are non-color. ORM channels are occlusion/roughness/metallic. Unreal retains the established normal green convention.

The atlas retains Dō/Kabuto provenance. Kusazuri review images are actual Blender/Unreal renders, not generated illustrations.
