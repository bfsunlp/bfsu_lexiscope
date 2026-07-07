@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo [BFSU AlignLens] Cleaning old build folders...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist BFSU_AlignLens.spec del /q BFSU_AlignLens.spec

echo [BFSU AlignLens] Installing / updating packaging dependencies...
python -m pip install -U pip
python -m pip install -r requirements.txt
python -m pip install -U openai pyinstaller

echo [BFSU AlignLens] Building one-folder Windows package...
pyinstaller ^
  --noconfirm ^
  --clean ^
  --onedir ^
  --windowed ^
  --contents-directory "." ^
  --name "BFSU_AlignLens" ^
  --icon "assets\app.ico" ^
  --add-data "assets;assets" ^
  --add-data "locales;locales" ^
  --add-data "config;config" ^
  --add-data "Prompt.md;." ^
  --add-data "README.md;." ^
  --collect-submodules sentence_transformers ^
  --collect-submodules transformers ^
  --collect-submodules huggingface_hub ^
  --collect-submodules tokenizers ^
  --collect-submodules safetensors ^
  --collect-submodules openai ^
  --collect-submodules stanza ^
  --collect-submodules spacy ^
  --collect-submodules hanlp ^
  --collect-data certifi ^
  --hidden-import torch ^
  --hidden-import torchvision ^
  --hidden-import torchaudio ^
  --hidden-import numpy ^
  --hidden-import scipy ^
  --hidden-import sklearn ^
  --hidden-import openpyxl ^
  --hidden-import docx ^
  --hidden-import striprtf ^
  --hidden-import charset_normalizer ^
  --hidden-import lxml ^
  --hidden-import PIL ^
  main.py

if errorlevel 1 (
  echo.
  echo [BFSU AlignLens] Build failed. Please check the error messages above.
  pause
  exit /b 1
)

echo [BFSU AlignLens] Creating runtime folders beside the executable...
if not exist "dist\BFSU_AlignLens\models" mkdir "dist\BFSU_AlignLens\models"
if not exist "dist\BFSU_AlignLens\log" mkdir "dist\BFSU_AlignLens\log"
if not exist "dist\BFSU_AlignLens\exports" mkdir "dist\BFSU_AlignLens\exports"

> "dist\BFSU_AlignLens\models\README_models.txt" echo Put downloaded SentenceTransformer / Stanza / spaCy / HanLP model folders here if you want an offline package.

echo.
echo [BFSU AlignLens] Build completed: dist\BFSU_AlignLens\BFSU_AlignLens.exe
echo [BFSU AlignLens] Large model files are NOT bundled by this script. Copy your models folder manually into dist\BFSU_AlignLens\models when needed.
pause
