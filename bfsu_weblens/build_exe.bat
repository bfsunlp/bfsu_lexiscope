@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "APP_NAME=BFSU_WebLens"
set "VENV_DIR=.venv_build"
set "PY_EXE=%VENV_DIR%\Scripts\python.exe"

echo ============================================================
echo BFSU WebLens desktop build - isolated virtual environment
echo ============================================================
echo.
echo This script builds a PyInstaller onedir desktop release using
echo a local minimal virtual environment: %VENV_DIR%
echo.
echo Output layout target:
echo   dist\%APP_NAME%\%APP_NAME%.exe
echo   dist\%APP_NAME%\_internal\...
echo.

if /I "%~1"=="--fresh" (
    echo [INFO] --fresh specified. Removing old build virtual environment...
    if exist "%VENV_DIR%" rmdir /s /q "%VENV_DIR%"
)

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python was not found in PATH.
    echo Please install Python 3.10+ or add Python to PATH, then run this script again.
    pause
    exit /b 1
)

if not exist "%PY_EXE%" (
    echo [INFO] Creating local build virtual environment: %VENV_DIR%
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [INFO] Reusing existing local build virtual environment: %VENV_DIR%
    echo [INFO] Use build_exe.bat --fresh to recreate it from scratch.
)

if not exist "%PY_EXE%" (
    echo [ERROR] Virtual environment Python was not found: %PY_EXE%
    pause
    exit /b 1
)

echo.
echo [INFO] Build Python:
"%PY_EXE%" --version

echo.
echo [INFO] Upgrading core packaging tools inside the build environment...
"%PY_EXE%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
    echo [ERROR] Failed to upgrade pip/setuptools/wheel inside the build environment.
    pause
    exit /b 1
)

echo.
echo [INFO] Installing required runtime/build packages into the isolated environment...
echo [INFO] This keeps the release build independent from your daily Python/Conda environment.
"%PY_EXE%" -m pip install --no-cache-dir -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install requirements in the build virtual environment.
    pause
    exit /b 1
)

"%PY_EXE%" -m PyInstaller --version >nul 2>nul
if errorlevel 1 (
    echo [ERROR] PyInstaller is still unavailable after installing requirements.
    pause
    exit /b 1
)

echo.
echo [INFO] Cleaning previous PyInstaller outputs...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist %APP_NAME%.spec del /q %APP_NAME%.spec

echo.
echo [INFO] Building onedir package with dependencies/resources under _internal...

echo [INFO] Selenium packaging note: this build explicitly collects Selenium dynamic modules.
echo [INFO] If a previous packaged exe reported missing selenium.webdriver.chrome.webdriver,
echo [INFO] run build_exe.bat --fresh and rebuild the whole dist folder.
echo.

"%PY_EXE%" -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onedir ^
  --windowed ^
  --contents-directory "_internal" ^
  --name "%APP_NAME%" ^
  --icon "assets\app.ico" ^
  --add-data "assets;assets" ^
  --add-data "tools;tools" ^
  --collect-all selenium ^
  --collect-submodules selenium ^
  --collect-submodules newspaper ^
  --collect-data newspaper ^
  --collect-data tldextract ^
  --hidden-import selenium.webdriver ^
  --hidden-import selenium.webdriver.chrome ^
  --hidden-import selenium.webdriver.chrome.webdriver ^
  --hidden-import selenium.webdriver.chrome.service ^
  --hidden-import selenium.webdriver.chrome.options ^
  --hidden-import selenium.webdriver.edge ^
  --hidden-import selenium.webdriver.edge.webdriver ^
  --hidden-import selenium.webdriver.edge.service ^
  --hidden-import selenium.webdriver.edge.options ^
  --hidden-import selenium.webdriver.remote.webdriver ^
  --hidden-import selenium.webdriver.common.by ^
  --hidden-import selenium.webdriver.common.service ^
  --hidden-import selenium.webdriver.common.selenium_manager ^
  --hidden-import selenium.webdriver.common.driver_finder ^
  --hidden-import selenium.webdriver.support.ui ^
  --hidden-import lxml_html_clean ^
  --hidden-import charset_normalizer ^
  --hidden-import bs4 ^
  --hidden-import openpyxl ^
  --hidden-import docx ^
  main.py

if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller build failed.
    pause
    exit /b 1
)

echo.
echo [INFO] Copying release documentation and auxiliary files...
if exist README.md copy /Y README.md "dist\%APP_NAME%\README.md" >nul
if exist requirements.txt copy /Y requirements.txt "dist\%APP_NAME%\requirements.txt" >nul
if exist run.bat copy /Y run.bat "dist\%APP_NAME%\run_source_mode.bat" >nul
if exist tools (
    if not exist "dist\%APP_NAME%\_internal\tools" mkdir "dist\%APP_NAME%\_internal\tools"
    xcopy /E /I /Y tools "dist\%APP_NAME%\_internal\tools" >nul
)

echo.
echo [OK] Build finished.
echo [OK] Desktop release folder: dist\%APP_NAME%
echo [OK] Executable location: dist\%APP_NAME%\%APP_NAME%.exe
echo [OK] Internal dependency/resource folder: dist\%APP_NAME%\_internal
echo [OK] Build virtual environment retained at: %VENV_DIR%
echo.
echo Release instruction:
echo   Zip the whole dist\%APP_NAME% folder.
echo   Do not move %APP_NAME%.exe away from _internal.
echo.
echo Maintenance:
echo   Run build_exe.bat --fresh after major dependency changes.
echo   You may delete %VENV_DIR% later; it is only used for building, not for running the packaged app.
echo.
pause
