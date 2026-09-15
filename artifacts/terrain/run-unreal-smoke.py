#!/usr/bin/env python3
"""Run existing regression suites plus one integrated prototype test in one editor."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'tools'))
import dev
report=Path(tempfile.mkdtemp(prefix='terrain-unreal-',dir=root/'artifacts/local'))
command=[str(dev.editor_executable(dev.DEFAULT_ENGINE_ROOT)),str(root/'game/Shoen.uproject'),
 '-ExecCmds=Automation RunTests Shoen.','-TestExit=Automation Test Queue Empty','-unattended','-NullRHI',
 f'-ReportExportPath={report}','-nop4','-nosplash','-stdout','-FullStdOutLogOutput']
(root/'artifacts/terrain/unreal-command.json').write_text(json.dumps(command,indent=2)+'\n')
with (root/'artifacts/terrain/unreal-tests.log').open('w') as log:
 result=subprocess.run(command,cwd=root,stdout=log,stderr=subprocess.STDOUT,timeout=300)
if result.returncode: raise SystemExit(result.returncode)
tests,problems=dev.parse_automation_report(report,'Shoen.')
if problems: raise SystemExit('\n'.join(problems))
data=json.loads((report/'index.json').read_text(encoding='utf-8-sig'))
summary=[{k:t[k] for k in ['fullTestPath','state','errors','warnings']} for t in data['tests']]
(root/'artifacts/terrain/unreal-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
if not any(t['fullTestPath']=='Shoen.Prototype.TerrainIntegration' for t in tests): raise SystemExit('Missing prototype test')
print(f'{len(tests)} Unreal tests passed; report {report}')
