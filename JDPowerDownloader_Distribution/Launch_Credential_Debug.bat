@echo off
REM JDPowerDownloader Credential Debug Launcher
REM This version shows detailed credential debugging information

echo Starting JDPowerDownloader Credential Debug Version...
echo This version will show detailed credential information to help debug login issues.
echo.

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
echo NOTE: Watch for credential debug messages in the console output.
echo Look for lines starting with [WORKER] and DEBUG: to see what credentials are being used.
echo.

REM Launch the debug application
cd /d "%SCRIPT_DIR%"
JDPowerDownloader_Debug.exe

echo.
echo Application has closed.
pause

