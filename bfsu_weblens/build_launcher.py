# -*- coding: utf-8 -*-
"""Windows build bootstrap selector for the WebLens slim builder."""
from __future__ import annotations
import os, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
LOG=ROOT/'build_logs'/'build_launcher.log'

def emit(s=''):
    print(s,flush=True); LOG.parent.mkdir(parents=True,exist_ok=True)
    with LOG.open('a',encoding='utf-8') as f:f.write(s+'\n')

def candidates():
    seen=set(); out=[]
    def add(p):
        if not p:return
        q=Path(p)
        if q.exists():
            q=q.resolve()
            k=str(q).lower()
            if k not in seen: seen.add(k);out.append(q)
    add(os.environ.get('BFSU_WEBLENS_PYTHON'))
    if os.environ.get('VIRTUAL_ENV'): add(Path(os.environ['VIRTUAL_ENV'])/'Scripts/python.exe')
    if os.environ.get('CONDA_PREFIX'): add(Path(os.environ['CONDA_PREFIX'])/'python.exe')
    # Known BFSU LexiScope environment relative to the project tree.
    for parent in [ROOT,*ROOT.parents]: add(parent/'conda_envs/bfsu_lexiscope/python.exe')
    add(sys.executable)
    return out

def usable(py:Path)->bool:
    code='import struct,sys; raise SystemExit(0 if sys.platform=="win32" and struct.calcsize("P")==8 and (3,10)<=sys.version_info[:2]<(3,14) else 2)'
    return subprocess.run([str(py),'-c',code],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0

def main():
    LOG.parent.mkdir(parents=True,exist_ok=True);LOG.write_text('',encoding='utf-8')
    emit('BFSU WebLens Windows SLIM build launcher')
    for py in candidates():
        emit(f'Checking bootstrap Python: {py}')
        if not usable(py): emit('  rejected');continue
        emit('  selected')
        env=os.environ.copy();env['BFSU_WEBLENS_BASE_PREFIX']=str(py.parent if not (py.parent.name.lower()=='scripts') else py.parent.parent)
        return subprocess.call([str(py),str(ROOT/'build_windows.py')],cwd=str(ROOT),env=env)
    emit('ERROR: no suitable Windows x64 Python 3.10-3.13 found.')
    return 2
if __name__=='__main__':raise SystemExit(main())
