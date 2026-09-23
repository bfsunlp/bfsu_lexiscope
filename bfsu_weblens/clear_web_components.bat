@echo off
setlocal
choice /M "Remove WebLens-managed portable browsers and WebDrivers? System Chrome/Edge will not be touched"
if errorlevel 2 exit /b 0
call "%~dp0maintenance.bat" clear-web
pause
