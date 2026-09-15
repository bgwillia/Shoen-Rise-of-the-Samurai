# Kusazuri final source motion review

372 poses: 363 native integer frames and 9 authored diagnostics. Source unchanged; rigidity preserved; no inverted/collapsed triangles.

| Clip | Frames | Leg-contact frames | Max leg estimate, mm | Hand-contact frames | Max Do signed-nearest diagnostic, mm |
|---|---:|---:|---:|---:|---:|
| A_Idle | 229 | 0 | 0.000 | 229 | 9.090 |
| A_Walk | 47 | 0 | 0.000 | 14 | 17.129 |
| A_Run | 55 | 2 | 2.261 | 12 | 17.510 |
| A_Attack | 32 | 0 | 0.000 | 0 | 8.569 |

## Diagnostics

| Diagnostic | Body triangle pairs | Shell leg estimate, mm | Lining leg estimate, mm | Max Do signed-nearest diagnostic, mm |
|---|---:|---:|---:|---:|
| neutral | 0 | 0.000 | 0.000 | 4.014 |
| wide-step | 0 | 0.000 | 0.000 | 4.014 |
| wide-stance | 0 | 0.000 | 0.000 | 4.014 |
| knee-lift | 478 | 6.425 | 6.094 | 4.014 |
| crouch | 0 | 0.000 | 0.000 | 3.049 |
| combat-stance | 0 | 0.000 | 0.000 | 2.218 |
| torso-turn | 0 | 0.000 | 0.000 | 5.110 |
| hip-rotation | 0 | 0.000 | 0.000 | 3.478 |
| bow-diagnostic | 0 | 0.000 | 0.000 | 2.218 |

## Interpretation

The full report retains affected components, body-bone regions, sampled points and frozen hinge targets. Actual body/Do surface contacts remain; this is not an all-clear report. Shell and lining estimates are reported separately.

Body-region labels use dominant skin influence per contacted body triangle.
Depth estimates use negative nearest-face signs at vertices of contacting triangles. They are not exact Boolean solid penetration.
Do signed-nearest diagnostic outliers require the separate do-outlier-solid-containment.json investigation. Actual triangle crossings remain even when an outlier point is outside all Do solids.
Integer frames do not establish subframe clearance. Existing body/upper armor animation and remaining hand contacts are preserved.

Source SHA-256: `cf7c0ec0578b7fe2aca7d1b30439c521e8cecc3e63d4f36b0c8820b31dc9eb9e`

## Bounded Do solid investigation

The four archived 12–20 mm outlier points reproduced exactly and were outside all closed Do islands tested. Their large signed-nearest-face distances are diagnostic artifacts. Actual upper-attachment surface crossings remain: sampled points inside closed Do islands were 1.846 mm (Run29 side lining), 1.587 mm (Walk41 center trim), 1.230 mm (Run50 center lining) and 1.068 mm (Run50 center shell) from the containing solid surface. Three independent ray directions agreed on every candidate point. These bounded vertex tests do not prove continuous or whole-triangle solid clearance.

## Native residuals

Run31: Front_L shell 0.896 mm and lining 2.261 mm, 66 leg triangle pairs. Run40: Front_R shell 0.003 mm and lining 1.179 mm, 45 leg pairs. Walk19, Run22, Run32, Run39 and Attack13 all have zero leg triangle pairs after the final corrections. The high-knee diagnostic retains shell 6.425 mm and lining 6.094 mm; its belt and obi are clear. Stock animation hand/finger contacts remain.

## Final per-clip Do maxima

The final maximum Do signed-nearest points were also checked, using the final frozen hinge fixture: Idle2 9.090 mm, Walk41 17.129 mm, Run29 17.510 mm, Attack23 8.569 mm. All four reproduced exactly and were outside every closed Do solid. The tested contacting components still cross Do surfaces; contained contact vertices were at most 1.964, 1.587, 1.960 and 1.993 mm from the containing solid surface respectively. Each deepest contained point belonged to Do_Lining. Eight ray-edge vote disagreements were resolved with closed-island signed solid-angle winding. This bounded result does not establish global or continuous Do clearance. See `do-final-outlier-solid-containment.json`; the reproducible command and both frozen input hashes are included there.
