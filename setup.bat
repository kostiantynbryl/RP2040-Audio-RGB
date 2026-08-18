@echo off
setlocal

cd /d "%~dp0"

echo Installing RP2040 Audio RGB dependencies...
py -m pip install --upgrade pip
if errorlevel 1 goto :error

py -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo.
echo Installation complete.
echo Run with: py led.py
pause
exit /b 0

:error
echo.
echo Installation failed.
echo Check that Python is installed and available through the Windows py launcher.
pause
exit /b 1
