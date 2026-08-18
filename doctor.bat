@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo   RP2040 Audio RGB - Diagnostics
echo ============================================================
echo.
echo [where py]
where py 2>&1
echo.
echo [where python]
where python 2>&1
echo.
echo [Python launcher installations]
py -0p 2>&1
echo.
echo [Default py]
py -c "import sys; print(sys.version); print(sys.executable); print(sys.prefix)" 2>&1
echo.
echo [Default py pip]
py -m pip --version 2>&1
echo.
echo [PATH python]
python -c "import sys; print(sys.version); print(sys.executable); print(sys.prefix)" 2>&1
echo.
echo [PATH python pip]
python -m pip --version 2>&1
echo.

for %%V in (3.13 3.12 3.11 3.10) do (
    echo [py -%%V]
    py -%%V -c "import sys,venv; print(sys.version); print(sys.executable); print('venv OK')" 2>&1
    echo.
)

if exist ".venv\Scripts\python.exe" (
    echo [.venv]
    ".venv\Scripts\python.exe" -c "import sys; print(sys.version); print(sys.executable)" 2>&1
    ".venv\Scripts\python.exe" -m pip --version 2>&1
) else (
    echo [.venv]
    echo Not created.
)

echo.
echo ============================================================
pause
