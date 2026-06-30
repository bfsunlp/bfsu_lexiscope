@echo off
chcp 65001 >nul
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist BFSU_ProofLens.spec del /q BFSU_ProofLens.spec
if exist .venv_build rmdir /s /q .venv_build
if exist __pycache__ rmdir /s /q __pycache__
for /d /r %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
echo Clean finished.
pause
