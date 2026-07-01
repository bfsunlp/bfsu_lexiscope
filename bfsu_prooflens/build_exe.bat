@echo off
chcp 65001 >nul
setlocal
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo =============================================
echo Building BFSU ProofLens Windows onedir package
echo RapidOCR / ONNXRuntime PyInstaller fixed build
echo =============================================

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist BFSU_ProofLens.spec del /q BFSU_ProofLens.spec

if not exist .venv_build (
  python -m venv .venv_build
)
call .venv_build\Scripts\activate

python -m pip install -U pip setuptools wheel
python -m pip install -r requirements.txt
python -m pip install -U pyinstaller

echo.
echo [1/3] Checking RapidOCR and ONNXRuntime in build environment...
python -c "import rapidocr, onnxruntime; from rapidocr import RapidOCR; print('RapidOCR=', getattr(rapidocr, '__version__', 'unknown')); print('ONNXRuntime=', getattr(onnxruntime, '__version__', 'unknown')); print('RapidOCR import OK')"
if errorlevel 1 (
  echo.
  echo ERROR: RapidOCR / ONNXRuntime cannot be imported in the build environment.
  echo Please check network access and run:
  echo python -m pip install rapidocr onnxruntime
  pause
  exit /b 1
)

echo.
echo [2/3] Running PyInstaller with RapidOCR hooks...
pyinstaller --noconfirm --clean --onedir --windowed ^
  --name "BFSU_ProofLens" ^
  --icon "assets\app.ico" ^
  --additional-hooks-dir "hooks" ^
  --add-data "assets;assets" ^
  --add-data "config;config" ^
  --add-data "models;models" ^
  --add-data "src;src" ^
  --collect-all rapidocr ^
  --collect-all onnxruntime ^
  --collect-all numpy ^
  --collect-all PIL ^
  --copy-metadata rapidocr ^
  --copy-metadata onnxruntime ^
  --collect-submodules rapidocr ^
  --collect-submodules onnxruntime ^
  --collect-binaries onnxruntime ^
  --hidden-import docx ^
  --hidden-import openpyxl ^
  --hidden-import lxml ^
  --hidden-import fitz ^
  --hidden-import rapidocr ^
  --hidden-import onnxruntime ^
  --hidden-import onnxruntime.capi ^
  --hidden-import onnxruntime.capi.onnxruntime_pybind11_state ^
  --hidden-import PIL._tkinter_finder ^
  --hidden-import easyocr ^
  --hidden-import torch ^
  --hidden-import torchvision ^
  --hidden-import src.parallel_workers ^
  --hidden-import src.import_workers ^
  main.py

if errorlevel 1 (
  echo.
  echo ERROR: PyInstaller build failed.
  pause
  exit /b 1
)

echo.
echo [3/3] Checking packaged executable imports...
if exist "dist\BFSU_ProofLens\_internal" (
  echo onedir package created: dist\BFSU_ProofLens
) else (
  echo WARNING: dist\BFSU_ProofLens\_internal was not found. Please check the dist folder manually.
)

echo.
echo Build finished. Check dist\BFSU_ProofLens\BFSU_ProofLens.exe
pause
