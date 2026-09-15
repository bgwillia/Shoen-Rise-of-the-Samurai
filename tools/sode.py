#!/usr/bin/env python3
"""Build, import and inspect the matching Sode01 pair on the existing native Manny."""
import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import dev

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'SourceArt/Characters/Samurai/Sode01'
EVIDENCE = ROOT / 'artifacts/sode01'
LOCAL = ROOT / 'artifacts/local/sode01'
BLENDER = Path('/Applications/Blender.app/Contents/MacOS/Blender')


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['source', 'export', 'validate', 'import', 'review'])
    parser.add_argument('--engine')
    parser.add_argument('--contract', type=Path, default=ART / 'asset-manifest.json')
    parser.add_argument('--mode', choices=['mannequin', 'armor', 'sode'], default='sode',
                        help='one body, body+Kabuto+Dō, or body+Kabuto+Dō+both Sode')
    parser.add_argument('--camera', choices=['close', 'front', 'back', 'left', 'right', 'rear', 'detail', 'tactical'], default='close',
                        help='close = 3/4 front; rear = 3/4 rear; back = straight rear')
    parser.add_argument('--animation', choices=['idle', 'walk', 'run', 'attack', 'none'], default='idle',
                        help='native Manny clips; run selects the existing jog clip')
    parser.add_argument('--pose', choices=['animation', 'neutral', 'arms-forward', 'arms-raised', 'turn', 'bend', 'head', 'bow'], default='animation',
                        help='bow is a diagnostic bone pose, not a native bow animation')
    parser.add_argument('--seconds', type=float, default=10)
    parser.add_argument('--label')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)
    if not math.isfinite(args.seconds) or not 0 <= args.seconds <= 600:
        parser.error('--seconds must be finite and 0–600')
    if args.label is not None and (not args.label or args.label in ('.', '..') or Path(args.label).name != args.label or '\\' in args.label):
        parser.error('--label must be a filename stem')
    return args


