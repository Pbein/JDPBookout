@echo off
REM JDPowerDownloader Launcher - Fixed Version
REM This script sets up the environment and launches the application

echo Starting JDPowerDownloader...
echo Setting up browser environment...

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Set Playwright browser path to the ms-playwright folder in the same directory
set PLAYWRIGHT_BROWSERS_PATH=%SCRIPT_DIR%ms-playwright

echo Browser path set to: %PLAYWRIGHT_BROWSERS_PATH%

REM Verify the browser path exists
if not exist "%PLAYWRIGHT_BROWSERS_PATH%" (
    echo ERROR: Browser folder not found at: %PLAYWRIGHT_BROWSERS_PATH%
    echo Please make sure the ms-playwright folder is in the same directory as this script.
    echo.
    echo Available files in this directory:
    dir /b
    echo.
    pause
    exit /b 1
)

echo Browser folder found. Checking for Chromium...

REM Check for Chromium specifically
set CHROMIUM_PATH=%PLAYWRIGHT_BROWSERS_PATH%\chromium-1187\chrome-win\chrome.exe
if not exist "%CHROMIUM_PATH%" (
    echo ERROR: Chromium browser not found at: %CHROMIUM_PATH%
    echo Available browsers:
    dir /b "%PLAYWRIGHT_BROWSERS_PATH%"
    echo.
    pause
    exit /b 1
)

echo Chromium browser found. Launching application...

REM Launch the application
"%SCRIPT_DIR%JDPowerDownloader.exe"

echo Application has closed.
pause
