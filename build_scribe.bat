@echo off
chcp 65001 > nul
echo ----------------------------------------
echo Scribe Compilation Script
echo ----------------------------------------

:: Get to the script's current directory (where scribe.spec should be)
cd /D "%~dp0"

echo [Step 1] Checking for old executable...
if exist "dist\Scribe.exe" (
    echo Found old Scribe.exe. Creating backup...
    if exist "dist\Scribe_backup.exe" (
        del /Q /F "dist\Scribe_backup.exe"
    )
    ren "dist\Scribe.exe" "Scribe_backup.exe"
    echo Backup created as Scribe_backup.exe inside "dist" folder.
) else (
    echo No old Scribe.exe found. Skipping backup.
)

echo.
echo [Step 2] Starting PyInstaller compilation...
echo Please wait, this may take a few minutes...
call pyinstaller scribe.spec

echo.
echo [Step 3] Verifying results...
if exist "dist\Scribe.exe" (
    echo ----------------------------------------
    echo SUCCESS: Compilation finished!
    echo The new Scribe.exe is ready in the "dist" folder.
    echo ----------------------------------------
) else (
    echo ----------------------------------------
    echo ERROR: Compilation failed!
    echo Scribe.exe was not generated.
    if exist "dist\Scribe_backup.exe" (
        echo Restoring the old backup so you don't lose the working version...
        ren "dist\Scribe_backup.exe" "Scribe.exe"
        echo Old Scribe.exe restored.
    )
    echo ----------------------------------------
)

pause
