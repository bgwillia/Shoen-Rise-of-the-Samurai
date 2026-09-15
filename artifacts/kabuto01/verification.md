# Kabuto 01 — asset and rendered verification

2026-09-15. Scope: one helmet, an unchanged mannequin fit fixture, and an opt-in art review scene. The existing gameplay presentation remains unchanged. [Request](../../docs/execution/kabuto01-request.md) · [Asset README](../../SourceArt/Characters/Samurai/Kabuto01/README.md).

## Visual result and reference comparison

The user's rejection of the first pass was about execution quality, not its design. The revision keeps the crescent, rounded bowl, turn-backs and flared neck guard. It improves surface curvature, raised ridge/rivet definition, plate overlap and rolled edges, a raised flower medallion, the crest's physical mounting shoe, cord weave, and separation between lacquer, brass, cord and leather. The [rejected first pass](iterations/first-pass/blender-hero.png) is retained for comparison with the [final actual Blender render](../../SourceArt/Characters/Samurai/Kabuto01/Review/Captures/blender-hero.png).

All review pictures are actual Blender or Unreal renders of the asset. Built-in ImageGen supplied only flat material swatches; [saved source and exact prompt](../../SourceArt/Characters/Samurai/Kabuto01/Textures/Source/prompt.txt). These are artist approximations, not scanned PBR measurements. The 2K atlas combines the swatches with procedural lacing, roughness, micro-normal and contact/pore AO; it is not a sculpt-to-low-poly bake.

| Reference feature | Observed result / difference |
|---|---|
| Front silhouette and crest | Broad crescent, central round medallion, pronounced brow and upturned side panels retained. Medallion carving and mount are simplified; crest thickness is visible in side view. |
| Side silhouette and head proportion | Bowl follows the actual original head. Five neck plates flare rearward and clear the face in the reviewed poses. The crest has a visible bent support instead of floating ahead of the bowl. |
| Rear and neck guard width | Continuous curved overlapping rows, wider toward the bottom. The repeated lacing still looks flat in places and too mechanically regular. |
| Top and turn-back angle | Radial segmentation, crown opening and symmetrical swept side panels read clearly. No attempt to reconcile contradictory tiny ornaments across the generated reference sheets. |
| Color and construction | Dark lacquer, aged warm brass, burgundy cord, brown padding. Fittings remain more uniform and the finish simpler than the rich hero reference. |
| Interior | Open head volume and padded rim are visible in the underside render. Neutral-fit checks support skull clearance, not every possible animated neck/shoulder pose. |

Priority was the 3D sheet's hero crescent/red cord, then front/side construction and rear/top. This is a closer and more controllable component result, but not a claim of reference-quality finish or user visual acceptance.

## Source, export and import

- Authoritative source: [Kabuto01.blend](../../SourceArt/Characters/Samurai/Kabuto01/Kabuto01.blend), Blender 5.1.2. Eleven logical source meshes, one opaque material atlas with four surface classes. Bowl, brow and padding retain useful thickness/bevel modifiers; other details are editable mesh parts.
- Source before modifiers: **82,864 triangles**. Evaluated source / FBX LOD0: **94,664**. Unreal imported LOD0: **94,608**; import cleanup removes 56 triangles. LOD1 **31,238**, LOD2 **7,062**. Each runtime LOD has one material section. Inspection LOD0 is expensive; it is not a sensible all-distance army mesh. [Manifest](../../SourceArt/Characters/Samurai/Kabuto01/asset-manifest.json).
- Three 2048² textures: BaseColor (sRGB), tangent Normal, ORM (linear). Normal green is flipped on Unreal import. Opaque, one-sided shader; no cloth, transparency or helmet skeleton.
- Unreal asset: `/Game/Art/Characters/Samurai/Kabuto01/SM_Kabuto01`. Bounds including crest and cord: **33.654 × 34.520 × 43.025 cm**. Source metres map to Unreal `(100x, -100y, 100z)` centimetres; component yaw −90° aligns the character forward axis.
- The original prototype's gray body, head, rig and idle/walk clips are embedded unchanged as a review fixture. No formal imported production mannequin existed; ordinary gameplay used instanced placeholders. Head width is **18.2 cm**, pivot **157 cm** above source ground. Matching body/head geometry hashes are recorded in [source validation](source-validation.json).

