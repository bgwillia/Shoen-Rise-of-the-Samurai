#!/usr/bin/env python3
"""Build, import and inspect Dō01. Rendering requires one real Unreal process at a time."""
import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import dev

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'SourceArt/Characters/Samurai/Do01'
EVIDENCE = ROOT / 'artifacts/do01'
LOCAL = ROOT / 'artifacts/local/do01'
BLENDER = Path('/Applications/Blender.app/Contents/MacOS/Blender')


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['source', 'export', 'validate', 'import', 'materials', 'review'])
    parser.add_argument('--engine')
    parser.add_argument('--contract', type=Path, default=ART / 'asset-manifest.json',
                        help='Dō manifest containing the measured native Manny review_contract')
    parser.add_argument('--count', type=int, choices=[100, 500, 1000], default=100)
    parser.add_argument('--mode', choices=['mannequin', 'helmet', 'armor'], default='armor')
    parser.add_argument('--camera', choices=['close', 'front', 'rear', 'left', 'right', 'tactical', 'far'], default='close')
    parser.add_argument('--animation', choices=['idle', 'walk', 'run', 'attack', 'none'], default='idle',
                        help='native Epic Manny idle/walk/jog/attack clips; run selects the authored jog clip')
    parser.add_argument('--pose', choices=['animation', 'neutral', 'arms-forward', 'arms-raised', 'turn', 'bend', 'head'], default='animation')
    parser.add_argument('--crowd', choices=['static', 'skeletal'], default='static',
                        help='skeletal is a bounded count-100 animated cost probe, not normal crowd representation')
    parser.add_argument('--seconds', type=float, default=10)
    parser.add_argument('--label')
    parser.add_argument('--dry-run', action='store_true', help='print the exact command without launching or changing files')
    args = parser.parse_args(argv)
    if not math.isfinite(args.seconds) or not 0 <= args.seconds <= 600:
        parser.error('--seconds must be finite and 0–600')
    if args.label is not None and (not args.label or args.label in ('.', '..') or Path(args.label).name != args.label or '\\' in args.label):
        parser.error('--label must be a filename stem')
    close = args.camera not in ('tactical', 'far')
    if args.command == 'review':
        if args.crowd == 'skeletal' and (close or args.count != 100 or args.pose != 'animation' or args.animation == 'none'):
            parser.error('--crowd skeletal requires tactical/far, --count 100 and a real animation')
        if not close and args.pose != 'animation':
            parser.error('inspection poses require a close/front/rear/left/right camera')
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
        '/Game/Art/Characters/Samurai/Do01/Review/Do01_Review?game=/Script/Shoen.DoReviewGameMode',
        '-game', '-windowed', '-ResX=1600', '-ResY=900', '-NoVSync', '-nop4', '-nosplash',
        '-stdout', '-FullStdOutLogOutput', f'-DoCount={args.count}', f'-DoMode={args.mode}',
        f'-DoCamera={args.camera}', f'-DoAnimation={args.animation}', f'-DoPose={args.pose}',
        f'-DoCrowd={args.crowd}', f'-DoContract={args.contract.resolve()}', f'-DoSeconds={args.seconds}', f'-DoOutput={output}', f'-DoScreenshot={screenshot}',
    ]


