# Kusazuri01 final motion and source capture review

## Reviewed source

Source SHA-256: `cf7c0ec0578b7fe2aca7d1b30439c521e8cecc3e63d4f36b0c8820b31dc9eb9e`.

The full production sweep contains 372 poses: every integer frame of the saved idle, walk, run and attack actions (363 frames), plus nine authored diagnostic poses. These are Blender source measurements and still captures, not Unreal performance or continuous/subframe clearance tests. No source or controller edits were saved by the review.

## Actual final capture inspection

The 44 component, outfit and motion captures and four contact close views are 900×900 PNGs, rendered at 16 Cycles samples with two Blender threads. `final-capture-validation.json` records every image hash and verified size; `capture-manifest.json` and `capture-contact-closeups.json` record poses and cameras.

- `threequarter-front.png`, `outfit-front.png` and `outfit-threequarter.png`: the dense lamellar construction, repeated red fastening cords, brass edging and blue braided obi now read as part of the existing Do/Kabuto/Sode outfit. The neutral belt transition is dark and continuous. Shortened tassel tails preserve the knot arrangement.
- `underside.png`: backing reads dark navy/indigo, with subtle quilt/fastening relief. The earlier pale gray/beige response is absent in this final image.
- `pose-A_Attack-13.png`, `pose-A_Run-22.png`, `pose-A_Run-32.png`, `pose-A_Run-39.png` and `pose-A_Walk-19.png`: the previously failing leg-contact frames are retained as direct regression evidence. All five have zero measured leg triangle pairs in the final sweep.
- `contact-close-A_Run-31.png` and `contact-close-A_Run-40.png`: no broad exposed body breakthrough is apparent in these views. The measured contacts remain near concealed lining/inner plate edges and must not be treated as cleared solely because they are difficult to see.
- `contact-close-knee-lift.png` and `contact-close-knee-lift-side.png`: the front panels open strongly over the raised thigh. The limited inner-edge contact remains measurable; the belt and obi are clear. The side view partly occludes the contact area with the unchanged hand, so the geometry measurements carry more weight than visibility alone.
- `pose-bow-diagnostic.png`: demonstrates the authored combat/bow posture with the existing Sode suspension. It is not a native bow animation or a weapon-clearance test.
- `tactical-distance.png`: the dark skirt silhouette, division into hanging sections and colored bands remain visible; individual fasteners are too small to assess at this distance. This image is not a crowd-performance measurement.

Compared with the supplied Kusazuri reference sheet, the final piece preserves the seven-part hanging arrangement, dark plates, red fastening rhythm, blue obi and brass hems. Its ornamental hem motifs remain simpler and thinner than the more elaborate reference motifs. The captured material and construction now match the neighboring armor more closely; this review does not claim an exact reproduction of the reference.

## Contacts retained in the final result

| Scope | Retained measured contact |
|---|---|
| Native idle, walk, attack | Zero leg contacts across all sampled integer frames. Stock hand/finger contact remains in idle and walk. |
| Run31, Front_L | 66 leg triangle pairs; shell estimate 0.896 mm, lining estimate 2.261 mm. |
| Run40, Front_R | 45 leg triangle pairs; shell estimate 0.003 mm, lining estimate 1.179 mm. |
| High-knee diagnostic | 478 body triangle pairs; shell estimate 6.425 mm, lining estimate 6.094 mm. Belt and obi clear. |
| Other eight diagnostics | Zero body triangle pairs. |
| Do attachment | Actual surface crossings remain around upper attachments, lining and some narrow fittings. See the bounded solid investigation below. |

All rigid panels preserved their shapes with no inverted/collapsed triangles. Maximum sampled pair-distance error was about 1.01 micrometres; maximum residual across every evaluated vertex was about 0.481 micrometres. The frozen controller targets reproduced within the required tolerance.

Depth estimates in the general sweep use the sign of the nearest face at vertices of contacting triangles. They are not exact Boolean penetration depths. The report deliberately retains `surface_clear_in_all_samples: false`.

## Final Do outlier investigation

`diagnose_do_contacts.py` reproduces the maximum signed-nearest Do outlier from every final native clip using `motion-validation.json` and `hinge-reference-poses.json`. Its report, `do-final-outlier-solid-containment.json`, includes both input hashes, source/controller hashes, the exact command and the complete diagnostic script.

| Final outlier | Signed-nearest estimate | Outlier inside a Do solid? | Maximum sampled distance inside a containing Do solid, same component |
|---|---:|---|---:|
| Idle2, belt | 9.090 mm | No | 1.964 mm |
| Walk41, center trim | 17.129 mm | No | 1.587 mm |
| Run29, center lining | 17.510 mm | No | 1.960 mm |
| Attack23, belt | 8.569 mm | No | 1.993 mm |

All four outlier world points reproduced exactly. Closed-island ray tests place the large outlier points outside Do solids; their signed-nearest distances therefore do not establish deep solid penetration. Actual contact-triangle vertices inside solids remain, and every deepest contained point in these final cases lies in `Do_Review_Lining`. Eight ray-edge disagreements were resolved with the closed island's signed solid-angle winding number. The archived four earlier outliers are separately retained in `do-outlier-solid-containment.json`.

This is a bounded investigation of those components and frames. It does not establish global Do clearance, exact union penetration, extrema within triangle interiors or subframe clearance.

## Reproduction

Run from the repository root with the frozen source and controller:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --threads 2 --python-exit-code 1 --python SourceArt/Characters/Samurai/Kusazuri01/Scripts/review_kusazuri.py
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --threads 2 --python-exit-code 1 --python SourceArt/Characters/Samurai/Kusazuri01/Scripts/diagnose_do_contacts.py
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --threads 2 --python-exit-code 1 --python SourceArt/Characters/Samurai/Kusazuri01/Scripts/review_kusazuri.py -- --render-only --resolution 900 --samples 16
```

The close-view manifest embeds its supplementary rendering script. The archived Do cases can be reproduced with `diagnose_do_contacts.py -- --baseline pre-lateral`; their point reproduction guard prevents interpreting a comparison if panel geometry has changed.
