# LivestockYard_01

Open `LivestockYard01.blend` for the editable exterior modules. Run `Launch_LivestockYard01.command` to view the imported group beside FarmCompound in the saved Unreal settlement scene.

The shelter/roof, straight and corner fences, main gate, pen gate, feed trough, water trough, hay rack, hay bundles, baskets and soil apron remain separate reusable modules. Timber, thatch, plaster, rope, stone, water and feed props reuse the SHŌEN rural kit. One ground material adds vertex-painted wet/dry soil, a generated soil albedo, and the existing stone normal texture.

Visual limitations: repeated rail segments and tied hay bundles remain visible at close range; fine wear and surrounding terrain dressing are simpler than the reference. Pens are intentionally empty until separate livestock assets exist. No enclosed interiors or livestock gameplay.

Reference: the user's supplied `SourceArt/References/Buildings/LivestockYard01/LivestockYard01-reference.png`.

Soil albedo: `Textures/LY01_Soil_BaseColor.png`, made with built-in ImageGen for this asset. Prompt: seamless orthographic neutral-lit base-color texture of warm brown compacted livestock-yard earth, subtle damp hoof wear, fine granular detail, sparse tiny pebbles and pressed straw; about 2.5 m per tile; no objects, grass, perspective, cast shadows or text. Source model pass is followed by `Scripts/finish_soil.py` for the final texture and terrain seating.
