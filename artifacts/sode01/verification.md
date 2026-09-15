# Sode01 — verified paired asset and quality revision

## Result and visual quality

Both `Sode_L_01` and `Sode_R_01` are authored, exported and imported on the existing Epic Manny skeleton. The user's follow-up rejected the original finish while retaining the design. The revision preserves the proportions and five-row outline, but replaces the flat repeated plate treatment with Dō's worn lacquer, recessed holes and properly proportioned braided fastenings. It also adds conforming metal relief, twisted suspension cords, compact knots, gathered tassel ends and a formed padded interior.

The final finish is coherent with Kabuto01 and Dō01. Repetition, ornament and suspension remain simpler than the reference sheets. See the independent [visual assessment](visual-review.md), [Blender fitted view](../../SourceArt/Characters/Samurai/Sode01/Review/Captures/fit-refined.png), and actual [Unreal detail](final-detail.png). These are renders of the real meshes, not generated concept images. Human approval of the revision is not claimed.

## Blender source, counts and materials

Editable source: [Sode01.blend](../../SourceArt/Characters/Samurai/Sode01/Sode01.blend). The source has **16 construction objects**, eight per side, plus separate fit fixtures, hidden runtime copies and review lights/camera. The full source was preserved by saved-source export.

| Asset | Source triangles | Runtime LOD0 | LOD1 | LOD2 | Material slots per LOD |
| --- | ---: | ---: | ---: | ---: | ---: |
| Sode_L_01 | 60,098 | 36,058 | 13,192 | 3,982 | 1 |
| Sode_R_01 | 60,098 | 36,058 | 13,196 | 3,994 | 1 |
| **Pair** | **120,196** | **72,116** | **26,388** | **7,976** | **2 sections, 1 shared material** |

Each runtime side combines its editable regions into one section. LODs derive independently from full evaluated source at approximate 60%/22%/7% ratios. LOD0's measured axis bounds are unchanged; the largest LOD2 axis-bound change is 1.68 mm. Counts match both imported static readback and actual rendered skeletal mesh inventory.

`M_Sode01` shares the existing Dō 2048² BaseColor, tangent Normal and ORM textures. It adds **zero new texture images** and uses one shared finish material. [Shader settings and provenance](../../SourceArt/Characters/Samurai/Sode01/Textures/README.md). Source normals, UVs, closed topology, positive winding, normalized weights and actual evaluated corner normals pass [source validation](source-validation.json).

## Left/right correctness and Unreal assets

`Sode_L_01` is the **wearer's left**, Blender/native mesh +X, weighted to `upperarm_l`. `Sode_R_01` is the **wearer's right**, −X, weighted to `upperarm_r`. Positive transforms, side-specific bone weights and imported bounds all pass. The original native root scale `.01` is intentional; no negative object mirror is used.

Unreal assets: `/Game/Art/Characters/Samurai/Sode01/SK_Sode_L_01`, `SK_Sode_R_01`, and `M_Sode01`; the review map and static copies live under `Review/`. Both skeletal meshes reuse the exact existing 89-bone reference including the object root. No new skeleton is created. [Import readback](unreal-import.json) records all twelve export hashes, reference-transform tolerances and unchanged hashes for Manny, native clips, Kabuto, Dō and shared textures.

## Fit, attachment and animation

Rigid plates carry 100% weight on the corresponding upper-arm bone. The two suspension braids blend that bone with `spine_05` at the Dō strap. The supplied stateless suspension controller copies the body's complete pose into a separate component using the same skeleton, filters axial twist, then adjusts only the Sode upper-arm transform for swing/opening/lift. It preserves rigid panel dimensions and adds no temporal lag or physics. **The controller is required; ordinary upper-arm leader pose alone does not reproduce this fit.** [Runtime integration](../../SourceArt/Characters/Samurai/Sode01/Runtime.md).

The final [Blender pose measurements](pose-review.json) sample sixteen poses: neutral, forward arms, raised arms, diagnostic bow, idle at two frames, walk/jog at three frames each and unarmed attack at four frames. Every sampled rigid panel is clear of the body, Dō and Kabuto; maximum sampled pair-distance error is **0.0000007275 m**. This is sampled surface evidence, not a continuous collision guarantee.

Remaining measured contacts are confined to flexible suspension: bow diagnostic against body/Dō (112/73 intersecting triangle pairs), jog frames23/40 against Dō (42/9), and attack frame12 against body (51). Triangle-pair counts are not penetration depths. Existing Dō/Kabuto behavior is preserved. A native bow-use clip is unavailable; the bow images are labeled static diagnostics without a weapon.

The compiled native suspension test passed **32 frozen Blender targets**, both sides in all sixteen poses, including unit scale, exact lateral elevation, axial-twist invariance and zero-length direction rejection. [Fixture provenance](suspension-fixture-refresh.json) confirms zero numerical change after the geometry revision.

## Actual rendered review

Fourteen final Unreal views/motion checks validated real **Metal rendering**, screenshot output, correct components, existing skeletons and attachment transforms. Native idle/walk/jog/attack clips advanced during their runs. Maximum controlled transform errors across the reports are recorded in each JSON; close idle measured 0.0000000361 cm position and 0.00394° rotation. Transform agreement does not establish hidden surface clearance.

| View | Captures |
| --- | --- |
| Front/back | [Front](final-front.png), [back](final-back.png) |
| Side proof | [Wearer left](final-left.png), [wearer right](final-right.png) |
| Three-quarter | [Front](final-close-idle.png), [rear](final-rear.png) |
| Detail/distance | [Detail](final-detail.png), [tactical](final-tactical.png) |
| Native motion | [Walk](final-walk.png), [jog](final-run.png), [attack](final-attack.png) |
| Diagnostics | [Raised arms](final-arms-raised.png), [forward arms](final-arms-forward.png), [bow](final-bow.png) |

