@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

title BFSU MetadataLens - Minimal Venv Build

echo ============================================================
echo  BFSU MetadataLens - Minimal Virtual Environment Build
echo ============================================================
echo.
echo This script does NOT modify the program source code.
echo It creates a clean build-only virtual environment and installs
echo only the packages required by BFSU MetadataLens.
echo.

set "VENV=.venv_build_min"
set "VPY=%VENV%\Scripts\python.exe"

rem ------------------------------------------------------------
rem Optional cleanup mode:
rem     build_minimal_venv.bat clean
rem ------------------------------------------------------------
if /I "%~1"=="clean" goto :CLEAN

rem ------------------------------------------------------------
rem 1. Remove previous build environment and PyInstaller output
rem ------------------------------------------------------------
echo [1/6] Cleaning previous build files...
if exist "%VENV%" rmdir /s /q "%VENV%"
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

rem ------------------------------------------------------------
rem 2. Create a fresh Python 3.12 virtual environment
rem ------------------------------------------------------------
echo.
echo [2/6] Creating minimal Python virtual environment...

where py >nul 2>nul
if not errorlevel 1 (
    py -3.12 -m venv "%VENV%"
)

if not exist "%VPY%" (
    python -m venv "%VENV%"
)

if not exist "%VPY%" (
    echo.
    echo ERROR: Failed to create the virtual environment.
    echo Please make sure Python 3.12 is installed and available in PATH.
    pause
    exit /b 1
)

rem ------------------------------------------------------------
rem 3. Install ONLY required packages
rem ------------------------------------------------------------
echo.
echo [3/6] Installing minimal dependencies...

"%VPY%" -m pip install --disable-pip-version-check --no-cache-dir --upgrade pip
if errorlevel 1 goto :ERROR

"%VPY%" -m pip install --disable-pip-version-check --no-cache-dir ^
    "pyinstaller>=6.10,<7" ^
    "customtkinter>=5.2.2,<6" ^
    "openpyxl>=3.1.2,<4" ^
    "pypdf>=5,<7" ^
    "openai>=2,<3" ^
    "Pillow>=10,<13"

if errorlevel 1 goto :ERROR

rem ------------------------------------------------------------
rem 4. Verify the clean environment
rem ------------------------------------------------------------
echo.
echo [4/6] Checking installed packages...

"%VPY%" -m pip check
if errorlevel 1 goto :ERROR

echo.
"%VPY%" -c "import customtkinter, openpyxl, pypdf, openai, PIL; print('Runtime dependencies: OK')"
if errorlevel 1 goto :ERROR

rem ------------------------------------------------------------
rem 5. Build
rem Prefer the project's existing .spec file so the program code,
rem resources, icon and current packaging rules stay unchanged.
rem ------------------------------------------------------------
echo.
echo [5/6] Building BFSU MetadataLens...

if exist "BFSU_MetadataLens.spec" (
    "%VPY%" -m PyInstaller --noconfirm --clean "BFSU_MetadataLens.spec"
) else (
    echo ERROR: BFSU_MetadataLens.spec was not found in:
    echo        %CD%
    echo.
    echo Please place this BAT file in the BFSU MetadataLens source
    echo directory together with BFSU_MetadataLens.spec.
    pause
    exit /b 1
)

if errorlevel 1 goto :ERROR

rem ------------------------------------------------------------
rem 6. Report final package size
rem ------------------------------------------------------------
echo.
echo [6/6] Build completed.

if exist "dist\BFSU_MetadataLens" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
      "$p='dist\BFSU_MetadataLens';" ^
      "$files=Get-ChildItem $p -Recurse -File;" ^
      "$size=($files | Measure-Object Length -Sum).Sum;" ^
      "Write-Host '';" ^
      "Write-Host ('Output: ' + (Resolve-Path $p));" ^
      "Write-Host ('Total size: {0:N1} MB' -f ($size/1MB));" ^
      "Write-Host '';" ^
      "Write-Host 'Largest 15 files:';" ^
      "$files | Sort-Object Length -Descending | Select-Object -First 15 @{N='MB';E={[math]::Round($_.Length/1MB,2)}},FullName | Format-Table -AutoSize"
) else (
    echo Output folder: dist
)

echo.
echo ============================================================
echo  BUILD SUCCESSFUL
echo ============================================================
echo.
echo The build-only virtual environment is:
echo     %VENV%
echo.
echo It is NOT included in the packaged application.
echo To remove it later, run:
echo     build_minimal_venv.bat clean
echo.
echo API keys stored under %%APPDATA%% are not copied into dist.
echo.
pause
exit /b 0

:CLEAN
echo Cleaning build environment and output...
if exist "%VENV%" rmdir /s /q "%VENV%"
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
echo Clean complete.
pause
exit /b 0

:ERROR
echo.
echo ============================================================
echo  BUILD FAILED
echo ============================================================
echo Check the error message above.
echo.
pause
exit /b 1
