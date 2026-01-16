@echo off
REM JDPowerDownloader Debug Launcher
REM This script sets up the environment and launches the debug version

echo Starting JDPowerDownloader Debug Version...
echo This version will show console output to help debug issues.

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Set Playwright browser path to the ms-playwright folder in the same directory
set PLAYWRIGHT_BROWSERS_PATH=%SCRIPT_DIR%ms-playwright

echo Browser path set to: %PLAYWRIGHT_BROWSERS_PATH%

REM Verify the browser path exists
if not exist "%PLAYWRIGHT_BROWSERS_PATH%" (
    echo ERROR: Browser folder not found at: %PLAYWRIGHT_BROWSERS_PATH%
    pause
    exit /b 1
)

echo Browser folder found. Launching debug application...
echo.
echo NOTE: You will see console output that will help identify any issues.
echo.

REM Launch the debug application
"%SCRIPT_DIR%JDPowerDownloader_Debug.exe"

echo.
echo Debug application has closed.
pause
