@echo off
:: Simple verification script to check if PyInstaller is working
echo Verifying PyInstaller installation...
python -m pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: PyInstaller is not installed or not accessible.
    echo Please install it using: pip install pyinstaller
    exit /b 1
) else (
    echo SUCCESS: PyInstaller is available.
    for /f "usebackq tokens=*" %%a in (`python -m pyinstaller --version`) do (
        echo Version: %%a
    )
)