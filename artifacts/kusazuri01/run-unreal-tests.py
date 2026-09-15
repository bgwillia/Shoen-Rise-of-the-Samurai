#!/usr/bin/env python3
"""Run the SHŌEN suite once, including frozen Blender/Unreal hinge parity."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'artifacts/kusazuri01'
sys.path.insert(0, str(ROOT / 'tools'))
import dev

fixture = EVIDENCE / 'hinge-reference-poses.json'
if not fixture.is_file():
    raise SystemExit('Measure final saved-source motion before running native parity tests.')
frozen = json.loads(fixture.read_text())
art = ROOT / 'SourceArt/Characters/Samurai/Kusazuri01'
for key, path in [('source_sha256', art / 'Kusazuri01.blend'),
                  ('motion_script_sha256', art / 'Scripts/kusazuri_motion.py')]:
    if frozen.get(key) != hashlib.sha256(path.read_bytes()).hexdigest():
        raise SystemExit('Frozen hinge fixture does not match final ' + path.name)
if frozen.get('expected_target_source') != 'Unmodified armor_pose return values, frozen before Unreal verification.':
    raise SystemExit('Native verification requires production controller expectations.')
probe = subprocess.run(['pgrep', '-x', 'UnrealEditor'], capture_output=True, text=True)
if probe.returncode != 1:
    raise SystemExit('An Unreal editor is open, or its process state could not be checked.')
report = Path(tempfile.mkdtemp(prefix='kusazuri-unreal-', dir=ROOT / 'artifacts/local'))
command = [str(dev.editor_executable(dev.DEFAULT_ENGINE_ROOT)), str(ROOT / 'game/Shoen.uproject'),
    '-ExecCmds=Automation RunTests Shoen.', '-TestExit=Automation Test Queue Empty',
    '-unattended', '-NullRHI', f'-ReportExportPath={report}', '-nop4', '-nosplash',
    '-stdout', '-FullStdOutLogOutput']
(EVIDENCE / 'unreal-tests-command.json').write_text(json.dumps(command, indent=2) + '\n')
with (EVIDENCE / 'unreal-tests.log').open('w') as log:
    result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=300)
tests, problems = dev.parse_automation_report(report, 'Shoen.')
summary = [{key: test.get(key) for key in ('fullTestPath', 'state', 'errors', 'warnings')} for test in tests]
(EVIDENCE / 'unreal-tests-summary.json').write_text(json.dumps({
    'exit_code': result.returncode, 'report_directory': str(report), 'tests': summary,
    'problems': problems, 'rendering_claim': False}, indent=2) + '\n')
if result.returncode:
    raise SystemExit(result.returncode)
if problems:
    raise SystemExit('\n'.join(problems))
paths = {test['fullTestPath'] for test in tests}
required = {'Shoen.Art.Kusazuri.HingeMath', 'Shoen.Art.Kusazuri.HingesMatchBlender',
            'Shoen.Prototype.TerrainIntegration'}
if not required.issubset(paths):
    raise SystemExit('Missing required regression or Kusazuri parity test: ' + str(required - paths))
print(f'{len(tests)} Unreal tests passed. This NullRHI run is logic evidence only.')
