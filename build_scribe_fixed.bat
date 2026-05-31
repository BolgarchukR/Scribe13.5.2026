@echo off
chcp 65001 > nul
echo ----------------------------------------
echo Scribe Compilation Script (Fixed v4 - preserving user data)
echo ----------------------------------------

:: Set the Python executable path
set PYTHON_EXE=C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe

:: Get to the script's current directory (where scribe.spec should be)
cd /D "%~dp0"

echo Using Python: %PYTHON_EXE%
"%PYTHON_EXE%" --version
if errorlevel 1 (
    echo ERROR: Python not found at %PYTHON_EXE%
    goto :end
)

echo.
echo [Step 1] Backing up user data (settings.json and models)...

if exist "dist\Scribe\settings.json" (
    echo Backing up settings.json...
    move /Y "dist\Scribe\settings.json" "dist\settings.json.bak"
)
if exist "dist\Scribe\models" (
    echo Backing up models folder...
    move /Y "dist\Scribe\models" "dist\models.bak"
)

echo.
echo [Step 2] Cleaning previous build artifacts...
if exist "build" rmdir /S /Q "build"
if exist "dist\Scribe" rmdir /S /Q "dist\Scribe"
echo Clean complete.

echo.
echo [Step 3] Starting PyInstaller compilation...
echo Please wait, this may take a few minutes...

"%PYTHON_EXE%" -m PyInstaller scribe.spec
if errorlevel 1 (
    echo PyInstaller failed with error code %errorlevel%
    goto :compilation_failed
)

echo.
echo [Step 4] Restoring user data...
if exist "dist\settings.json.bak" (
    echo Restoring settings.json...
    move /Y "dist\settings.json.bak" "dist\Scribe\settings.json"
)
if exist "dist\models.bak" (
    echo Restoring models folder...
    move /Y "dist\models.bak" "dist\Scribe\models"
)

echo.
echo [Step 5] Verifying results...
if exist "dist\Scribe\Scribe.exe" (
    echo ----------------------------------------
    echo SUCCESS: Compilation finished!
    echo The Scribe.exe is ready in "dist\Scribe\" folder.
    echo Your settings.json and models have been restored.
    echo ----------------------------------------
    goto :end
) else (
    echo ----------------------------------------
    echo ERROR: Compilation failed!
    echo Scribe.exe was not generated.
    echo Restoring user data...
    if exist "dist\settings.json.bak" (
        move /Y "dist\settings.json.bak" "dist\Scribe\settings.json"
    )
    if exist "dist\models.bak" (
        move /Y "dist\models.bak" "dist\Scribe\models"
    )
    echo ----------------------------------------
    goto :end
)

:compilation_failed
echo.
echo ----------------------------------------
echo ERROR: Compilation failed during PyInstaller execution!
echo Check the output above for details.
echo.
echo Attempting to show PyInstaller error logs...
if exist "build\Scribe\warn-Scribe.txt" (
    echo --- Warning log (first 20 lines) ---
    type "build\Scribe\warn-Scribe.txt" | more +0
)
echo.
echo Restoring user data...
if exist "dist\settings.json.bak" (
    move /Y "dist\settings.json.bak" "dist\Scribe\settings.json"
)
if exist "dist\models.bak" (
    move /Y "dist\models.bak" "dist\Scribe\models"
)
echo ----------------------------------------

:end
pause
