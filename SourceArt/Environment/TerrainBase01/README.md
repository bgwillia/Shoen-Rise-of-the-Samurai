# TerrainBase_01

Native Unreal Landscape map: `/Game/Art/Environment/TerrainBase01/TerrainBase_01`.

Working heightmap: `TerrainBase_01.r16`, little-endian unsigned 16-bit, 505 × 505. Import at XY scale 297.6190476 cm and Z scale 100, with 63-quads sections, one section per component, 8 × 8 components. Footprint: 1,500 × 1,500 m; base elevations approximately 2.23–115.61 m. North is negative Y.

The visual revision replaces isolated mounds with connected, unequal ridge spurs and rolling shoulders. The central-east village shelf is softened to about 19.5 m, above the southern agricultural flats around 6–8 m. The downhill shoulder is separated by a shallow swale, and broad saddles break up the western ridge. Ground texture repetition and slope-color contrast are reduced. The user-supplied reference is preserved in `SourceArt/References/Environment/TerrainBase01/`.

The existing WaterBase_01 layout is preserved: both rivers, both pools, gravel island, zone and brush manager retain their positions, and all recorded spline points are unchanged. No foliage, roads, buildings or gameplay work was added. The map remains a native Landscape after removing the temporary import helper.

Recovered after the computer shutdown on September 16. Actual Unreal Metal captures are in `artifacts/terrainbase01/revision/`: `overview.png`, `top-down.png`, `strategy.png`, and `low-oblique.png`. No project tests or benchmarks were run for this terrain-only revision.

Unresolved: this is still a bare terrain foundation, below the reference’s finished visual quality. The village shelf is subtle from low angles, the broad valley remains visually sparse, and the local map boundary is visible at the distant river exit.