The saved `.blend` exports directly without reconstructing the design. A temporary-copy test moved one crest vertex 2 mm, exported it and verified the edit survived and runtime geometry changed: [export preservation](export-preservation.json). Production source was unchanged by that test.

## Verification performed

| Check | Result / evidence |
|---|---|
| `python3 tools/dev.py core-test` | 6/6 CTest targets pass; 115.58 s. [Log](core-tests.log). |
| `python3 -m unittest discover -s tools/tests -v` | 51/51 pass; 9.201 s. [Log](tooling-tests.log). |
| `python3 tools/dev.py build` | ShoenEditor Mac Development succeeded; 11.57 s. [Log](build.log). |
| `python3 tools/kabuto.py validate` | 151/151 source checks pass, including finite geometry/UVs, closed parts, no duplicate faces or zero-area triangles, textures, unchanged fit and decreasing LODs. [Report](source-validation.json). |
| `python3 tools/kabuto.py import` | Scale, assets, textures, material slots and LOD checks pass. **NullRHI import checks do not establish rendering.** [Report](unreal-import.json). |
| Five animated/poseable close runs | Actual Metal rendering; all runtime assertions pass and screenshot files exist. See below. |
| Nine tactical comparisons + far run | Actual Metal rendering, requested counts present; all runtime assertions pass. Raw JSON/CSV and launch commands retained. |

Neutral source checks found zero helmet/head surface intersections and zero forward eye-ray obstructions. Sampled minimum skull-to-bowl clearance is **19.886 mm**; padding clearance **11.962 mm**. These checks do not certify peripheral vision, cloth behavior or inter-part intersections. Independently closed trim/cord parts intentionally overlap.

No new full Unreal regression-automation run was claimed for this art task. Existing portable tests plus the current build and opt-in runtime review passed. Earlier import tangent artifacts were corrected; the final import contains no helmet tangent/binormal warning. Existing engine compression/audio and deprecated editor API warnings remain; see the retained [import diagnostic excerpt](import-diagnostics.txt).

## Attachment and inspected captures

The rigid helmet attaches to `head`. Its relative transform cancels the imported composed head reference rotation and scale, yielding helmet world scale `(1,1,1)` and zero attachment-position drift in all five sampled runs. The source rig has 63 bones; the FBX importer adds the `FIT_Rig` root (64 total). The head sweep reached **40.27° from its first sample**; the programmed sweep is ±38°, so this metric is excursion from the sampled start, not an absolute angle limit. Walk uses the existing one-second clip and has almost no independent head rotation; idle and explicit head sweep supply that coverage.

- [Close idle](close-idle.png) · [front idle](front-idle.png) · [side walking](side-walk.png) · [rear idle](rear-idle.png) · [head turn](close-head-turn.png).
- Blender [rear](../../SourceArt/Characters/Samurai/Kabuto01/Review/Captures/blender-rear.png), [top](../../SourceArt/Characters/Samurai/Kabuto01/Review/Captures/blender-top.png), [interior](../../SourceArt/Characters/Samurai/Kabuto01/Review/Captures/blender-interior.png).
- Tactical [100](helmet-100-tactical.png), [500](helmet-500-tactical.png), [1,000](helmet-1000-tactical.png); [far 1,000](helmet-1000-far.png).

Close camera: 1.3 m, horizontal FOV 40°, elevation 15°. Bowl ridges, crest, plate edges and materials are readable. Tactical: 110 m, FOV 55°, elevation 60°; helmets contribute a dark head silhouette and occasional gold pixels, while lace/medallion detail cannot reliably identify units. Far: 310 m, same FOV/elevation; formation mass remains visible, individual helmet detail does not. All ten formations are within the final 1,000-body tactical frame. Review map objects spawn on BeginPlay: press **Play** or use the CLI, rather than judging an empty editor map.

## Rendered performance sanity check

M1 Max / 32 GB, Unreal 5.8.2 Mac Development editor-game, Metal. Actual viewport **1280×720**, despite a 1600×900 launch request. Three-second warmup, then approximately 12 seconds sampled per tactical case, one Unreal process at a time. Screenshot readback occurs after timing. These are static instanced crowds using one body and one helmet component per 100-person formation, not animated armies or combat. The close tests render one skeletal/poseable body regardless of their default requested crowd count.

