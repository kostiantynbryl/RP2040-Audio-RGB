@echo off
setlocal
echo Installing RP2040 Audio RGB...
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
if errorlevel 1 (
  echo Installation failed.
  pause
  exit /b 1
)
echo.
echo Installation complete.
echo Run run.bat to launch the application.
pause
