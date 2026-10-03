# RoadsPaths_01

Open `/Game/Art/Environment/TerrainBase01/TerrainBase_01`. The network retains one main road, village branches, four farm tracks, two map exits, one timber bridge and one tributary ford.

## Visual revision after user feedback

Road surfaces now blend directly into a copy of the existing Landscape material. The authored 8K weight mask supplies irregular shoulders, subdued packed earth, worn village dirt, soft farm tracks and faint wheel wear. This removes the floating strips and their distance-dependent gaps. Original native spline segments remain hidden, editor-only, in `RoadsPaths_01/AuthoringSplines`; `layout.json` remains the authored route source.

The bridge uses reusable beveled timber pieces, the existing RuralHouse01 weathered timber material, slight plank variation and cross-beams. Sloped earth shoulders replace the exposed block approaches. The ford has irregular cobbles, a submerged gravel bed and a localized transparency adjustment to the tributary material. The original terrain heightfield and water geometry are retained.

Latest actual Unreal Metal captures: `artifacts/roadspaths01/revision/` — overview, top-down, strategy, low-oblique, road-detail, bridge and ford. Earlier captures are preserved separately. No game-wide tests, profiling, vegetation, agriculture or gameplay systems were added.

Source: `layout.json`, `author_surface_mask.py`, `TimberBridge_01_pieces.blend`, `Exports/`; the editor revision scripts record assembly. Reused soil textures retain WaterBase01/Textures/SOURCES.md provenance; timber and stone materials come from RuralHouse01. The user's reference remains under SourceArt/References/Environment/RoadsPaths01/.

Remaining: this is a bare environment foundation and still below the reference's complete scene quality. No buildings are placed in this map, so entrance connections remain provisional. Short grades still reach roughly 14° on the main road and 13° near the ford branch. Crossings and the surrounding ground need further art refinement for final production quality.
