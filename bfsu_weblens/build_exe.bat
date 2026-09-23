@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PY="
if defined BFSU_WEBLENS_PYTHON if exist "%BFSU_WEBLENS_PYTHON%" set "PY=%BFSU_WEBLENS_PYTHON%"
if not defined PY if defined VIRTUAL_ENV if exist "%VIRTUAL_ENV%\Scripts\python.exe" set "PY=%VIRTUAL_ENV%\Scripts\python.exe"
if not defined PY if defined CONDA_PREFIX if exist "%CONDA_PREFIX%\python.exe" set "PY=%CONDA_PREFIX%\python.exe"
if not defined PY for %%P in (python.exe) do set "PY=%%~$PATH:P"
if not defined PY (echo ERROR: No Python found.& pause & exit /b 2)
"%PY%" build_launcher.py
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (echo. & echo BUILD FAILED. See build_logs\build_windows.log & pause & exit /b %RC%)
echo.
echo BUILD COMPLETE. See release folder.
pause
exit /b 0
