# -*- coding: utf-8 -*-
"""Minimal Windows x64 ONEDIR builder for BFSU WebLens.

Goals:
- never expose a large source Conda environment through --system-site-packages;
- build from a private minimal environment;
- install PySide6-Essentials only (QtCore/QtGui/QtWidgets are all WebLens uses);
- explicitly exclude unrelated scientific/ML/notebook stacks;
- prune only demonstrably unused Qt payloads, then run a frozen smoke test;
- create a size report and release ZIP.

For a Conda source Python, a private Conda prefix is preferred because it owns
its native DLL runtime.  For standard CPython/venv, python -m venv is used.
"""
from __future__ import annotations

import os
import platform
import shutil
import struct
import subprocess
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP_NAME = "BFSU_WebLens"
BUILD_ENV = ROOT / ".venv_build_windows"
BUILD_DIR = ROOT / "build"
DIST_DIR = ROOT / "dist" / APP_NAME
INTERNAL_DIR = DIST_DIR / "_internal"
RELEASE_DIR = ROOT / "release"
LOG_DIR = ROOT / "build_logs"
LOG_FILE = LOG_DIR / "build_windows.log"
SIZE_REPORT = LOG_DIR / "bundle_size_report.txt"
VERSION_FILE = ROOT / ".build_version_info.txt"
SPEC_FILE = ROOT / f"{APP_NAME}.spec"
SOURCE_PREFIX = Path(os.environ.get("BFSU_WEBLENS_BASE_PREFIX", sys.prefix)).resolve()


def _version() -> str:
    ns: dict[str, object] = {}
    exec((ROOT / "bfsu_weblens" / "__init__.py").read_text(encoding="utf-8"), ns)
    return str(ns.get("__version__", "0.0.0"))


APP_VERSION = _version()
RELEASE_ZIP = RELEASE_DIR / f"{APP_NAME}_v{APP_VERSION}_windows_x64.zip"