def run(argv, label, timeout=900):
    LOCAL.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    argv = [str(value) for value in argv]
    print(dev.printed_command(argv), flush=True)
    (EVIDENCE / (label + '-command.json')).write_text(json.dumps(argv, indent=2) + '\n')
    with (LOCAL / (label + '.log')).open('w') as log:
        try:
            result = subprocess.run(argv, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
        except subprocess.TimeoutExpired as error:
            raise SystemExit(f'Timed out after {timeout}s; see {LOCAL / (label + ".log")}') from error
    print(f'Exit {result.returncode}: {LOCAL / (label + ".log")}', flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)


def review_flags(args, output, screenshot):
    return [
        '/Game/Art/Characters/Samurai/Sode01/Review/Sode01_Review?game=/Script/Shoen.SodeReviewGameMode',
        '-game', '-windowed', '-ResX=1600', '-ResY=900', '-NoVSync', '-nop4', '-nosplash',
        '-stdout', '-FullStdOutLogOutput', f'-SodeMode={args.mode}', f'-SodeCamera={args.camera}',
        f'-SodeAnimation={args.animation}', f'-SodePose={args.pose}', f'-SodeContract={args.contract.resolve()}',
        f'-SodeSeconds={args.seconds}', f'-SodeOutput={output}', f'-SodeScreenshot={screenshot}',
    ]


def validate_review(report, args):
    """Validate fresh engine evidence; bone agreement is not surface-clearance approval."""
    if not isinstance(report, dict):
        raise ValueError('Review report must be a JSON object')
    expected = {'rendered_bodies': 1, 'rendered_helmets': int(args.mode != 'mannequin'),
                'rendered_armors': int(args.mode != 'mannequin'), 'rendered_sode': 2 if args.mode == 'sode' else 0,
                'rendered_sode_left': int(args.mode == 'sode'), 'rendered_sode_right': int(args.mode == 'sode'),
                'mode': args.mode, 'camera': args.camera, 'pose': args.pose, 'requested_animation': args.animation,
                'body_standard': 'Epic Unreal Manny — SKM_Manny_Simple',
                'crowd_representation': 'single skeletal/poseable fixture'}
    if not all(type(report.get(key)) is type(value) and report[key] == value for key, value in expected.items()):
        raise ValueError('Review counts or requested mode/camera/pose do not match')
    if not all(report.get(key) is True for key in ('rendered', 'validated', 'screenshot_exists')):
        raise ValueError('Rendered review did not validate or capture a real viewport')
    for key in ('frames', 'viewport_width', 'viewport_height'):
        if type(report.get(key)) is not int or report[key] <= 0:
            raise ValueError(f'Review lacks positive integer rendering evidence: {key}')
    rhi = report.get('rhi')
    if not isinstance(rhi, str) or not rhi.strip() or rhi.lower() in ('null', 'nullrhi', 'unavailable', 'none'):
        raise ValueError('Review lacks a rendering RHI')
    for key, maximum in [('max_root_position_error_cm', .1), ('max_root_rotation_error_degrees', .1),
                         ('max_attachment_position_error_cm', .1), ('max_armor_bone_position_error_cm', .1),
                         ('max_armor_bone_rotation_error_degrees', .1), ('max_sode_bone_position_error_cm', .1),
                         ('max_sode_bone_rotation_error_degrees', .1), ('max_component_world_scale_error', .001)]:
        value = report.get(key)
        if type(value) not in (float, int) or not math.isfinite(value) or not 0 <= value < maximum:
            raise ValueError(f'Invalid attachment/bone/scale result: {key}')
    if args.pose == 'animation' and args.animation != 'none':
        observed = report.get('observed_animation_position_range_seconds')
        if report.get('animation_advanced') is not True or type(observed) not in (int, float) or not math.isfinite(observed) or observed <= .001:
            raise ValueError('Requested clip did not advance')
        clip = {'idle': 'MM_Idle', 'walk': 'Walk/MF_Unarmed_Walk_Fwd',
                'run': 'Jog/MF_Unarmed_Jog_Fwd', 'attack': 'Attack/MM_Attack_01'}[args.animation]
        expected_clip = '/Game/Characters/Mannequins/Anims/Unarmed/' + clip + '.' + clip.split('/')[-1]
        if report.get('animation_asset') != expected_clip:
            raise ValueError('Reported animation is not the requested native Manny clip')
    if args.mode != 'mannequin' and report.get('armor_skeleton_compatible') is not True:
        raise ValueError('Dō does not use the existing compatible skeleton')
    if args.mode == 'sode' and report.get('sode_skeleton_compatible') is not True:
        raise ValueError('Sode pair does not use the existing compatible skeleton')
    if args.mode == 'sode':
        if type(report.get('sode_suspension_samples')) is not int or report['sode_suspension_samples'] <= 0:
            raise ValueError('Sode suspension was not sampled')
        suspension = report.get('sode_suspension')
        if not isinstance(suspension, list) or len(suspension) != 2:
            raise ValueError('Sode suspension requires both sides')
        for side, sample in zip(('left', 'right'), suspension):
            if not isinstance(sample, dict) or sample.get('side') != side:
                raise ValueError('Invalid Sode suspension side')
            for key in ('opening_at_capture_cm', 'maximum_opening_cm', 'maximum_body_rotation_difference_degrees'):
                value = sample.get(key)
                if type(value) not in (float, int) or not math.isfinite(value) or value < 0:
                    raise ValueError(f'Invalid Sode suspension measurement: {key}')
            if sample['maximum_opening_cm'] < sample['opening_at_capture_cm']:
                raise ValueError('Sode opening maximum is smaller than its current sample')


def main(argv=None):
    args = parse_args(argv)
    if args.command in ('source', 'export', 'validate'):
        script = {'source': 'build_sode.py', 'export': 'export_sode.py', 'validate': 'validate_sode.py'}[args.command]
        command = [BLENDER, '--background', '--factory-startup', '--python-exit-code', '1', '--python', ART / 'Scripts' / script]
        if args.dry_run:
            print(dev.printed_command([str(value) for value in command]))
            return
        run(command, args.command)
        return
    editor = dev.editor_executable(dev.resolve_engine_root(args.engine, os.environ))
    base = [editor, ROOT / 'game/Shoen.uproject']
    label = args.label or f'{args.mode}-{args.camera}-{args.animation}-{args.pose}'
    output = EVIDENCE / (label + '.json')
    screenshot = EVIDENCE / (label + '.png')
    if args.command == 'import':
        command = base + [f'-ExecutePythonScript={ART / "Scripts/import_unreal.py"}', '-unattended', '-NullRHI',
                          '-nop4', '-nosplash', '-stdout', '-FullStdOutLogOutput']
    else:
        command = base + review_flags(args, output, screenshot)
    if args.dry_run:
        print(dev.printed_command([str(value) for value in command]))
        return
    probe = subprocess.run(['pgrep', '-x', 'UnrealEditor'], capture_output=True, text=True)
    if probe.returncode == 0:
        raise SystemExit('An Unreal editor/game is already open. Finish it before this import/review.')
    if probe.returncode != 1:
        raise SystemExit('Cannot inspect Unreal processes: ' + probe.stderr)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    if args.command == 'import':
        report_path = EVIDENCE / 'unreal-import.json'
        report_path.unlink(missing_ok=True)
        run(command, 'import')
        if not json.loads(report_path.read_text()).get('validated'):
            raise SystemExit('Import report did not validate.')
        return
    if args.seconds == 0:
        raise SystemExit(subprocess.call([str(value) for value in command], cwd=ROOT))
    output.unlink(missing_ok=True)
    screenshot.unlink(missing_ok=True)
    run(command, label, args.seconds + 180)
    report = json.loads(output.read_text())
    try:
        validate_review(report, args)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    print(json.dumps({key: report[key] for key in ['rendered_bodies', 'rendered_helmets', 'rendered_armors',
                     'rendered_sode', 'frames', 'median_fps', 'interval_fps', 'max_sode_bone_position_error_cm']}, indent=2))


if __name__ == '__main__':
    main()
