#!/usr/bin/env python3
"""Small serial rendered comparison; run only after other heavy work finishes."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'artifacts/kusazuri01'
sys.path.insert(0, str(ROOT / 'tools'))
import kusazuri

for name in ('Blender', 'UnrealEditor', 'ShaderCompileWorker'):
    probe = subprocess.run(['pgrep', '-x', name], capture_output=True, text=True)
    if probe.returncode != 1:
        raise SystemExit('Stop other heavy work before timing: ' + name)
cases = [(1, 'existing'), (1, 'kusazuri'), (100, 'existing'), (100, 'kusazuri'),
         (500, 'kusazuri'), (500, 'existing')]
rows = []
for count, mode in cases:
    camera = 'close' if count == 1 else 'tactical'
    seconds = 15 if count == 1 else 20
    label = f'cost-{count}-{mode}'
    arguments = ['review', '--camera', camera, '--count', str(count), '--mode', mode,
                 '--animation', 'idle', '--seconds', str(seconds), '--label', label]
    command = [sys.executable, str(ROOT / 'tools/kusazuri.py'), *arguments]
    started = time.time()
    print(f'Starting {label}', flush=True)
    result = subprocess.run(command, cwd=ROOT, timeout=seconds + 240)
    if result.returncode:
        raise SystemExit(result.returncode)
    report_path = EVIDENCE / (label + '.json')
    report = json.loads(report_path.read_text())
    kusazuri.validate_review(report, kusazuri.parse_args(arguments))
    rows.append({'label': label, 'count': count, 'mode': mode, 'camera': camera,
        'started_unix_seconds': started, 'finished_unix_seconds': time.time(),
        'report': str(report_path.relative_to(ROOT)), 'frames': report['frames'],
        'viewport': [report['viewport_width'], report['viewport_height']],
        'rhi': report['rhi'], 'frame': report['frame'], 'median_fps': report['median_fps'],
        'game_thread': report['game_thread'], 'render_thread': report['render_thread'],
        'gpu': report['gpu'], 'capture_seconds': report['capture_seconds'],
        'representation': report['crowd_representation']})
    (EVIDENCE / 'performance-runs.json').write_text(json.dumps({'runs': rows}, indent=2) + '\n')
comparisons = []
for count in (1, 100, 500):
    pair = {row['mode']: row for row in rows if row['count'] == count}
    before, after = pair['existing'], pair['kusazuri']
    if before['viewport'] != after['viewport'] or before['rhi'] != after['rhi']:
        raise SystemExit('Comparison viewport/RHI differs')
    delta = after['frame']['median_ms'] - before['frame']['median_ms']
    comparisons.append({'count': count, 'median_frame_delta_ms': delta,
        'median_frame_delta_percent': 100 * delta / before['frame']['median_ms'],
        'p95_frame_delta_ms': after['frame']['p95_ms'] - before['frame']['p95_ms']})
source = ROOT / 'SourceArt/Characters/Samurai/Kusazuri01/Kusazuri01.blend'
summary = {'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'runs': rows, 'comparisons': comparisons,
    'scope': 'Incremental art sanity check: one advancing native-idle character, plus 100/500 static outfit groups. No combat, population simulation or animated crowd claim.',
    'conditions': 'Sequential runs after coordinated Blender/build/review work finished; three-second warmup; no VSync; identical camera per count. Single trials; order reversed at 500.',
    'limits': 'Editor review validation overhead remains. Thermal/background variation is not eliminated. Null GPU counters are unavailable, not zero. Baseline close framing loads the waist asset; process memory is not isolated asset residency.'}
(EVIDENCE / 'performance-runs.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(comparisons, indent=2))
