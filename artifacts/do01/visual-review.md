# Dō01 independent visual review

Reviewed 2026-09-15 against the [supplied reference](../../SourceArt/References/Samurai/Do01/do_01_reference_sheet.png), Blender hero/orthographic views, official Manny fit views, and sampled native-animation stress views in [Review/Captures](../../SourceArt/Characters/Samurai/Do01/Review/Captures/).

**Status: final Blender observations, not visual approval or full animation-clearance certification.** This review includes the refreshed final-source rear and stress captures and the final [pose-review.json](pose-review.json), including the smooth strap weights and revised lining profile.

## Appearance and reference deviations

- Dense woven red pairs, separate plate rows, side ties and raised brass fittings make the construction substantially clearer than the earlier version. The silhouette remains recognizable as the requested Dō, now fitted to official Manny.
- The broad bib and shoulder straps still read as pale sheet metal under some review-light angles. The reference emphasizes darker lacquer with more localized highlights.
- Repeated straight seams and gold tracers remain more regular and prominent than the reference's rounded, overlapping black plates. The central three-lobed fittings are simpler than its fine botanical relief.
- The broad brown lining protrusion at the rear waist is removed in the final [rear view](../../SourceArt/Characters/Samurai/Do01/Review/Captures/blender-rear.png). The overlapping plate rows now cover that area.

## Pose findings

Neutral and raised-arm views showed no obvious large body protrusions from the inspected angle. The final measurements report zero body/armor and helmet/armor triangle intersections for neutral, arms-raised, turn, bend and head inspection poses. This does not establish clearance throughout an animation clip.

Final [attack frame 28](../../SourceArt/Characters/Samurai/Do01/Review/Captures/stress-a_attack-28.png) shows reduced sharp strap folding after the smooth `spine_05`/clavicle weight change. Pale contact and overlap remain beneath the helmet guards, particularly at the screen-right shoulder. The upright strap kink is also reduced in [attack frame 20](../../SourceArt/Characters/Samurai/Do01/Review/Captures/stress-a_attack-20.png). These changes improve deformation without eliminating the remaining attack contact. Final [jog frame 23](../../SourceArt/Characters/Samurai/Do01/Review/Captures/stress-a_run-23.png) has a smoother shoulder transition; all three sampled jog frames report zero helmet/armor intersections, while body/armor intersections remain.

Final sampled-pose measurements:

| Pose or native clip | Body/armor triangle pairs | Helmet/armor triangle pairs |
| --- | ---: | ---: |
| Neutral, arms-raised, turn, bend, head | 0 | 0 |
| Arms-forward | 488 | 0 |
| Idle | 1,098–1,427 | 0–106 |
| Walk | 1,849–2,191 | 0 |
| Jog (`A_Run`) | 617–1,143 | 0 |
| Attack | 193–2,989 | 826–1,123 |

Triangle-pair counts measure intersecting surfaces, not penetration depth or visible severity; crossing arms also hide parts of the torso. These clips cannot be described as fully clipping-free. Native clips, Manny and Kabuto are preserved; review poses do not constitute a new animation library.

The retained stress views complement the neutral and raised/forward-arm views. Unreal material correctness, rendered performance and user visual acceptance are separate from this Blender review.

## Final Unreal cross-check

The final left/right, walk/jog, forward-arm, turn/bend and head-turn captures show the intended lacquer/red cord/brass material and native Manny materials, with coherent armor and helmet placement. No new catastrophic import or pose artifact was observed. The 100-body skeletal capture shows an intact 10×10 formation; its distance is too great to judge fine clearance. The documented stock-animation contact remains a limitation.
