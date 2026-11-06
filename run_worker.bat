@echo off
rem Second-PC worker: see WORKER.md.  Double-click to run, or give a case list:
rem     run_worker.bat cases\golden.json
setlocal
cd /d "%~dp0"
set CASES=%~1
if "%CASES%"=="" set CASES=cases\golden.json

if not exist .venv\Scripts\python.exe (
    echo Setting up, once only...
    py -3.14 -m venv .venv
    if errorlevel 1 goto nopython
    .venv\Scripts\python -m pip install -r requirements.lock
    if errorlevel 1 goto noinstall
)

.venv\Scripts\python tools\worker.py %CASES% --out worker_out
if errorlevel 1 goto failed
echo.
echo Finished. Copy the worker_out folder back to the main PC.
pause
exit /b 0

:nopython
echo Python 3.14 wasn't found. Install it from python.org (see WORKER.md), then run this again.
pause
exit /b 1

:noinstall
echo Installing the packages failed. Check the internet connection and run this again.
rmdir /s /q .venv
pause
exit /b 1

:failed
echo The worker stopped. Send the messages above to the maintainer's main PC session.
pause
exit /b 1
