@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo   RP2040 Audio RGB - Windows Setup
echo ============================================================
echo.

set "PYTHON_CMD="

rem Prefer supported, known-good Python versions instead of an arbitrary
rem `py` default. This avoids broken launcher targets such as C:\Python314.
for %%V in (3.13 3.12 3.11 3.10) do (
    py -%%V -c "import sys,venv; print(sys.executable)" >nul 2>&1
    if not errorlevel 1 if not defined PYTHON_CMD set "PYTHON_CMD=py -%%V"
)

rem Fall back to python.exe from PATH only when it is Python 3.10-3.13 and
rem its standard library / venv module are healthy.
if not defined PYTHON_CMD (
    python -c "import sys,venv; raise SystemExit(0 if (3,10) <= sys.version_info[:2] < (3,14) else 1)" >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD goto :no_python

echo Using: %PYTHON_CMD%
%PYTHON_CMD% -c "import sys; print('Python:', sys.version); print('Executable:', sys.executable)"
if errorlevel 1 goto :no_python

echo.
echo [1/4] Creating isolated virtual environment...
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import sys; raise SystemExit(0 if (3,10) <= sys.version_info[:2] < (3,14) else 1)" >nul 2>&1
    if errorlevel 1 (
        echo Existing .venv is invalid or unsupported. Recreating it...
        rmdir /s /q ".venv"
    )
)

if not exist ".venv\Scripts\python.exe" (
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 goto :venv_failed
)

set "VPY=.venv\Scripts\python.exe"

echo [2/4] Ensuring pip is available...
"%VPY%" -m ensurepip --upgrade >nul 2>&1
"%VPY%" -m pip --version
if errorlevel 1 goto :pip_failed

echo [3/4] Updating packaging tools...
"%VPY%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :pip_failed

echo [4/4] Installing application dependencies...
"%VPY%" -m pip install -r requirements.txt
if errorlevel 1 goto :install_failed

echo.
echo ============================================================
echo   Installation complete.
echo ============================================================
echo Virtual environment: %CD%\.venv
echo Run run.bat to launch RP2040 Audio RGB.
echo.
pause
exit /b 0

:no_python
echo.
echo ERROR: No healthy Python 3.10-3.13 installation was found.
echo.
echo Your current Windows Python launcher points to a broken/unsupported
 echo Python 3.14 installation. Install a clean Python 3.13, then rerun setup.
echo.
echo Recommended command:
echo   winget install -e --id Python.Python.3.13
echo.
echo After installation, close this CMD window, open a new one and run:
echo   cd /d %CD%
echo   setup.bat
echo.
pause
exit /b 2

:venv_failed
echo.
echo ERROR: Python was found, but creating .venv failed.
echo Run doctor.bat and send its output.
pause
exit /b 3

:pip_failed
echo.
echo ERROR: pip could not be initialized inside .venv.
echo Run doctor.bat and send its output.
pause
exit /b 4

:install_failed
echo.
echo ERROR: One or more Python dependencies failed to install.
echo Run doctor.bat and send its output.
pause
exit /b 5
