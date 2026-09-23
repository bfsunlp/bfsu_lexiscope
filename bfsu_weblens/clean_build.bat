@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist .venv_build_windows rmdir /s /q .venv_build_windows
if exist BFSU_WebLens.spec del /q BFSU_WebLens.spec
if exist .build_version_info.txt del /q .build_version_info.txt
if exist build_logs rmdir /s /q build_logs
for /d /r bfsu_weblens %%D in (__pycache__) do if exist "%%D" rmdir /s /q "%%D"
echo Build intermediates cleaned. The release folder was kept.
pause