def log(msg: str = "") -> None:
    print(msg, flush=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(msg + "\n")


def run(cmd, *, env=None, timeout=None) -> None:
    argv=[str(x) for x in cmd]
    log("> " + subprocess.list2cmdline(argv))
    with LOG_FILE.open("a", encoding="utf-8", newline="\n") as fh:
        p=subprocess.Popen(argv,cwd=str(ROOT),env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace")
        start=time.monotonic()
        assert p.stdout is not None
        for line in p.stdout:
            line=line.rstrip("\r\n")
            print(line,flush=True); fh.write(line+"\n"); fh.flush()
            if timeout and time.monotonic()-start>timeout:
                p.kill(); raise RuntimeError(f"Command timed out: {subprocess.list2cmdline(argv)}")
        rc=p.wait()
    if rc:
        raise RuntimeError(f"Command failed with exit code {rc}: {subprocess.list2cmdline(argv)}")


def capture(cmd, *, env=None) -> str:
    p=subprocess.run([str(x) for x in cmd],cwd=str(ROOT),env=env,capture_output=True,text=True,encoding="utf-8",errors="replace")
    if p.returncode:
        raise RuntimeError((p.stdout+"\n"+p.stderr).strip())
    return p.stdout.strip()


def is_conda(prefix: Path) -> bool:
    return (prefix / "conda-meta").exists() or bool(os.environ.get("CONDA_EXE"))


def system_dirs() -> list[str]:
    w=Path(os.environ.get("SystemRoot") or os.environ.get("WINDIR") or r"C:\Windows")
    return [str(p) for p in [w/'System32',w,w/'System32/Wbem',w/'System32/WindowsPowerShell/v1.0'] if p.exists()]


def clean_env(*, build_python: Path | None = None) -> dict[str,str]:
    env=os.environ.copy()
    for k in list(env):
        u=k.upper()
        # The build may be launched from an activated Conda/venv (for example
        # PyCharm Terminal).  None of that environment may leak into the
        # private build runtime once it has been created.
        if (u.startswith("QT_") or u.startswith("PYTHON") or u == "VIRTUAL_ENV"
                or u.startswith("CONDA") or u == "BFSU_WEBLENS_BASE_PREFIX"
                or u == "BFSU_WEBLENS_USE_BASE_DLLS"):
            env.pop(k, None)
    env["PYTHONNOUSERSITE"]="1"
    env["BFSU_WEBLENS_PRIVATE_BUILD"]="1"
    parts=[]
    if build_python:
        # Conda keeps python.exe at the prefix root; venv keeps it in Scripts.
        # Resolve the private prefix correctly in both layouts.
        if build_python.parent.name.lower() == "scripts":
            prefix = build_python.parent.parent
        else:
            prefix = build_python.parent
        parts.append(str(build_python.parent))
        if (prefix/'conda-meta').exists():
            parts += [str(prefix),str(prefix/'DLLs'),str(prefix/'Library/bin'),str(prefix/'Library/usr/bin'),str(prefix/'Scripts')]
    parts += system_dirs()
    env["PATH"]=os.pathsep.join(dict.fromkeys(p for p in parts if Path(p).exists()))
    return env


def check_host() -> None:
    log("[1/14] Checking Windows x64 build host...")
    if os.name!="nt": raise RuntimeError("Windows releases must be built on Windows.")
    if struct.calcsize("P")*8!=64: raise RuntimeError("64-bit Python is required.")
    if platform.machine().lower() not in {"amd64","x86_64","x64"}: raise RuntimeError("Windows x64 Python is required.")
    for p in [ROOT/'main.py',ROOT/'requirements.txt',ROOT/'requirements-build.txt',ROOT/'assets/app.ico',ROOT/'config/default_settings.json']:
        if not p.exists(): raise RuntimeError(f"Missing required file: {p.name}")
    log(f"  Bootstrap Python: {sys.executable}")
    log(f"  Bootstrap prefix: {SOURCE_PREFIX}")
    log(f"  Bootstrap type  : {'Conda' if is_conda(SOURCE_PREFIX) else 'standard/venv'}")
    log(f"  App version     : {APP_VERSION}")


def clean() -> None:
    log("[2/14] Cleaning previous build intermediates...")
    for p in [BUILD_ENV,BUILD_DIR,ROOT/'dist']:
        if p.exists(): shutil.rmtree(p,ignore_errors=False)
    for p in [SPEC_FILE,VERSION_FILE]:
        if p.exists(): p.unlink()
    for c in (ROOT/'bfsu_weblens').rglob('__pycache__'):
        shutil.rmtree(c,ignore_errors=True)


def find_conda_exe() -> Path | None:
    vals=[os.environ.get('CONDA_EXE')]
    vals += [str(SOURCE_PREFIX/'Scripts/conda.exe'),str(SOURCE_PREFIX/'condabin/conda.bat')]
    which=shutil.which('conda')
    if which: vals.append(which)
    for v in vals:
        if v and Path(v).exists(): return Path(v)
    return None


def create_private_env() -> tuple[Path,str]:
    log("[3/14] Creating a PRIVATE minimal build environment...")
    conda=find_conda_exe() if is_conda(SOURCE_PREFIX) else None
    if conda:
        log("  Conda bootstrap detected: creating a clean private Conda prefix (Python 3.12).")
        # conda.bat requires cmd /c; conda.exe can be called directly.
        cmd=[conda,'create','-y','-p',BUILD_ENV,'python=3.12','pip']
        if conda.suffix.lower()=='.bat': cmd=['cmd','/d','/c',conda,'create','-y','-p',BUILD_ENV,'python=3.12','pip']
        run(cmd, env=os.environ.copy())
        py=BUILD_ENV/'python.exe'
        mode='private-conda'
    else:
        log("  Standard Python bootstrap detected: creating an isolated venv.")
        run([sys.executable,'-m','venv','--clear','--copies',BUILD_ENV], env=clean_env())
        py=BUILD_ENV/'Scripts/python.exe'
        mode='private-venv'
    if not py.exists(): raise RuntimeError(f"Private build Python was not created: {py}")
    return py,mode


def install_minimal_runtime(py: Path) -> dict[str,str]:
    log("[4/14] Installing ONLY WebLens runtime + build dependencies...")
    env=clean_env(build_python=py)
    run([py,'-m','pip','install','--upgrade','pip','setuptools','wheel'],env=env)
    run([py,'-m','pip','install','--no-cache-dir','-r',ROOT/'requirements.txt'],env=env)
    run([py,'-m','pip','install','--no-cache-dir','-r',ROOT/'requirements-build.txt'],env=env)
    return env


def verify_runtime(py: Path, env: dict[str,str]) -> None:
    log("[5/14] Verifying the private minimal runtime...")
    log(f"  Private Python : {py}")
    log(f"  Private PATH   : {env.get('PATH', '')}")
    if str(SOURCE_PREFIX).lower() in env.get('PATH', '').lower():
        raise RuntimeError("Outer source environment leaked into the private build PATH.")
    run([py,ROOT/'build_probe.py','runtime-check'],env=env)
    # Prove that Addons/WebEngine are not installed in the minimal environment.
    code=("import importlib.util; "
          "print('PySide6_Addons=', bool(importlib.util.find_spec(\"PySide6.QtWebEngineCore\"))); "
          "from PySide6 import QtCore,QtGui,QtWidgets; print('Qt=',QtCore.qVersion())")
    run([py,'-c',code],env=env)


def compile_sources(py: Path, env: dict[str,str]) -> None:
    log("[6/14] Compiling sources and creating version metadata...")
    run([py,'-m','compileall','-q',ROOT/'bfsu_weblens',ROOT/'main.py',ROOT/'build_probe.py'],env=env)
    run([py,ROOT/'build_probe.py','write-version-info',VERSION_FILE],env=env)


def build_onedir(py: Path, env: dict[str,str]) -> None:
    log("[7/14] Building minimal PyInstaller ONEDIR package...")
    e=env.copy(); e['QT_API']='PySide6'
    excludes=[
        # Other GUI stacks
        'PyQt5','PyQt6','PySide2','tkinter',
        # Scientific/ML stacks WebLens never imports
        'numpy','pandas','scipy','sklearn','scikit_learn','matplotlib','seaborn',
        'torch','torchvision','torchaudio','tensorflow','keras','transformers','spacy',
        # Notebook/dev/test stacks
        'IPython','jupyter','notebook','pytest','setuptools.tests','pip._vendor',
        # Qt Addons not used by WebLens (Essentials should mean these are absent anyway)
        'PySide6.QtWebEngineCore','PySide6.QtWebEngineWidgets','PySide6.QtWebChannel',
        'PySide6.QtPdf','PySide6.QtPdfWidgets','PySide6.QtMultimedia','PySide6.QtMultimediaWidgets',
        'PySide6.QtQuick','PySide6.QtQml','PySide6.QtCharts','PySide6.QtDataVisualization',
        'PySide6.Qt3DCore','PySide6.Qt3DRender','PySide6.QtBluetooth','PySide6.QtNfc',
    ]
    args=[py,'-m','PyInstaller','--noconfirm','--clean','--onedir','--windowed','--contents-directory','_internal',
          '--name',APP_NAME,'--version-file',VERSION_FILE,'--icon',ROOT/'assets/app.ico',
          '--add-data',f"{ROOT/'assets'};assets",'--add-data',f"{ROOT/'config'};config",'--add-data',f"{ROOT/'README.md'};.",
          '--collect-data','newspaper','--collect-data','tldextract',
          '--hidden-import','lxml_html_clean','--hidden-import','charset_normalizer','--hidden-import','openpyxl','--hidden-import','docx',
          '--paths',ROOT]
    for x in excludes: args += ['--exclude-module',x]
    args.append(ROOT/'main.py')
    run(args,env=e)
    if not (DIST_DIR/f'{APP_NAME}.exe').exists() or not INTERNAL_DIR.exists():
        raise RuntimeError('PyInstaller did not produce the expected ONEDIR layout.')


def prune_qt_payload() -> None:
    log("[8/14] Pruning Qt payloads that WebLens does not use...")
    # Only remove categories that are irrelevant to a QtWidgets desktop app.
    candidates=[
        INTERNAL_DIR/'PySide6/Qt/qml',
        INTERNAL_DIR/'PySide6/Qt/translations',
        INTERNAL_DIR/'PySide6/Qt/resources',
        INTERNAL_DIR/'PySide6/Qt/plugins/designer',
        INTERNAL_DIR/'PySide6/Qt/plugins/qmltooling',
        INTERNAL_DIR/'PySide6/Qt/plugins/multimedia',
        INTERNAL_DIR/'PySide6/Qt/plugins/sqldrivers',
        INTERNAL_DIR/'PySide6/Qt/plugins/geoservices',
        INTERNAL_DIR/'PySide6/Qt/plugins/position',
        INTERNAL_DIR/'PySide6/Qt/plugins/sensors',
        INTERNAL_DIR/'PySide6/Qt/plugins/canbus',
        INTERNAL_DIR/'PySide6/Qt/plugins/gamepads',
        INTERNAL_DIR/'PySide6/Qt/plugins/webview',
    ]
    removed=0
    for p in candidates:
        if p.exists():
            if p.is_dir(): shutil.rmtree(p,ignore_errors=True)
            else: p.unlink(missing_ok=True)
            removed+=1
            log(f"  removed: {p.relative_to(DIST_DIR)}")
    if not removed: log("  No extra Qt payload directories were present; nothing to prune.")


def ensure_qwindows(py: Path, env: dict[str,str]) -> None:
    log("[9/14] Verifying qwindows.dll...")
    candidates=list(INTERNAL_DIR.rglob('qwindows.dll'))
    if candidates:
        log(f"  qwindows.dll: {candidates[0].relative_to(DIST_DIR)}")
        return
    plugins=Path(capture([py,ROOT/'build_probe.py','qt-plugins'],env=env).splitlines()[-1].strip())
    src=plugins/'platforms/qwindows.dll'
    if not src.exists(): raise RuntimeError(f"qwindows.dll not found in verified runtime: {src}")
    dst=INTERNAL_DIR/'qt_plugins/platforms'; dst.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst/'qwindows.dll')


def smoke_env() -> dict[str,str]:
    env=os.environ.copy()
    for k in list(env):
        u=k.upper()
        if u.startswith('QT_') or u.startswith('PYTHON') or u.startswith('CONDA') or u=='VIRTUAL_ENV': env.pop(k,None)
    env['PATH']=os.pathsep.join(system_dirs()); env['PYTHONNOUSERSITE']='1'
    return env


def smoke_test() -> None:
    log("[10/14] Running frozen Qt smoke test after pruning...")
    run([DIST_DIR/f'{APP_NAME}.exe','--qt-smoke-test'],env=smoke_env(),timeout=180)


def dir_size(p: Path) -> int:
    return sum(f.stat().st_size for f in p.rglob('*') if f.is_file()) if p.exists() else 0


def human(n: int) -> str:
    units=['B','KB','MB','GB','TB']; x=float(n)
    for u in units:
        if x<1024 or u==units[-1]: return f"{x:.2f} {u}"
        x/=1024
    return str(n)


def write_size_report() -> None:
    log("[11/14] Writing bundle-size report...")
    total=dir_size(DIST_DIR)
    rows=[]
    for p in INTERNAL_DIR.iterdir() if INTERNAL_DIR.exists() else []:
        size=dir_size(p) if p.is_dir() else p.stat().st_size
        rows.append((size,p.name))
    rows.sort(reverse=True)
    largest=[]
    for f in INTERNAL_DIR.rglob('*') if INTERNAL_DIR.exists() else []:
        if f.is_file(): largest.append((f.stat().st_size,str(f.relative_to(INTERNAL_DIR))))
    largest.sort(reverse=True)
    lines=[f"BFSU WebLens v{APP_VERSION} Windows bundle size report",f"Total dist size: {human(total)}","","Largest top-level _internal entries:"]
    lines += [f"{human(s):>12}  {n}" for s,n in rows[:30]]
    lines += ["","Largest individual files:"]+[f"{human(s):>12}  {n}" for s,n in largest[:50]]
    SIZE_REPORT.write_text("\n".join(lines)+"\n",encoding='utf-8')
    log(f"  Dist size: {human(total)}")
    log(f"  Report   : {SIZE_REPORT}")
    if total > 2*1024**3:
        log("  WARNING: bundle still exceeds 2 GB. Inspect bundle_size_report.txt before release.")


def verify_layout() -> None:
    log("[12/14] Verifying ONEDIR layout...")
    req=[DIST_DIR/f'{APP_NAME}.exe',INTERNAL_DIR,INTERNAL_DIR/'assets/app_256.png',INTERNAL_DIR/'config/default_settings.json']
    miss=[str(p.relative_to(ROOT)) for p in req if not p.exists()]
    if miss: raise RuntimeError('Frozen package is incomplete: '+', '.join(miss))


def make_zip() -> None:
    log("[13/14] Creating release ZIP...")
    RELEASE_DIR.mkdir(parents=True,exist_ok=True)
    if RELEASE_ZIP.exists(): RELEASE_ZIP.unlink()
    with zipfile.ZipFile(RELEASE_ZIP,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9,allowZip64=True) as zf:
        for p in sorted(DIST_DIR.rglob('*')):
            if p.is_file(): zf.write(p,p.relative_to(DIST_DIR.parent).as_posix())
    with zipfile.ZipFile(RELEASE_ZIP) as zf:
        bad=zf.testzip()
        if bad: raise RuntimeError(f'ZIP integrity failure: {bad}')
        names=set(zf.namelist())
        if f'{APP_NAME}/{APP_NAME}.exe' not in names: raise RuntimeError('EXE missing from release ZIP.')
        if not any(n.startswith(f'{APP_NAME}/_internal/') for n in names): raise RuntimeError('_internal missing from release ZIP.')
    log(f"  ZIP size : {human(RELEASE_ZIP.stat().st_size)}")


def finish(mode: str) -> None:
    log("[14/14] Final cleanup...")
    for p in [VERSION_FILE,SPEC_FILE]:
        if p.exists(): p.unlink()
    log(''); log('='*68); log('BUILD COMPLETE - SLIM WINDOWS RELEASE')
    log(f'Build env  : {mode}')
    log(f'Dist       : {DIST_DIR}')
    log(f'Release ZIP: {RELEASE_ZIP}')
    log(f'Size report: {SIZE_REPORT}')
    log('='*68)


def main() -> int:
    LOG_DIR.mkdir(parents=True,exist_ok=True); LOG_FILE.write_text('',encoding='utf-8')
    log(f'BFSU WebLens v{APP_VERSION} - Windows x64 SLIM build'); log(time.strftime('%Y-%m-%d %H:%M:%S')); log('')
    mode='unknown'
    try:
        check_host(); clean(); py,mode=create_private_env(); env=install_minimal_runtime(py); verify_runtime(py,env)
        compile_sources(py,env); build_onedir(py,env); prune_qt_payload(); ensure_qwindows(py,env); smoke_test(); write_size_report(); verify_layout(); make_zip(); finish(mode)
        return 0
    except Exception as exc:
        log(''); log('='*68); log('BUILD FAILED'); log(f'Reason: {exc}'); log(f'Build mode: {mode}'); log(f'Build log: {LOG_FILE}'); log(f'Size report: {SIZE_REPORT}'); log('='*68)
        return 1


if __name__=='__main__': raise SystemExit(main())
