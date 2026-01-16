@echo off
REM JDPowerDownloader Debug Launcher
REM This version shows console output to help debug issues

echo Starting JDPowerDownloader Debug Version...
echo This version will show console output to help debug issues.
echo.

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Set Playwright browser path to the ms-playwright folder in the same directory
set PLAYWRIGHT_BROWSERS_PATH=%SCRIPT_DIR%ms-playwright

echo Browser path set to: %PLAYWRIGHT_BROWSERS_PATH%

REM Verify the browser path exists
if not exist "%PLAYWRIGHT_BROWSERS_PATH%" (
    echo ERROR: Browser folder not found at: %PLAYWRIGHT_BROWSERS_PATH%
    echo Please make sure the ms-playwright folder is in the same directory as this script.
    pause
    exit /b 1
)

echo Browser folder found. Launching application...
echo.
echo NOTE: You will see console output that will help identify any issues.
echo.

REM Launch the application (this will show console output)
REM We need to run the executable directly to see console output
cd /d "%SCRIPT_DIR%"
JDPowerDownloader.exe

echo.
echo Application has closed.
pause
