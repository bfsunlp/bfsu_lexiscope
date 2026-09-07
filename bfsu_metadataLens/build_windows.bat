@echo off
setlocal
cd /d %~dp0
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
python -m PyInstaller --noconfirm --clean BFSU_MetadataLens.spec
endlocal
