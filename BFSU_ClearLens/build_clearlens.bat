@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "VENV_DIR=%CD%\virtual_env"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "DIST_DIR=%CD%\dist\BFSU_ClearLens"

if not exist "%VENV_PYTHON%" (
  echo Creating isolated build environment: virtual_env
  where py >nul 2>nul
  if not errorlevel 1 (
    py -3 -m venv "%VENV_DIR%"
  ) else (
    python -m venv "%VENV_DIR%"
  )
  if errorlevel 1 goto :error
)

echo Installing build and runtime dependencies in virtual_env...
"%VENV_PYTHON%" -m pip install --disable-pip-version-check --upgrade pip
if errorlevel 1 goto :error
"%VENV_PYTHON%" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto :error

echo Building minimal complete onedir package...
"%VENV_PYTHON%" -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --windowed ^
  --onedir ^
  --contents-directory "_internal" ^
  --name "BFSU_ClearLens" ^
  --icon "assets\app.ico" ^
  --version-file "assets\version_info.txt" ^
  --collect-all tkinterdnd2 ^
  --collect-all customtkinter ^
  --copy-metadata customtkinter ^
  --collect-data ftfy ^
  --collect-data opencc ^
  --collect-submodules openai ^
  --copy-metadata openai ^
  --copy-metadata pydantic ^
  --hidden-import PIL.Image ^
  --hidden-import PIL.ImageTk ^
  --hidden-import PIL._tkinter_finder ^
  --exclude-module pytest ^
  --exclude-module IPython ^
  --exclude-module matplotlib ^
  --exclude-module pandas ^
  --exclude-module numpy ^
  main.py
if errorlevel 1 goto :error

for %%D in (assets config samples) do (
  if exist "%DIST_DIR%\%%D" rmdir /s /q "%DIST_DIR%\%%D"
  xcopy "%%D" "%DIST_DIR%\%%D\" /E /I /Y /Q >nul
  if errorlevel 1 goto :error
)

for %%F in (README.md technical_readme.md RELEASE_NOTES.md requirements.txt) do (
  copy /Y "%%F" "%DIST_DIR%\%%F" >nul
  if errorlevel 1 goto :error
)

if not exist "%DIST_DIR%\BFSU_ClearLens.exe" goto :layout_error
if not exist "%DIST_DIR%\_internal" goto :layout_error
if not exist "%DIST_DIR%\assets\app.ico" goto :layout_error
if not exist "%DIST_DIR%\assets\app.png" goto :layout_error
if not exist "%DIST_DIR%\assets\clearlens_theme.json" goto :layout_error
if not exist "%DIST_DIR%\config\default_settings.json" goto :layout_error
if not exist "%DIST_DIR%\config\regex_rules.json" goto :layout_error
if not exist "%DIST_DIR%\samples\sample_noisy_text.txt" goto :layout_error
if not exist "%DIST_DIR%\README.md" goto :layout_error
if not exist "%DIST_DIR%\technical_readme.md" goto :layout_error
if not exist "%DIST_DIR%\RELEASE_NOTES.md" goto :layout_error
if not exist "%DIST_DIR%\requirements.txt" goto :layout_error

echo.
echo Build completed and layout verified.
echo Executable: %DIST_DIR%\BFSU_ClearLens.exe
echo Runtime dependencies: %DIST_DIR%\_internal
echo External resources and documentation: %DIST_DIR%
pause
exit /b 0

:layout_error
echo.
echo Build finished, but the release directory layout is incomplete.
goto :error

:error
echo.
echo Build failed. Review the messages above.
pause
exit /b 1
