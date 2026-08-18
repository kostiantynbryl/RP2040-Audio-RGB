@echo off
setlocal
py -m pip install -r requirements.txt
py -m PyInstaller --noconfirm --clean RP2040AudioRGB.spec
if errorlevel 1 exit /b 1
powershell -NoProfile -Command "Compress-Archive -Force -Path dist\RP2040AudioRGB\* -DestinationPath dist\RP2040AudioRGB-portable.zip"
echo.
echo Portable build: dist\RP2040AudioRGB\RP2040AudioRGB.exe
echo Archive: dist\RP2040AudioRGB-portable.zip
