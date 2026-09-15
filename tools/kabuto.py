#!/usr/bin/env python3
"""Build, import and review the isolated Kabuto01 asset. One Unreal process at a time."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import dev

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'SourceArt/Characters/Samurai/Kabuto01'
EVIDENCE=ROOT/'artifacts/kabuto01'
LOCAL=ROOT/'artifacts/local/kabuto01'
BLENDER=Path('/Applications/Blender.app/Contents/MacOS/Blender')

def run(argv,label,timeout=600):
    LOCAL.mkdir(parents=True,exist_ok=True)
    argv=[str(x) for x in argv]
    print(dev.printed_command(argv),flush=True)
    (EVIDENCE/(label+'-command.json')).write_text(json.dumps(argv,indent=2)+'\n')
    with (LOCAL/(label+'.log')).open('w') as log:
        result=subprocess.run(argv,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
    print(f'Exit {result.returncode}: {LOCAL/(label+".log")}',flush=True)
    if result.returncode: raise SystemExit(result.returncode)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['source','export','validate','import','review'])
    p.add_argument('--engine')
    p.add_argument('--count',type=int,choices=[100,500,1000],default=100)
    p.add_argument('--mode',choices=['placeholder','mannequin','helmet'],default='helmet')
    p.add_argument('--camera',choices=['close','front','side','rear','tactical','far'],default='close')
    p.add_argument('--animation',choices=['idle','walk','head','none'],default='idle')
    p.add_argument('--seconds',type=float,default=10)
    p.add_argument('--label')
    args=p.parse_args(); EVIDENCE.mkdir(parents=True,exist_ok=True)
    if not 0<=args.seconds<=600: p.error('--seconds must be 0–600')
    if args.command in ('source','export','validate'):
        script={'source':'build_kabuto.py','export':'export_kabuto.py','validate':'validate_kabuto.py'}[args.command]
        run([BLENDER,'--background','--factory-startup','--python-exit-code','1','--python',ART/'Scripts'/script],args.command,900)
        return
    probe=subprocess.run(['pgrep','-x','UnrealEditor'],capture_output=True,text=True)
    if probe.returncode==0: raise SystemExit('An Unreal editor/game is already open. Finish that session before running this review.')
    if probe.returncode!=1: raise SystemExit('Cannot inspect running Unreal processes: '+probe.stderr)
    editor=dev.editor_executable(dev.resolve_engine_root(args.engine,os.environ))
    base=[editor,ROOT/'game/Shoen.uproject']
    if args.command=='import':
        run(base+[f'-ExecutePythonScript={ART/"Scripts/import_unreal.py"}','-unattended','-NullRHI','-nop4','-nosplash','-stdout','-FullStdOutLogOutput'],'import',900)
        report=json.loads((EVIDENCE/'unreal-import.json').read_text())
        if not report.get('validated'): raise SystemExit('Import report did not validate.')
        return
    label=args.label or f'{args.mode}-{args.count}-{args.camera}-{args.animation}'
    if Path(label).name!=label or not label: p.error('--label must be a filename stem')
    output=EVIDENCE/(label+'.json'); screenshot=EVIDENCE/(label+'.png')
    flags=['/Game/Art/Characters/Samurai/Kabuto01/Review/Kabuto01_Review?game=/Script/Shoen.KabutoReviewGameMode','-game','-windowed','-ResX=1600','-ResY=900','-NoVSync','-nop4','-nosplash','-stdout','-FullStdOutLogOutput',f'-KabutoCount={args.count}',f'-KabutoMode={args.mode}',f'-KabutoCamera={args.camera}',f'-KabutoAnimation={args.animation}',f'-KabutoSeconds={args.seconds}',f'-KabutoOutput={output}',f'-KabutoScreenshot={screenshot}']
    if args.seconds==0:
        raise SystemExit(subprocess.call([str(x) for x in base+flags],cwd=ROOT))
    output.unlink(missing_ok=True)
    run(base+flags,label,args.seconds+180)
    report=json.loads(output.read_text())
    if not report.get('validated') or not report.get('screenshot_exists'): raise SystemExit('Rendered review did not validate or capture.')
    print(json.dumps({k:report[k] for k in ['rendered_bodies','rendered_helmets','frames','median_fps','max_attachment_position_error_cm']},indent=2))

if __name__=='__main__': main()
