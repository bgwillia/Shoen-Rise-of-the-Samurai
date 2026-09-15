# SHŌEN — Kabuto01

One rigid helmet for the component art feasibility test. The gray body, rig and existing clips are review fixtures; gameplay is unchanged. [Verification and captures](../../../../artifacts/kabuto01/verification.md) document the measured result, not visual acceptance.

## 1. Visual result

The **3/4 hero in `samurai_kabuto_3d_reference_sheet.png` takes priority**, followed by front, side, back, top and details. Its crescent/red cord resolve the first sheet's small crest/blue lacing. Reference dimensions are approximate.

| Comparison | Construction / limitation |
|---|---|
| Front | Rounded ribbed bowl, projecting brow, crescent and raised eight-petal medallion. |
| Side | Five plates flare downward/backward; upper edges recess 4 mm for overlap. |
| Rear | Curved rows; repeated flat lacing with representative geometric fastening pairs. |
| Top | Symmetrical radial ridges and crown fitting; regular, simplified ornament. |
| Neck width | Flared coverage around the preserved head; overall helmet width 33.65 cm. |
| Crest | Rounded petals, recessed field, raised bezel, bent mounting shoe and two saddle bolts. |
| Head proportion | Fitted around the unchanged 18.2 cm-wide head. |
| Side angle | Outward turn-backs, geometric knots and thicker bindings. |
| Colors | Dark lacquer, aged brass, dark red cord and brown padding; simplified finish. |

[Blender captures](Review/Captures/) include hero, fit, runtime-fit, rear, top and interior views. These show actual scene renders.

## 2. Blender asset

**[Kabuto01.blend](Kabuto01.blend) is authoritative** (Blender 5.1.2). Eleven editable parts: `Hachi`, `Hachi_Fittings`, `Mabisashi`, `Mabisashi_Edge`, `Shikoro`, `Fukigaeshi_L`, `Fukigaeshi_R`, `Maedate`, `Uchiwa`, `Padding rolled rim`, `ShinHimo`. The crest remains replaceable.

| Helmet geometry | Triangles |
|---|---:|
| Source before remaining modifiers | 82,864 |
| Evaluated source / exported LOD0 | 94,664 |
| Unreal LOD0 | 94,608 |
| Export / Unreal LOD1 | 31,238 |
| Export / Unreal LOD2 | 7,062 |

[Manifest](asset-manifest.json) and [import report](../../../../artifacts/kabuto01/unreal-import.json). Some source parts already contain applied modifiers. Unreal cleanup removes 56 LOD0 triangles. **LOD0 retains full inspection detail at high cost**; distance LODs provide reduction. Each plate has six three-pair texture repeats and six representative geometric fastening pairs.

**One opaque atlas material covers four surface classes.** Three packed/external **2048² PNGs**:

- **BaseColor:** linear reflectance explicitly encoded to sRGB PNG and reloaded; Unreal sRGB.
- **Normal:** non-color derived/analytic tangent relief, OpenGL +Y; Unreal flips green, strength 0.65.
- **ORM:** non-color R = procedural pore/contact AO, G = roughness, B = metallic.

This is not a sculpt bake. Lacquer is dielectric. No transparency or cloth simulation.

## 3. Unreal asset and attachment

Asset: `/Game/Art/Characters/Samurai/Kabuto01/SM_Kabuto01`; fixtures/map under `Review/`. Press **Play** or use the CLI to spawn the review scene. Import verified **one section per LOD**, one material, **33.65 × 34.52 × 43.03 cm** bounds and existing idle/walk clips (60/30 frames).

No imported/formal standard mannequin existed at inspection. The gray fixture preserves geometry from untracked `Prototype01/Samurai01.blend`: **63 source bones / 64 imported**, including the FBX rig root. It is not a certified retarget standard.

Blender uses metres, +X left, −Y forward, +Z up; head pivot `(0,0,1.57)`. Helmet vertices export relative to that pivot. Import uses `convert_scene=False`, `convert_scene_unit=True`: `(x,−y,z)×100` centimetres. Component yaw −90° aligns +Y with game-forward +X.

