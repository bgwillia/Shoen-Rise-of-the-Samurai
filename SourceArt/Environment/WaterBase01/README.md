# WaterBase_01

Integrated in the existing `/Game/Art/Environment/TerrainBase01/TerrainBase_01` map. Open that map in SHŌEN; the actors are grouped under `WaterBase_01`.

One native Water Body River follows the existing valley; one tributary enters from the west. Main-river spline points 10 and 25 define the two narrowed, shallow crossing candidates. Two small seasonal pools and a painted damp-ground mask establish the southern wet flats. Native water brushes make local bank/bed adjustments; the original terrain heightfield and surrounding hills are retained.

The scene uses native static water meshes with a muted translucent material, depth-softened margins and a supplied Unreal ripple normal. Scanned soil, gravel and mud textures provide surface variation; daylight and exposure were rebalanced. An inside-bend gravel bar uses a native Water Body Island brush. No vegetation or other dressing was added. Actual Metal overview, top-down, strategy and low-oblique captures are in `artifacts/waterbase01/`.

Unresolved visual issues: this remains below the reference's finished-game quality. Banks still look too uniform, gravel detail and crossing shallows are weak at strategy distance, the water lacks convincing reflection/depth variation, and the map boundary/background is visible. No project tests or benchmarks were run.


## Updated terrain fit — September 16

WaterBase_01 was refitted in the revised TerrainBase_01 map. The main river centerline and water elevation are retained. The tributary now has denser spline points fitted to the saved landscape surface; both pools have broader bank falloff and use the stream's shorter shallow-water edge fade. The two main-river crossing candidates retain 35 cm conceptual depth and approximately 18.5 m width. The revised terrain source heightmap, ground material and lighting are retained.

Latest actual Unreal Metal views: `artifacts/waterbase01/terrain-update/contact/` (`overview.png`, `top-down.png`, `strategy.png`, `low-oblique.png`). The lower tributary and pools are clearer, but the upper tributary still has visible interruptions at strategy distance; pool rims and the uniform main-bank treatment remain unfinished. No project tests, builds or benchmarks were run for this asset-only update.
