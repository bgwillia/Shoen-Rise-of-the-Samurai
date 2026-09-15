# Kusazuri motion baseline before lateral correction

**Failing baseline, not final approval.** 372 poses: 363 native integer frames and 9 diagnostics. Source unchanged; rigidity preserved; no inverted/collapsed triangles.

| Clip | Frames | Leg-contact frames | Max leg estimate, mm | Hand-contact frames | Max Do estimate, mm |
|---|---:|---:|---:|---:|---:|
| A_Idle | 229 | 0 | 0.000 | 229 | 9.090 |
| A_Walk | 47 | 1 | 2.003 | 10 | 17.129 |
| A_Run | 55 | 8 | 6.254 | 12 | 20.188 |
| A_Attack | 32 | 1 | 15.088 | 0 | 8.569 |

## Diagnostics

| Diagnostic | Body triangle pairs | Max leg estimate, mm | Max Do estimate, mm |
|---|---:|---:|---:|
| neutral | 0 | 0.000 | 4.014 |
| wide-step | 0 | 0.000 | 4.014 |
| wide-stance | 0 | 0.000 | 4.014 |
| knee-lift | 715 | 7.012 | 4.014 |
| crouch | 0 | 0.000 | 3.049 |
| combat-stance | 0 | 0.000 | 2.218 |
| torso-turn | 0 | 0.000 | 5.110 |
| hip-rotation | 0 | 0.000 | 3.478 |
| bow-diagnostic | 0 | 0.000 | 2.218 |

Depth is a signed nearest-surface estimate at contact-triangle vertices. It is not exact Boolean penetration. The full report retains affected components, dominant body-bone regions, sampled points and frozen hinge targets.

The subsequent bounded thigh-direction/lateral-guard/.08-side-floor probe clears the tested native failure frames; its full rerun remains pending. Run32 cord contact was traced to the hanging tassel tip, not the waist rings.
