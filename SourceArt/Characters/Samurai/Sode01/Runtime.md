# Sode01 runtime suspension

The unchanged native Manny skeleton drives the body and Dō. Each Sode uses a separate poseable mesh component containing the same reference skeleton. Its plate regions are rigidly weighted to the corresponding `upperarm_l` or `upperarm_r`; suspension cords blend that controlled bone with `spine_05`.

Each frame, after the body finishes updating, the review copies its complete local pose into each Sode component and refreshes the resulting component-space transforms. It then overrides only that side's upper-arm transform and refreshes again. Copying all parents before applying the override prevents stale parent transforms from corrupting the pose. The body, Dō, helmet, native clips, and reference skeleton assets are not changed.

The stateless suspension follows the shoulder position and the shoulder-to-elbow direction in the torso's reference axes. It removes axial arm twist, follows fore/aft swing, and smoothly rolls the plate onto the upper side of a raised arm only when the arm is nearly lateral. Other overhead and cross-body positions retain a hanging plate direction. Lateral suspension opening and up to 4 cm of lift clearance keep rigid plates clear during the sampled attack poses. The exact source formula is [sode_motion.py](Scripts/sode_motion.py); `SodeSuspensionTarget` in the Unreal review is its native-coordinate port using a Y-axis reflection in both directions.

This is authored pose control, with no physics simulation or delayed response. It preserves rigid plate shape while flexible attachment cords deform. Plain leader-pose attachment does not reproduce the demonstrated fit: the suspension controller is required. The review is an isolated integration example rather than battlefield equipment integration.

## Verification

`Shoen.Art.Sode.SuspensionMatchesBlender` compares the C++ target against 32 frozen Blender targets: both sides across sixteen native animation and diagnostic poses. [suspension-reference-poses.json](Scripts/suspension-reference-poses.json) records the source and controller hashes. The test also checks unit scale, immunity to upper-arm axial twist, a nonsingular result at exact lateral elevation, and rejection of a zero-length shoulder/elbow direction. It requires an actual compiled Unreal automation run; source presence alone is not a passing test.

Rendered reports measure bone errors against the intended controlled upper-arm transform and its propagated descendants. They separately record lateral opening, lift clearance, and the expected angular difference from Manny's arm. Those differences are not attachment errors. Bone-transform agreement does not prove surface clearance; the Blender intersection checks and rendered inspection provide separate evidence.
