#!/usr/bin/env python3
"""Build, import and inspect modular Kusazuri01 on the existing native Manny."""
import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import dev

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'SourceArt/Characters/Samurai/Kusazuri01'
EVIDENCE = ROOT / 'artifacts/kusazuri01'
LOCAL = ROOT / 'artifacts/local/kusazuri01'
BLENDER = Path('/Applications/Blender.app/Contents/MacOS/Blender')


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['source', 'export', 'validate', 'import', 'review'])
    parser.add_argument('--engine')
    parser.add_argument('--contract', type=Path, default=ART / 'asset-manifest.json')
    parser.add_argument('--mode', choices=['existing', 'kusazuri'], default='kusazuri',
                        help='existing Manny/Kabuto/Dō/Sode outfit, optionally adding Kusazuri')
    parser.add_argument('--count', type=int, choices=[1, 100, 500], default=1)
    parser.add_argument('--camera', choices=['close', 'front', 'back', 'left', 'right', 'rear', 'detail', 'top', 'interior', 'tactical'], default='close',
                        help='close = 3/4 front; rear = 3/4 rear; front/back = straight views; detail/top/interior inspect the waist')
    parser.add_argument('--animation', choices=['idle', 'walk', 'run', 'attack', 'none'], default='idle',
                        help='native Manny clips; run selects the existing jog clip')
    parser.add_argument('--pose', choices=['animation', 'neutral', 'arms-forward', 'arms-raised', 'turn', 'bend', 'head', 'bow', 'crouch', 'wide-step', 'knee-lift', 'wide-stance', 'combat-stance', 'hip-rotation', 'torso-turn'], default='animation',
                        help='bow is a diagnostic bone pose, not a native bow animation')
    parser.add_argument('--seconds', type=float, default=10)
    parser.add_argument('--label')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)
    if not math.isfinite(args.seconds) or not 0 <= args.seconds <= 600:
        parser.error('--seconds must be finite and 0–600')
    if args.label is not None and (not args.label or args.label in ('.', '..') or Path(args.label).name != args.label or '\\' in args.label):
        parser.error('--label must be a filename stem')
    if args.command == 'review':
        if (args.camera == 'tactical') != (args.count > 1):
            parser.error('tactical requires --count 100 or 500; other cameras require --count 1')
        if args.count > 1 and args.pose != 'animation':
            parser.error('static crowd probes do not accept diagnostic poses')
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
        '/Game/Art/Characters/Samurai/Kusazuri01/Review/Kusazuri01_Review?game=/Script/Shoen.KusazuriReviewGameMode',
        '-game', '-windowed', '-ResX=1600', '-ResY=900', '-NoVSync', '-nop4', '-nosplash',
        '-stdout', '-FullStdOutLogOutput', f'-KusazuriMode={args.mode}', f'-KusazuriCount={args.count}', f'-KusazuriCamera={args.camera}',
        f'-KusazuriAnimation={args.animation}', f'-KusazuriPose={args.pose}', f'-KusazuriContract={args.contract.resolve()}',
        f'-KusazuriSeconds={args.seconds}', f'-KusazuriOutput={output}', f'-KusazuriScreenshot={screenshot}',
    ]


