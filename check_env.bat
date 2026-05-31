@echo off
echo Checking Python and PyInstaller installation...
echo.

:: Check Python version
python --version
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    goto :end
)

echo.
echo Checking if pyinstaller is available as a module...
python -c "import pyinstaller; print('PyInstaller imported successfully')" 2>nul
if errorlevel 1 (
    echo ERROR: PyInstaller not found as Python module
    echo Trying to locate pyinstaller script...
    where pyinstaller 2>nul
    if errorlevel 1 (
        echo PyInstaller not found anywhere. Please install it:
        echo   pip install pyinstaller
    )
) else (
    echo SUCCESS: PyInstaller is available
)

:end
pause