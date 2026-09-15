"""Serial headless Shoen regression and Sode reference-pose verification."""
import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
import dev
EVIDENCE=ROOT/'artifacts/sode01';LOCAL=ROOT/'artifacts/local/sode01';REPORT=LOCAL/'unreal-tests'
REPORT.mkdir(parents=True,exist_ok=True)
command=[str(dev.editor_executable(dev.DEFAULT_ENGINE_ROOT)),str(ROOT/'game/Shoen.uproject'),'-ExecCmds=Automation RunTests Shoen.','-TestExit=Automation Test Queue Empty','-unattended','-NullRHI',f'-ReportExportPath={REPORT}','-nop4','-nosplash','-stdout','-FullStdOutLogOutput']
(EVIDENCE/'unreal-tests-command.json').write_text(json.dumps(command,indent=2)+'\n')
with (LOCAL/'unreal-tests.log').open('w') as log:result=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=300)
if result.returncode:raise SystemExit(result.returncode)
data=json.loads((REPORT/'index.json').read_text(encoding='utf-8-sig'))
summary=[{k:t[k] for k in ['fullTestPath','state','errors','warnings']} for t in data['tests']]
(EVIDENCE/'unreal-tests-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
tests,problems=dev.parse_automation_report(REPORT,'Shoen.')
if problems:raise SystemExit('\n'.join(problems))
assert any(t['fullTestPath']=='Shoen.Art.Sode.SuspensionMatchesBlender' for t in tests)
print(f'{len(tests)} Unreal tests passed')