def validate_review(report, args):
    """Reject stale/incorrect evidence; rigid-bone agreement is separate from surface fit."""
    if not isinstance(report, dict):
        raise ValueError('Review report must be a JSON object')
    count = args.count
    expected = {'rendered_bodies': count, 'rendered_helmets': count, 'rendered_armors': count,
                'rendered_sode': 2*count, 'rendered_kusazuri': count if args.mode == 'kusazuri' else 0,
                'mode': args.mode, 'camera': args.camera, 'pose': args.pose, 'requested_animation': args.animation,
                'requested_count': count, 'body_standard': 'Epic Unreal Manny — SKM_Manny_Simple',
                'crowd_representation': 'single skeletal/poseable fixture' if count == 1 else 'static'}
    if not all(type(report.get(key)) is type(value) and report[key] == value for key, value in expected.items()):
        raise ValueError('Review counts or requested mode/camera/pose do not match')
    if not all(report.get(key) is True for key in ('rendered', 'validated', 'screenshot_exists')):
        raise ValueError('Rendered review did not validate or capture a real viewport')
    for key in ('frames', 'viewport_width', 'viewport_height'):
        if type(report.get(key)) is not int or report[key] <= 0:
            raise ValueError('Missing positive integer rendering evidence: '+key)
    rhi = report.get('rhi')
    if not isinstance(rhi, str) or not rhi.strip() or rhi.lower() in ('null', 'nullrhi', 'unavailable', 'none'):
        raise ValueError('Review lacks a rendering RHI')
    for key in ('max_root_position_error_cm', 'max_root_rotation_error_degrees',
                'max_attachment_position_error_cm', 'max_armor_bone_position_error_cm',
                'max_armor_bone_rotation_error_degrees', 'max_sode_bone_position_error_cm',
                'max_sode_bone_rotation_error_degrees', 'max_kusazuri_bone_position_error_cm',
                'max_kusazuri_bone_rotation_error_degrees', 'max_component_world_scale_error'):
        value = report.get(key)
        maximum = .001 if key == 'max_component_world_scale_error' else .1
        if type(value) not in (float, int) or not math.isfinite(value) or not 0 <= value < maximum:
            raise ValueError('Invalid attachment/bone/scale evidence: '+key)
    for key in ('armor_skeleton_compatible', 'sode_skeleton_compatible'):
        if report.get(key) is not True:
            raise ValueError('Incompatible existing outfit skeleton: '+key)
    if args.mode == 'kusazuri':
        if report.get('kusazuri_skeleton_compatible') is not True or type(report.get('kusazuri_panel_count')) is not int or report['kusazuri_panel_count'] != 7:
            raise ValueError('Kusazuri must have seven controlled panels on the existing skeleton')
        if count == 1 and (type(report.get('kusazuri_controller_samples')) is not int or report['kusazuri_controller_samples'] <= 0):
            raise ValueError('Kusazuri controller was not sampled')
    if count == 1 and args.pose == 'animation' and args.animation != 'none':
        observed = report.get('observed_animation_position_range_seconds')
        if report.get('animation_advanced') is not True or type(observed) not in (int, float) or not math.isfinite(observed) or observed <= .001:
            raise ValueError('Requested clip did not advance')
        clip = {'idle': 'MM_Idle', 'walk': 'Walk/MF_Unarmed_Walk_Fwd',
                'run': 'Jog/MF_Unarmed_Jog_Fwd', 'attack': 'Attack/MM_Attack_01'}[args.animation]
        expected_clip = '/Game/Characters/Mannequins/Anims/Unarmed/' + clip + '.' + clip.split('/')[-1]
        if report.get('animation_asset') != expected_clip:
            raise ValueError('Reported animation is not the requested native Manny clip')


def main(argv=None):
    args = parse_args(argv)
    if args.command in ('source', 'export', 'validate'):
        script = {'source': 'build_kusazuri.py', 'export': 'export_kusazuri.py', 'validate': 'validate_kusazuri.py'}[args.command]
        command = [BLENDER, '--background', '--factory-startup', '--python-exit-code', '1', '--python', ART / 'Scripts' / script]
        if args.dry_run:
            print(dev.printed_command([str(value) for value in command]))
            return
        run(command, args.command)
        return
    editor = dev.editor_executable(dev.resolve_engine_root(args.engine, os.environ))
    base = [editor, ROOT / 'game/Shoen.uproject']
    label = args.label or f'{args.mode}-{args.count}-{args.camera}-{args.animation}-{args.pose}'
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
                     'rendered_kusazuri', 'rendered_sode', 'frames', 'median_fps', 'interval_fps', 'max_kusazuri_bone_position_error_cm']}, indent=2))


if __name__ == '__main__':
    main()
