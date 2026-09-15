"""Portable checks for Sode review invocation and rejection of invalid evidence."""
import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import unittest
from unittest import mock


TOOLS = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


with mock.patch.dict(sys.modules, {'dev': load_module('shoen_dev_for_sode', TOOLS / 'dev.py')}):
    sode = load_module('shoen_sode', TOOLS / 'sode.py')


def valid_report(mode='sode', pose='animation'):
    return {
        'rendered_bodies': 1, 'rendered_helmets': int(mode != 'mannequin'),
        'rendered_armors': int(mode != 'mannequin'), 'rendered_sode': 2 if mode == 'sode' else 0,
        'rendered_sode_left': int(mode == 'sode'), 'rendered_sode_right': int(mode == 'sode'),
        'mode': mode, 'camera': 'close', 'pose': pose, 'requested_animation': 'idle',
        'body_standard': 'Epic Unreal Manny — SKM_Manny_Simple',
        'crowd_representation': 'single skeletal/poseable fixture',
        'rendered': True, 'validated': True, 'screenshot_exists': True,
        'frames': 100, 'viewport_width': 1600, 'viewport_height': 900, 'rhi': 'Metal',
        'max_root_position_error_cm': 0., 'max_root_rotation_error_degrees': 0.,
        'max_attachment_position_error_cm': 0., 'max_armor_bone_position_error_cm': 0.,
        'max_armor_bone_rotation_error_degrees': 0., 'max_sode_bone_position_error_cm': 0.,
        'max_sode_bone_rotation_error_degrees': 0., 'max_component_world_scale_error': 0.,
        'animation_advanced': pose == 'animation', 'armor_skeleton_compatible': True,
        'sode_suspension_samples': 100 if mode == 'sode' else 0,
        'sode_suspension': [{'side': side, 'opening_at_capture_cm': 2., 'maximum_opening_cm': 4.,
                             'maximum_body_rotation_difference_degrees': 35.} for side in ['left', 'right']] if mode == 'sode' else [],
        'sode_skeleton_compatible': True,
        'observed_animation_position_range_seconds': .9 if pose == 'animation' else None,
        'animation_asset': '/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle.MM_Idle' if pose == 'animation' else '',
    }


class SodeReviewCliTests(unittest.TestCase):
    def arguments(self, *extra):
        return sode.parse_args(['review', *extra])

    def assert_rejected(self, changed):
        report = valid_report()
        report.update(changed)
        with self.assertRaises(ValueError):
            sode.validate_review(report, self.arguments())

    def test_command_uses_isolated_review_and_literal_paths(self):
        args = self.arguments('--mode', 'armor', '--camera', 'rear', '--animation', 'attack',
                              '--seconds', '12', '--contract', '/tmp/sode folder/asset-manifest.json')
        command = sode.review_flags(args, Path('/tmp/sode folder/report.json'), Path('/tmp/sode folder/capture.png'))
        self.assertEqual(command[0], '/Game/Art/Characters/Samurai/Sode01/Review/Sode01_Review?game=/Script/Shoen.SodeReviewGameMode')
        for argument in ['-game', '-SodeMode=armor', '-SodeCamera=rear', '-SodeAnimation=attack',
                         '-SodePose=animation', '-SodeSeconds=12.0', f'-SodeContract={Path("/tmp/sode folder/asset-manifest.json").resolve()}',
                         '-SodeOutput=/tmp/sode folder/report.json', '-SodeScreenshot=/tmp/sode folder/capture.png']:
            self.assertIn(argument, command)
        self.assertFalse(any(arg.startswith(('-Do', '-Kabuto', '-NullRHI')) for arg in command))

    def test_valid_comparisons_and_diagnostic_pose_do_not_require_a_native_bow_clip(self):
        for mode in ['mannequin', 'armor', 'sode']:
            sode.validate_review(valid_report(mode=mode), self.arguments('--mode', mode))
        sode.validate_review(valid_report(pose='bow'), self.arguments('--pose', 'bow'))

    def test_rejects_wrong_side_counts_or_stale_requested_modes(self):
        for changes in [{'rendered_sode_left': 0}, {'rendered_sode_right': 0}, {'rendered_sode': 1},
                        {'mode': 'armor'}, {'camera': 'back'}, {'requested_animation': 'walk'},
                        {'body_standard': 'different mannequin'}]:
            with self.subTest(changes=changes):
                self.assert_rejected(changes)

    def test_rejects_missing_or_incompatible_skeleton_evidence(self):
        for field in ['armor_skeleton_compatible', 'sode_skeleton_compatible']:
            for value in [False, None, 'true']:
                with self.subTest(field=field, value=value):
                    self.assert_rejected({field: value})

    def test_rejects_nonfinite_out_of_range_and_mistyped_bone_errors(self):
        for field in ['max_sode_bone_position_error_cm', 'max_sode_bone_rotation_error_degrees',
                      'max_component_world_scale_error']:
            for value in [None, float('nan'), float('inf'), -.001, .1, '0', False]:
                with self.subTest(field=field, value=value):
                    self.assert_rejected({field: value})

    def test_rejects_malformed_render_flags_counts_and_viewport(self):
        for changes in [{'rendered': 'false'}, {'validated': 1}, {'screenshot_exists': 'true'},
                        {'frames': -1}, {'frames': True}, {'viewport_width': '1600'},
                        {'viewport_height': -900}, {'rendered_bodies': True}, {'rhi': 'Null'},
                        {'rhi': 'unavailable'}]:
            with self.subTest(changes=changes):
                self.assert_rejected(changes)

    def test_rejects_missing_or_malformed_suspension_evidence(self):
        for changes in [{'sode_suspension_samples': 0}, {'sode_suspension_samples': True},
                        {'sode_suspension': []}, {'sode_suspension': 'left and right'},
                        {'sode_suspension': [dict(valid_report()['sode_suspension'][0], maximum_opening_cm=float('nan')),
                                             valid_report()['sode_suspension'][1]]}]:
            with self.subTest(changes=changes):
                self.assert_rejected(changes)

    def test_rejects_stalled_or_mislabeled_animation(self):
        for changes in [{'animation_advanced': False}, {'animation_advanced': 'true'},
                        {'observed_animation_position_range_seconds': 0},
                        {'observed_animation_position_range_seconds': float('nan')},
                        {'animation_asset': '/Game/OtherSkeleton/Idle.Idle'}]:
            with self.subTest(changes=changes):
                self.assert_rejected(changes)

    def test_rejects_malformed_report_root_and_missing_measurements(self):
        for report in [None, [], {}, {key: value for key, value in valid_report().items() if key != 'frames'}]:
            with self.subTest(report=report):
                with self.assertRaises(ValueError):
                    sode.validate_review(report, self.arguments())

    def test_cli_rejects_unbounded_duration_and_path_traversal_labels(self):
        for arguments in [('--seconds', 'nan'), ('--seconds', 'inf'), ('--seconds', '-1'),
                          ('--seconds', '601'), ('--label', '../outside'), ('--label', 'x/y')]:
            with self.subTest(arguments=arguments), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    self.arguments(*arguments)


if __name__ == '__main__':
    unittest.main()