The composed Unreal head reference measures **157 cm height, 90° roll, scale 100**. Attachment cancels reference rotation **and scale**, with zero translation. Final close-idle/front-idle/side-walk/rear-idle/head-turn checks passed at **1280×720**, with screenshots, **zero measured attachment drift and world scale 1**.

## 4. Performance

Final tactical median FPS, M1 Max/32 GB, Mac/Metal, UE 5.8.2 Development editor game, **1280×720**, three-second warmup then twelve-second samples:

| Count | Placeholder | Mannequin | Mannequin + helmet |
|---|---:|---:|---:|
| 100 | 119.46 | 117.93 | 108.32 |
| 500 | 113.67 | 94.18 | 89.43 |
| 1,000 | 117.48 | 77.65 | 63.47 |

Crowds use static instances grouped by 100. Cameras: close 1.3 m/40°, tactical 110 m/55°, far 310 m/55°. Screenshots occur after sampling.

**Medians conceal stalls:** placeholder-1,000 had 43.68 ms frame p95 and a **1.086 s** worst frame, averaging only 44.2 frames/s over the interval. The archived pre-mount mannequin-100 run stalled **2.761 s**. An orphan Unreal crash reporter was terminated before repetition; these observations do not identify every cause. Helmet-1,000 had 21.21 ms p95 and 65.93 ms worst frame. See [evidence](../../../../artifacts/kabuto01/verification.md) before drawing comparisons. Static art runs do not measure animated armies/combat; NullRHI import measures no rendering performance.

## 5. Pipeline and provenance

Scripts automate parametric construction, atlas processing, export, validation and import, revised from actual renders; no manual sculpt pass.

**Built-in ImageGen generated four flat material swatches only, not review renders.** Retained [sheet](Textures/Source/Kabuto01_MaterialSwatches.png): **1254 × 1254 pixels**; [exact prompt](Textures/Source/prompt.txt). Blender resamples/processes these into the 2K atlas with analytic lacing, derived micro-relief/roughness and procedural AO. Scene lighting is not baked.

**Save Blender edits**, then from repository root:

```sh
python3 tools/kabuto.py export
python3 tools/kabuto.py validate
python3 tools/dev.py build
python3 tools/kabuto.py import
python3 tools/kabuto.py review --camera close --animation head --seconds 10
python3 tools/kabuto.py review --camera tactical --count 1000 --mode helmet --seconds 30
```

Run one Unreal process; exclude heavy work during timing. `source` **overwrites manual edits**. `export` preserves them: a [temporary-copy test](../../../../artifacts/kabuto01/export-preservation.json) retained a **2 mm crest edit** and changed runtime output.

SHA-256 provenance:

- User reference ZIP: `aecce5beecfa2ecc2c27329a6ffdee032c5bbb5569a600bcb306e19d51b75438`.
- Legacy Blender source: `8ef9b52e33a70196616add1b71522dd643a7c2429d2a577687193777ed1a9917`.
- Preserved body geometry: `46adab1d763b74c084c996c0fc0a8fc976c578b77693c6d252e71ebe528486bb`.
- Preserved head geometry: `67b618e44b3060beb7707edcfe784a53306ef8ca840b7a458ba60d2c85fb1283`.

No external meshes/animations were acquired. Generated material bases are disclosed above. User concept art is not historical certification.

## 6. Problems and limits

[Source validation](../../../../artifacts/kabuto01/source-validation.json), Unreal build, **6/6 portable** and **51/51 tooling** checks passed. Neutral-fit checks do not certify every animated clearance. Earlier normal/UV issues were corrected; the final import has no helmet tangent/binormal warnings.

Repeated flat lacing, regular fittings and simplified finish remain; technical checks do not establish polished/reference-quality art.

## 7. Recommendation

Keep component-by-component authoring with preserved anatomy and inspect each component in Blender and Unreal. This helmet establishes a reviewable workflow; production quality still requires human visual judgement. Stop at Kabuto01.
