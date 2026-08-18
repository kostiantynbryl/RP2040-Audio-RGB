@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo RP2040 Audio RGB is not installed yet.
    echo Run setup.bat first.
    echo.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" app.py
set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
    echo.
    echo Application exited with code %RC%.
    echo Run doctor.bat if you need diagnostics.
    pause
)

exit /b %RC%