Source close-ups: [L outside](../../SourceArt/Characters/Samurai/Sode01/Review/Captures/Sode_L_01-outside.png), [L inside](../../SourceArt/Characters/Samurai/Sode01/Review/Captures/Sode_L_01-inside.png), [R outside](../../SourceArt/Characters/Samurai/Sode01/Review/Captures/Sode_R_01-outside.png), [R inside](../../SourceArt/Characters/Samurai/Sode01/Review/Captures/Sode_R_01-inside.png). Root additionally inspected the forward-arm and right outside images; the independent visual report enumerates its thirteen inspected engine images separately.

## Incremental performance sanity check

One character, Mac M1 Max / 32 GB, UE 5.8.2 Development editor-game, **actual 1280×720 Metal viewport** (1600×900 requested, actual viewport constrained by the display). Fifteen measured seconds per run after three-second warmup, no VSync. All six modes ran serially with other coordinated Blender/build/Unreal work held. Close/tactical comparisons use identical framing within each camera and the same advancing native idle. [Run summary](performance-runs.json); raw `cost-*.json` reports and exact command files are alongside it.

| Camera | Equipped state | Median FPS | Frame median ms | Frame p95 ms | Frames |
| --- | --- | ---: | ---: | ---: | ---: |
| close | mannequin | 69.9 | 14.304 | 16.694 | 1054 |
| close | armor | 59.0 | 16.948 | 21.660 | 887 |
| close | sode | 57.5 | 17.394 | 21.786 | 869 |
| tactical | mannequin | 64.9 | 15.420 | 19.054 | 986 |
| tactical | armor | 62.3 | 16.048 | 19.422 | 952 |
| tactical | sode | 61.4 | 16.296 | 20.370 | 940 |

Adding both Sode versus Kabuto+Dō increased observed frame median by **0.446 ms close** and **0.249 ms tactical** (about 2.6% and 1.5%). No obvious incremental hitch/regression appeared in this bounded check. These are sequential single-run observations, not confidence-bounded causal estimates or battlefield capacity. Thermal/background variation is not controlled. Engine RHI draw-call/primitives counters were unavailable on this setup. Baseline framing loads the same armor assets, so process-memory differences do not measure total asset residency; no texture-memory reduction is inferred.

## Verification and preservation

- [67/67 tooling tests](tooling-final.log) passed, including ten Sode-specific tests.
- [6/6 portable CTest targets](core-final.log) passed.
- [Unreal build](build-final.log) succeeded in 29.41 seconds.
- [Full Unreal automation summary](unreal-tests-summary.json): **20/21 passed**, including Sode and all prior foundation/gameplay suites. The one failure is the concurrent, separately owned `Shoen.Art.Kusazuri.HingesMatchBlender`: its not-yet-created fixture was unreadable. That task acknowledged the unfinished fixture and owns its final test. The shared build included that task's syntactically complete code; those files are excluded from this Sode commit.
- Strict source validation and import passed; actual rendered review is separate from NullRHI automation/import.
- Independent code review found no blocking Sode issue. It flagged baseline asset residency and limited animation-advancement evidence, reflected above.

The committed Dō/Manny baseline is `6dbc613`; this task preserves those assets, the native reference skeleton, Kabuto and gameplay. It preserves the design package, workbook and unrelated working-tree changes, including the user's separate Kusazuri task. Files named `before`, `initial`, `controlled-first`, `lateral-opening`, `quick` or `diagnostic` are earlier debugging evidence, not final acceptance results. The medallion bevel collapse and LOD2 inward islands were repaired without weakening validation; generated LOD repair records are in the manifest.

Final source SHA-256: `009e3fd8ba1f89119f874e94673b2abee187284e1e386e23eb77acbbea3f0d9a`. [FILES.sha](../../SourceArt/Characters/Samurai/Sode01/FILES.sha) covers the saved source, manifest and exports. Source/pose hashes match; the separate pre-export source hash records the input before hidden runtime copies were saved.

## Follow-up unity-build correction

After the asset commit, the shared unity build exposed four anonymous-namespace names that collided with Dō when Unreal compiled the files together. Commit `8ff7bb2` prefixes the Sode constants/functions and all their uses; it changes identifiers only. Independent scanning found no additional Sode helper collisions.

The separate Kusazuri task then ran the serialized shared build successfully: **exit 0, 24.98 seconds wall time** (Unreal reports 24.34 seconds internally). `Module.Shoen.cpp` compiled with Sode in the unity unit, the separate Kusazuri source compiled, and the editor library linked. [Copied build log](unity-build-after-fix.log), [result and provenance](unity-build-after-fix.json). This closes the unity-build verification gap; it does not represent a new animation or automation run.

## Limitations and pipeline assessment

The atlas and lamella rhythm remain regular; ornament and knots are simpler than the sheets. Suspension arcs are conspicuous and raised-arm poses look lifted rather than gravity driven. Flexible tie contact remains in the listed poses. The preview controller is an isolated art integration example, not production battlefield equipment wiring. No human motion/visual acceptance, continuous clearance or full-army performance is claimed.

Building the pair together kept dimensions, palette, topology logic and motion rules consistent while validating each anatomical side separately. **Kusazuri** is the recommended next component; the user is already pursuing it in a separate task. This task's authored assets stop at the Sode pair.
