@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "ACTION=%~1"
if "%ACTION%"=="" (
  echo Usage: maintenance.bat reset-settings^|clear-web^|purge-user-state^|self-check
  exit /b 2
)

if not exist "%~dp0BFSU_WebLens.exe" goto :source_mode
start "" /wait "%~dp0BFSU_WebLens.exe" --maintenance "%ACTION%"
exit /b %ERRORLEVEL%

:source_mode
set "PY="
if defined BFSU_WEBLENS_PYTHON if exist "%BFSU_WEBLENS_PYTHON%" set "PY=%BFSU_WEBLENS_PYTHON%"
if not defined PY if defined VIRTUAL_ENV if exist "%VIRTUAL_ENV%\Scripts\python.exe" set "PY=%VIRTUAL_ENV%\Scripts\python.exe"
if not defined PY if defined CONDA_PREFIX if exist "%CONDA_PREFIX%\python.exe" set "PY=%CONDA_PREFIX%\python.exe"
if not defined PY for %%P in (python.exe) do set "PY=%%~$PATH:P"
if not defined PY (
  echo [ERROR] Python was not found. Activate the WebLens environment or set BFSU_WEBLENS_PYTHON.
  exit /b 3
)
"%PY%" "%~dp0maintenance_cli.py" "%ACTION%"
exit /b %ERRORLEVEL%
