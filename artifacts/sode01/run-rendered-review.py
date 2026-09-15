"""Serial actual-Metal Sode captures, or bounded incremental timing comparison."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--performance', action='store_true')
args = parser.parse_args()
if args.performance:
    jobs = [(f'cost-{camera}-{mode}', mode, camera, 'idle', 'animation', 15)
            for camera in ('close', 'tactical') for mode in ('mannequin', 'armor', 'sode')]
else:
    jobs = [(f'final-{camera}', 'sode', camera, 'idle', 'animation', 6)
            for camera in ('front', 'back', 'left', 'right', 'rear', 'detail', 'tactical')]
    jobs += [(f'final-{clip}', 'sode', 'close', clip, 'animation', 8)
             for clip in ('walk', 'run', 'attack')]
    jobs += [(f'final-{pose}', 'sode', 'close', 'none', pose, 4)
             for pose in ('arms-raised', 'arms-forward', 'bow')]
results = []
for label, mode, camera, clip, pose, seconds in jobs:
    command = [sys.executable, str(ROOT/'tools/sode.py'), 'review', '--mode', mode,
               '--camera', camera, '--animation', clip, '--pose', pose,
               '--seconds', str(seconds), '--label', label]
    output = ROOT/'artifacts/local/sode01'/f'{label}-cli.log'
    with output.open('w') as log:
        result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=seconds+240)
    if result.returncode:
        raise SystemExit(f'{label} failed; inspect {output}')
    report = json.loads((ROOT/'artifacts/sode01'/f'{label}.json').read_text())
    results.append({'label':label,'validated':report['validated'], 'rhi':report['rhi'],
                    'frames':report['frames'],'median_fps':report['median_fps']})
    print(json.dumps(results[-1]), flush=True)
name = 'performance-runs.json' if args.performance else 'rendered-runs.json'
(ROOT/'artifacts/sode01'/name).write_text(json.dumps(results,indent=2)+'\n')
