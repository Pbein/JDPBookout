@echo off
REM JDPowerDownloader Launcher - Clean Version
REM This script sets up the environment and launches the application without showing terminal

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Set Playwright browser path to the ms-playwright folder in the same directory
set PLAYWRIGHT_BROWSERS_PATH=%SCRIPT_DIR%ms-playwright

REM Verify the browser path exists
if not exist "%PLAYWRIGHT_BROWSERS_PATH%" (
    echo ERROR: Browser folder not found at: %PLAYWRIGHT_BROWSERS_PATH%
    echo Please make sure the ms-playwright folder is in the same directory as this script.
    pause
    exit /b 1
)

REM Launch the debug application (using the working debug executable)
cd /d "%SCRIPT_DIR%"
start "" "JDPowerDownloader_Debug.exe"

REM Exit without showing terminal
exit /b 0
