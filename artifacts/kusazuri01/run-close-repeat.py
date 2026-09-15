#!/usr/bin/env python3
"""Reverse one close-view pair after an unexpected negative first-pair delta."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'artifacts/kusazuri01'
sys.path.insert(0, str(ROOT / 'tools'))
import kusazuri

for name in ('Blender', 'UnrealEditor', 'ShaderCompileWorker'):
    if subprocess.run(['pgrep', '-x', name], capture_output=True).returncode != 1:
        raise SystemExit('Stop other heavy work before timing: ' + name)
rows = []
for mode in ('kusazuri', 'existing'):
    label = 'cost-repeat-1-' + mode
    args = ['review', '--camera', 'close', '--count', '1', '--mode', mode,
            '--animation', 'idle', '--seconds', '15', '--label', label]
    result = subprocess.run([sys.executable, str(ROOT / 'tools/kusazuri.py'), *args], cwd=ROOT, timeout=255)
    if result.returncode:
        raise SystemExit(result.returncode)
    report = json.loads((EVIDENCE / (label + '.json')).read_text())
    kusazuri.validate_review(report, kusazuri.parse_args(args))
    rows.append({'label': label, 'mode': mode, 'report': label + '.json',
                 'frame': report['frame'], 'median_fps': report['median_fps'],
                 'gpu': report['gpu'], 'frames': report['frames'],
                 'viewport': [report['viewport_width'], report['viewport_height']],
                 'rhi': report['rhi']})
summary = {'reason': 'First single-character pair was unexpectedly faster with added armor. Reverse the order once to expose run-to-run variation; do not infer a speedup.',
           'conditions': 'Same close camera, native idle, three-second warmup,15-second sample command, no coordinated heavy work. Followed the original six serial trials.',
           'runs': rows, 'median_frame_delta_ms': rows[0]['frame']['median_ms'] - rows[1]['frame']['median_ms']}
(EVIDENCE / 'performance-close-repeat.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
