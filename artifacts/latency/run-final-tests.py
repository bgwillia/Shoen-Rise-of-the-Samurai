#!/usr/bin/env python3
"""Run all M2C regressions serially; all Unreal suites share one editor process."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'tools'))
import dev

checks=[('tooling-tests',['python3','-m','unittest','discover','-s','tools/tests','-v']),
        ('core-test',['python3','tools/dev.py','core-test']),
        ('build',['python3','tools/dev.py','build'])]
for name,command in checks:
    print('Running '+name,flush=True)
    with (root/'artifacts/latency'/f'final-{name}.log').open('w') as log:
        result=subprocess.run(command,cwd=root,stdout=log,stderr=subprocess.STDOUT,timeout=600)
    if result.returncode: raise SystemExit(f'{name}: exit {result.returncode}')
report=Path(tempfile.mkdtemp(prefix='m2c-unreal-',dir=root/'artifacts/local'))
command=[str(dev.editor_executable(dev.DEFAULT_ENGINE_ROOT)),str(root/'game/Shoen.uproject'),
         '-ExecCmds=Automation RunTests Shoen.', '-TestExit=Automation Test Queue Empty',
         '-unattended','-NullRHI',f'-ReportExportPath={report}','-nop4','-nosplash','-stdout','-FullStdOutLogOutput']
(root/'artifacts/latency/final-unreal-command.json').write_text(json.dumps(command,indent=2)+'\n')
print('Running all Shoen Unreal suites',flush=True)
with (root/'artifacts/latency/final-unreal.log').open('w') as log:
    result=subprocess.run(command,cwd=root,stdout=log,stderr=subprocess.STDOUT,timeout=600)
if result.returncode: raise SystemExit(f'Unreal exit {result.returncode}')
tests,problems=dev.parse_automation_report(report,'Shoen.')
if problems: raise SystemExit('\n'.join(problems))
data=json.loads((report/'index.json').read_text(encoding='utf-8-sig'))
summary={}
for suite,count in [('Foundation',5),('Placement',4),('Inspection',3),('Profiling',4)]:
    selected=[t for t in data['tests'] if t['fullTestPath'].startswith('Shoen.'+suite+'.')]
    if len(selected)!=count: raise SystemExit(f'Unexpected {suite} test count: {len(selected)}')
    summary[suite]=[{k:t[k] for k in ['fullTestPath','state','errors','warnings']} for t in selected]
(root/'artifacts/latency/final-unreal-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(f'All checks passed; {len(data["tests"])} Unreal tests',flush=True)
