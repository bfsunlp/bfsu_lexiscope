@echo off
chcp 65001 >nul
setlocal

echo =============================================
echo Building BFSU ProofLens Windows onedir package
echo =============================================

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist BFSU_ProofLens.spec del /q BFSU_ProofLens.spec

if not exist .venv_build (
  python -m venv .venv_build
)
call .venv_build\Scripts\activate
python -m pip install -U pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

pyinstaller --noconfirm --clean --onedir --windowed ^
  --name "BFSU_ProofLens" ^
  --icon "assets\app.ico" ^
  --add-data "assets;assets" ^
  --add-data "config;config" ^
  --add-data "models;models" ^
  --add-data "src;src" ^
  --hidden-import docx ^
  --hidden-import openpyxl ^
  --hidden-import lxml ^
  --hidden-import fitz ^
  --hidden-import rapidocr ^
  --hidden-import onnxruntime ^
  --hidden-import easyocr ^
  --hidden-import torch ^
  --hidden-import src.parallel_workers ^
  --hidden-import src.import_workers ^
  main.py

echo.
echo Build finished. Check dist\BFSU_ProofLens\BFSU_ProofLens.exe
pause
