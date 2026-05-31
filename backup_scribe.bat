@echo off
chcp 65001 > nul
echo ----------------------------------------
echo Scribe Source Code Backup Script
echo ----------------------------------------

:: Get to the script's current directory
cd /D "%~dp0"

:: Get current date and time for the filename
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set YYYY=%datetime:~0,4%
set MM=%datetime:~4,2%
set DD=%datetime:~6,2%
set HH=%datetime:~8,2%
set MIN=%datetime:~10,2%

set BACKUP_NAME=Scribe_Source_Backup_%YYYY%-%MM%-%DD%_%HH%-%MIN%.zip

echo Creating backup: %BACKUP_NAME%
echo Please wait...

:: Use PowerShell to zip only the source code and exclude heavy folders (dist, models, .git, venv)
powershell.exe -Command "Compress-Archive -Path 'scribe', 'resources', 'run.py', 'build_scribe.bat', 'scribe.spec' -DestinationPath '%BACKUP_NAME%' -Force"

if exist "%BACKUP_NAME%" (
    echo.
    echo ----------------------------------------
    echo SUCCESS: Backup created!
    echo File: %BACKUP_NAME%
    echo ----------------------------------------
) else (
    echo.
    echo ----------------------------------------
    echo ERROR: Failed to create backup.
    echo ----------------------------------------
)

pause