| Bodies | Placeholder median FPS | Mannequin median FPS | Mannequin + helmet median FPS | Helmet increase in median frame time vs mannequin |
|---|---:|---:|---:|---:|
| 100 | 119.5 | 117.9 | 108.3 | +0.752 ms / +8.9% |
| 500 | 113.7 | 94.2 | 89.4 | +0.565 ms / +5.3% |
| 1,000 | 117.5 | 77.7 | 63.5 | +2.878 ms / +22.4% |

The median is the reciprocal of median frame interval, not total frames divided by elapsed time. Both are exposed below so pauses are not hidden.

| Raw report | Frames | Frames / elapsed seconds | Frame p95 / worst ms | GPU median ms |
|---|---:|---:|---:|---:|
| [placeholder 100](placeholder-100-tactical.json) | 1,379 | 114.9 | 10.102 / 109.123 | 7.969 |
| [mannequin 100](mannequin-100-tactical.json) | 1,348 | 112.3 | 10.301 / 90.727 | 7.989 |
| [helmet 100](helmet-100-tactical.json) | 1,268 | 105.6 | 10.992 / 23.359 | 8.715 |
| [placeholder 500](placeholder-500-tactical.json) | 1,219 | 101.6 | 15.158 / 17.193 | 8.263 |
| [mannequin 500](mannequin-500-tactical.json) | 1,064 | 88.6 | 15.655 / 40.880 | 10.045 |
| [helmet 500](helmet-500-tactical.json) | 1,026 | 85.5 | 16.237 / 17.949 | 10.626 |
| [placeholder 1,000](placeholder-1000-tactical.json) | 531 | 44.2 | 43.685 / 1085.734 | 7.941 |
| [mannequin 1,000](mannequin-1000-tactical.json) | 933 | 77.7 | 16.355 / 25.511 | 12.341 |
| [helmet 1,000](helmet-1000-tactical.json) | 721 | 60.1 | 21.213 / 65.934 | 15.252 |

Each report has a same-stem `.csv` with individual samples and `-command.json` with the exact launch arguments. Game/render CPU counters and RHI GPU times are recorded separately. Metal draw-call and primitive counters returned zero/unavailable and are recorded **null**; mesh LOD inventory is not a GPU draw count. The 1,000 case has ten added helmet ISM components, not a claim of ten actual draw calls.

The latest 1,000-placeholder run has a **1,085.734 ms** worst frame and only **44.2 frames/s over the interval**, despite a 117.5 median. Its median is a poor standalone baseline. A preceding comparison is preserved in [iterations/pre-mount-comparison](iterations/pre-mount-comparison/): helmet medians were 79.9 / 54.1 / 46.2 FPS, and mannequin-100 suffered a **2,761.426 ms** frame. That version had nearly identical geometry, preceding the final crest support.

Before the repeat, an orphaned Unreal CrashReportClient from a prior failed process was found with PPID 1 at 100% CPU and terminated; its crash files were preserved. Other system/background activity remained uncontrolled. The repeat improved, but these observations cannot attribute all stalls to that process or establish statistical confidence. Both runs are retained. No further optimization cycle was undertaken.

**Conclusion:** one opaque section and instanced attachment are viable for this feasibility review, but helmet geometry has a measurable cost: at 1,000 the final mannequin-to-helmet median rises **2.878 ms (22.4%)**, with a **21.213 ms p95** frame. The expensive inspection mesh and high remaining distant LOD count need consideration before wider art rollout. These data do not certify full-army frame budgets.

## Reproduce and inspect

From the repository root, use `python3 tools/kabuto.py export`, `validate`, and `import` sequentially. `export` consumes saved edits; `source` intentionally rebuilds/overwrites the authored source from its construction script. Build before launching the C++ review mode.

```sh
python3 tools/kabuto.py review --camera close --animation idle --seconds 6 --label close-idle
python3 tools/kabuto.py review --camera side --animation walk --seconds 6 --label side-walk
python3 tools/kabuto.py review --camera close --animation head --seconds 6 --label close-head-turn
python3 tools/kabuto.py review --mode helmet --count 1000 --camera tactical --seconds 12
python3 tools/kabuto.py review --mode helmet --count 1000 --camera far --seconds 6
```

Use `--seconds 0` for an interactive persistent review. The same tactical command with modes `placeholder`, `mannequin`, `helmet` and counts `100`, `500`, `1000` reproduces the comparison. Blender extra-view and saved-edit checks are in the asset's `Scripts/` directory. Their final executions exited 0.

Kabuto 01 ends here. No additional armor, body edits, gameplay integration or next component was started.
