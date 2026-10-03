#!/usr/bin/env python3
"""Reproducible original samurai source/import/Unreal art laboratory commands."""
from __future__ import annotations
import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import dev

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'SourceArt/Characters/Samurai/Prototype01'
EVIDENCE=ROOT/'artifacts/samurai-prototype'
LOCAL=EVIDENCE/'local'
BLENDER=Path('/Applications/Blender.app/Contents/MacOS/Blender')

def run(argv, log, timeout=600):
    LOCAL.mkdir(parents=True,exist_ok=True)
    print(dev.printed_command(argv),flush=True)
    (LOCAL/(log+'.command.json')).write_text(json.dumps([str(a) for a in argv],indent=2)+'\n')
    with (LOCAL/(log+'.log')).open('w') as f:
        result=subprocess.run([str(a) for a in argv],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
    print(f'Exit {result.returncode}; {LOCAL/(log+".log")}',flush=True)
    if result.returncode: raise SystemExit(result.returncode)

def require_engine_idle():
    # Do not disturb an editor owned by another task/user. All our commands are
    # sequential; other processes must close normally before import/capture.
    result=subprocess.run(['pgrep','-x','UnrealEditor'],capture_output=True,text=True)
    if result.returncode==0: raise SystemExit('UnrealEditor is already running; close it normally before this command.')
    if result.returncode!=1: raise SystemExit('Could not verify that UnrealEditor is idle: '+result.stderr)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['source','validate-source','import','test','lab','benchmark'])
    p.add_argument('--engine'); p.add_argument('--soldiers',type=int,choices=[100,500,1000,2000],default=1000)
    p.add_argument('--representation',choices=['samurai','placeholder'],default='samurai')
    p.add_argument('--camera',choices=['close','tactical','wide'],default='wide')
    p.add_argument('--seconds',type=float,default=30)
    p.add_argument('--no-animation',action='store_true'); p.add_argument('--animation',type=int,choices=[0,1,2],default=1)
    p.add_argument('--label',default='')
    args=p.parse_args()
    if args.command in ('source','validate-source'):
        script='build_samurai.py' if args.command=='source' else 'validate_source.py'
        run([BLENDER,'--background','--factory-startup','--python-exit-code','1','--python',ART/'scripts'/script],args.command,900)
        return
    require_engine_idle()
    engine=dev.resolve_engine_root(args.engine,os.environ)
    editor=dev.editor_executable(engine); project=ROOT/'game/Shoen.uproject'
    base=[editor,project]
    if args.command=='import':
        result=EVIDENCE/'unreal-import.json'
        if result.exists(): result.unlink()
        run(base+[f'-ExecutePythonScript={ART/"scripts/import_unreal.py"}','-unattended','-nop4','-nosplash','-NullRHI','-stdout','-FullStdOutLogOutput'], 'unreal-import',900)
        if not result.exists() or not json.loads(result.read_text()).get('validated'): raise SystemExit('Unreal import produced no validated result.')
        return
    if args.command=='test':
        LOCAL.mkdir(parents=True,exist_ok=True)
        report=Path(tempfile.mkdtemp(prefix='automation-',dir=LOCAL))
        run(base+['-ExecCmds=Automation RunTests Shoen.','-TestExit=Automation Test Queue Empty','-unattended','-NullRHI',f'-ReportExportPath={report}','-nop4','-nosplash','-stdout','-FullStdOutLogOutput'],'unreal-tests')
        tests,problems=dev.parse_automation_report(report,'Shoen.')
        if problems: raise SystemExit('\n'.join(problems))
        if not any(t.get('fullTestPath','').startswith('Shoen.Samurai.') for t in tests): raise SystemExit('No samurai tests ran')
        summary=[{k:t.get(k) for k in ['fullTestPath','state','errors','warnings']} for t in tests]
        (EVIDENCE/'unreal-tests.json').write_text(json.dumps(summary,indent=2)+'\n')
        print(f'{len(tests)} Unreal tests passed')
        return
    flags=['/Game/Domain/Maps/Foundation?game=/Script/Shoen.SamuraiLabGameMode','-game','-windowed','-ResX=1600','-ResY=900','-NoVSync','-nop4','-nosplash',
        f'-ShoenSamuraiLabSoldiers={args.soldiers}',f'-ShoenSamuraiLabRepresentation={args.representation}',f'-ShoenSamuraiLabCamera={args.camera}',
        f'-ShoenSamuraiLabAnimation={0 if args.no_animation else 1}',f'-ShoenSamuraiLabAnimationIndex={args.animation}', '-stdout','-FullStdOutLogOutput']
    if args.command=='benchmark':
        label=args.label or f'{args.representation}-{args.soldiers}-{args.camera}'+('-static' if args.no_animation else '')
        if Path(label).name!=label: raise SystemExit('Label must be a filename stem')
        result=EVIDENCE/(label+'.json')
        if result.exists(): result.unlink()
        flags += ['-ShoenSamuraiLab',f'-ShoenSamuraiLabSeconds={args.seconds}',f'-ShoenSamuraiLabOutput={result}',f'-ShoenSamuraiLabCsv={EVIDENCE/(label+".csv")}',f'-ShoenSamuraiLabScreenshot={EVIDENCE/(label+".png")}']
        run(base+flags,label,args.seconds+180)
        if not result.exists(): raise SystemExit('No rendered benchmark result')
        data=json.loads(result.read_text())
        if data.get('soldiers')!=args.soldiers or data.get('frames',0)<1: raise SystemExit('Invalid rendered benchmark result')
        print(json.dumps({k:data.get(k) for k in ['soldiers','representation','median_fps','p95_frame_ms','median_gpu_frame_ms','median_game_thread_ms']},indent=2))
    else:
        print(dev.printed_command(base+flags)); raise SystemExit(subprocess.call([str(a) for a in base+flags],cwd=ROOT))
if __name__=='__main__': main()
