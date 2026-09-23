@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if exist "%~dp0BFSU_WebLens.exe" goto :packaged_mode

echo Source-code mode detected. The source folder will NOT be deleted.
choice /M "Reset WebLens user state and managed web components"
if errorlevel 2 exit /b 0
call "%~dp0maintenance.bat" purge-user-state
set "RC=%ERRORLEVEL%"
pause
exit /b %RC%

:packaged_mode
choice /M "Uninstall this portable BFSU WebLens release? User output/content folders will be preserved"
if errorlevel 2 exit /b 0

start "" /wait "%~dp0BFSU_WebLens.exe" --maintenance purge-user-state
set "APPDIR=%~dp0"
set "HELPER=%TEMP%\bfsu_weblens_uninstall_%RANDOM%%RANDOM%.bat"

>"%HELPER%" echo @echo off
>>"%HELPER%" echo timeout /t 2 /nobreak ^>nul
>>"%HELPER%" echo rmdir /s /q "%APPDIR%_internal" 2^>nul
>>"%HELPER%" echo rmdir /s /q "%APPDIR%tools" 2^>nul
>>"%HELPER%" echo del /q "%APPDIR%BFSU_WebLens.exe" 2^>nul
>>"%HELPER%" echo del /q "%APPDIR%README.md" "%APPDIR%MAINTENANCE.md" "%APPDIR%maintenance.bat" "%APPDIR%reset_user_settings.bat" "%APPDIR%clear_web_components.bat" "%APPDIR%uninstall_weblens.bat" 2^>nul
>>"%HELPER%" echo if exist "%APPDIR%output" goto :preserve
>>"%HELPER%" echo if exist "%APPDIR%content_downloads" goto :preserve
>>"%HELPER%" echo if exist "%APPDIR%weblens_google_results.xlsx" goto :preserve
>>"%HELPER%" echo if exist "%APPDIR%weblens_baidu_results.xlsx" goto :preserve
>>"%HELPER%" echo rmdir "%APPDIR%" 2^>nul
>>"%HELPER%" echo goto :done
>>"%HELPER%" echo :preserve
>>"%HELPER%" echo echo BFSU WebLens application files were removed. User output/content files were preserved in:
>>"%HELPER%" echo echo %APPDIR%
>>"%HELPER%" echo pause
>>"%HELPER%" echo :done
>>"%HELPER%" echo del /q "%%~f0"
start "" /min cmd /d /c ""%HELPER%""
exit /b 0
