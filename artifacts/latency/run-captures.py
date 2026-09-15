#!/usr/bin/env python3
"""Reproduce the Mac development latency captures, one rendered game at a time."""
import argparse
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--counts', nargs='+', type=int, choices=(1, 10, 100), default=[1, 10, 100])
parser.add_argument('--iterations', type=int, default=30)
parser.add_argument('--disabled', action='store_true')
parser.add_argument('--cap', type=int, default=0)
parser.add_argument('--label', default='uncapped')
args = parser.parse_args()
editor = Path('/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor')
for count in args.counts:
    name = f'{args.label}-{count}'
    output = root / 'artifacts/latency' / f'{name}.json'
    if output.exists() or Path(str(output)+'.frames.json').exists():
        raise SystemExit(f'Refusing to overwrite existing capture: {output}')
    command = [str(editor), str(root/'game/Shoen.uproject'), '/Game/Domain/Maps/Foundation',
               '-game', '-ShoenScenario=settlement', '-windowed', '-ResX=1600', '-ResY=900', '-NoVSync',
               f'-ShoenProfileBuildings={count}', f'-ShoenProfileIterations={args.iterations}',
               f'-ShoenProfileOutput={output}', '-stdout', '-FullStdOutLogOutput']
    if args.disabled:
        command.append('-ShoenProfileDisabled')
    if args.cap:
        command.append(f'-ExecCmds=t.MaxFPS {args.cap}')
    (output.parent/f'{name}-command.json').write_text(json.dumps(command, indent=2)+'\n')
    print(f'Starting {name}', flush=True)
    with (root/'artifacts/local'/f'm2c-{name}.log').open('w') as log:
        result = subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT, timeout=600)
    if result.returncode:
        raise SystemExit(f'{name}: Unreal exit {result.returncode}')
    frames = json.loads(Path(str(output)+'.frames.json').read_text())
    if not frames.get('completed'):
        raise SystemExit(f'{name}: replay did not complete its correctness checks')
    if not args.disabled:
        subprocess.run(['python3', str(root/'tools/latency.py'), str(output), '--output',
                        str(output.parent/f'{name}-report.json')], cwd=root, check=True)
    print(f'Completed {name}', flush=True)