def validate_review(report, args):
    """Reject stale/incomplete or technically invalid results; this is not visual acceptance."""
    bodies = 1 if args.camera not in ('tactical', 'far') else args.count
    expected = {'rendered_bodies': bodies, 'rendered_helmets': bodies if args.mode != 'mannequin' else 0,
                'rendered_armors': bodies if args.mode == 'armor' else 0,
                'mode': args.mode, 'camera': args.camera, 'pose': args.pose, 'requested_animation': args.animation,
                'body_standard': 'Epic Unreal Manny — SKM_Manny_Simple',
                'crowd_representation': 'single skeletal/poseable fixture' if bodies == 1 else args.crowd}
    if not all(report.get(key) == value for key, value in expected.items()):
        raise ValueError('Review counts or requested mode/camera/pose do not match')
    if not all(report.get(key) for key in ('rendered', 'validated', 'screenshot_exists', 'frames', 'viewport_width', 'viewport_height')):
        raise ValueError('Rendered review did not validate or capture a real viewport')
    for key, maximum in [('max_root_position_error_cm', .1), ('max_root_rotation_error_degrees', .1),
                         ('max_attachment_position_error_cm', .1), ('max_armor_bone_position_error_cm', .1),
                         ('max_armor_bone_rotation_error_degrees', .1), ('max_component_world_scale_error', .001)]:
        value = report.get(key)
        if not isinstance(value, (float, int)) or not math.isfinite(value) or not 0 <= value < maximum:
            raise ValueError(f'Invalid attachment/bone/scale result: {key}')
    if (bodies == 1 or args.crowd == 'skeletal') and args.pose == 'animation' and args.animation != 'none' and not report.get('animation_advanced'):
        raise ValueError('Requested clip did not advance')
    if args.mode == 'armor' and not report.get('armor_skeleton_compatible'):
        raise ValueError('Armor does not use the existing compatible skeleton')


def main(argv=None):
    args = parse_args(argv)
    if args.command in ('source', 'export', 'validate'):
        script = {'source': 'build_do.py', 'export': 'export_do.py', 'validate': 'validate_do.py'}[args.command]
        command = [BLENDER, '--background', '--factory-startup', '--python-exit-code', '1', '--python', ART / 'Scripts' / script]
        if args.dry_run:
            print(dev.printed_command([str(value) for value in command]))
            return
        run(command, args.command)
        return
    editor = dev.editor_executable(dev.resolve_engine_root(args.engine, os.environ))
    base = [editor, ROOT / 'game/Shoen.uproject']
    label = args.label or f'{args.mode}-{args.count}-{args.camera}-{args.animation}-{args.pose}-{args.crowd}'
    output = EVIDENCE / (label + '.json')
    screenshot = EVIDENCE / (label + '.png')
    if args.command in ('import', 'materials'):
        script = 'import_unreal.py' if args.command == 'import' else 'compile_do_materials.py'
        command = base + [f'-ExecutePythonScript={ART / "Scripts" / script}', '-unattended',
                          '-nop4', '-nosplash', '-stdout', '-FullStdOutLogOutput']
        if args.command == 'import': command.append('-NullRHI')
    else:
        command = base + review_flags(args, output, screenshot)
    if args.dry_run:
        print(dev.printed_command([str(value) for value in command]))
        return
    probe = subprocess.run(['pgrep', '-x', 'UnrealEditor'], capture_output=True, text=True)
    if probe.returncode == 0:
        raise SystemExit('An Unreal editor/game is already open. Finish it before this import/materials/review.')
    if probe.returncode != 1:
        raise SystemExit('Cannot inspect Unreal processes: ' + probe.stderr)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    if args.command in ('import', 'materials'):
        report_path = EVIDENCE / ('unreal-import.json' if args.command == 'import' else 'material-compilation.json')
        report_path.unlink(missing_ok=True)
        run(command, args.command)
        if json.loads(report_path.read_text(encoding='utf-8')).get('validated') is not True:
            raise SystemExit(f'{args.command.capitalize()} report did not validate.')
        return
    if args.seconds == 0:
        raise SystemExit(subprocess.call([str(value) for value in command], cwd=ROOT))
    output.unlink(missing_ok=True)
    run(command, label, args.seconds + 180)
    report = json.loads(output.read_text())
    try:
        validate_review(report, args)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    print(json.dumps({key: report[key] for key in ['rendered_bodies', 'rendered_helmets', 'rendered_armors',
                     'frames', 'median_fps', 'interval_fps', 'max_armor_bone_position_error_cm']}, indent=2))


if __name__ == '__main__':
    main()
