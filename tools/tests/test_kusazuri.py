"""Reject incorrect count, animation, rendering and panel-controller evidence."""
import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
try:
    import kusazuri
except ModuleNotFoundError:
    kusazuri = None


def report(count=1, mode='kusazuri', pose='animation'):
    return {
        'rendered_bodies': count, 'rendered_helmets': count, 'rendered_armors': count,
        'rendered_sode': count * 2, 'rendered_kusazuri': count if mode == 'kusazuri' else 0,
        'mode': mode, 'camera': 'close' if count == 1 else 'tactical', 'pose': pose,
        'requested_animation': 'idle', 'requested_count': count,
        'body_standard': 'Epic Unreal Manny — SKM_Manny_Simple',
        'crowd_representation': 'single skeletal/poseable fixture' if count == 1 else 'static',
        'rendered': True, 'validated': True, 'screenshot_exists': True, 'rhi': 'Metal',
        'frames': 100, 'viewport_width': 1600, 'viewport_height': 900,
        'max_root_position_error_cm': 0., 'max_root_rotation_error_degrees': 0.,
        'max_attachment_position_error_cm': 0., 'max_armor_bone_position_error_cm': 0.,
        'max_armor_bone_rotation_error_degrees': 0., 'max_sode_bone_position_error_cm': 0.,
        'max_sode_bone_rotation_error_degrees': 0., 'max_component_world_scale_error': 0.,
        'max_kusazuri_bone_position_error_cm': 0., 'max_kusazuri_bone_rotation_error_degrees': 0.,
        'armor_skeleton_compatible': True, 'sode_skeleton_compatible': True,
        'kusazuri_skeleton_compatible': True, 'kusazuri_controller_samples': 100,
        'kusazuri_panel_count': 7, 'animation_advanced': True,
        'observed_animation_position_range_seconds': .9,
        'animation_asset': '/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle.MM_Idle',
    }


class KusazuriReviewTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(kusazuri, 'Kusazuri CLI has not been implemented')

    def args(self, *extra):
        return kusazuri.parse_args(['review', *extra])

    def test_literal_isolated_command_and_real_crowd_count(self):
        flags = kusazuri.review_flags(self.args('--count', '500', '--camera', 'tactical', '--mode', 'existing'),
                                    Path('/tmp/armor review/result.json'), Path('/tmp/armor review/image.png'))
        self.assertEqual(flags[0], '/Game/Art/Characters/Samurai/Kusazuri01/Review/Kusazuri01_Review?game=/Script/Shoen.KusazuriReviewGameMode')
        self.assertIn('-KusazuriCount=500', flags)
        self.assertIn('-KusazuriMode=existing', flags)
        self.assertIn('-KusazuriOutput=/tmp/armor review/result.json', flags)
        self.assertNotIn('-NullRHI', flags)

    def test_accepts_two_comparison_modes_and_static_crowds_without_animation_claim(self):
        for mode in ['existing', 'kusazuri']:
            for count in [1, 100, 500]:
                value = report(count, mode)
                if count > 1:
                    value.update(animation_advanced=False, kusazuri_controller_samples=0, animation_asset='')
                kusazuri.validate_review(value, self.args('--mode', mode, '--count', str(count),
                                                        '--camera', value['camera']))

    def test_rejects_incomplete_counts_and_non_rendering_evidence(self):
        for changed in [{'rendered_kusazuri': 0}, {'rendered_sode': 1}, {'rendered_bodies': True},
                        {'rhi': 'NullRHI'}, {'validated': 1}, {'frames': 0}, {'viewport_height': -1},
                        {'requested_count': 100}, {'crowd_representation': 'static'}]:
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                kusazuri.validate_review(dict(report(), **changed), self.args())

    def test_rejects_invalid_panel_motion_and_skeleton_evidence(self):
        for changed in [{'kusazuri_controller_samples': 0}, {'kusazuri_panel_count': 6},
                        {'kusazuri_skeleton_compatible': False}, {'sode_skeleton_compatible': 'true'},
                        {'max_kusazuri_bone_position_error_cm': float('nan')},
                        {'max_kusazuri_bone_rotation_error_degrees': .2},
                        {'max_component_world_scale_error': False}]:
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                kusazuri.validate_review(dict(report(), **changed), self.args())

    def test_rejects_stalled_or_wrong_native_clip_and_accepts_diagnostic_pose(self):
        for changed in [{'animation_advanced': False}, {'observed_animation_position_range_seconds': 0},
                        {'animation_asset': '/Game/Retargeted/Idle'}]:
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                kusazuri.validate_review(dict(report(), **changed), self.args())
        value = report(pose='crouch')
        value.update(animation_advanced=False, animation_asset='')
        kusazuri.validate_review(value, self.args('--pose', 'crouch'))

    def test_rejects_unsupported_counts_ambiguous_crowd_poses_and_unsafe_labels(self):
        for extra in [('--count', '1000'), ('--count', '500'), ('--camera', 'tactical'),
                      ('--camera', 'tactical', '--count', '100', '--pose', 'crouch'),
                      ('--seconds', 'nan'), ('--seconds', '-1'), ('--label', '../x')]:
            with self.subTest(extra=extra), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                self.args(*extra)


if __name__ == '__main__':
    unittest.main()
