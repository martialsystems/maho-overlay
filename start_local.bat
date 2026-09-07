@echo off
setlocal EnableExtensions DisableDelayedExpansion

cd /d "%~dp0"

set "VENV_PYTHON=%CD%\backend\.venv\Scripts\python.exe"

if not exist "%VENV_PYTHON%" (
    echo ERROR: backend\.venv was not found.
    echo Create it once:
    echo.
    echo   py -3.12 -m venv backend\.venv
    echo   backend\.venv\Scripts\python -m pip install -r backend\requirements-no-ai.txt
    echo.
    pause
    exit /b 1
)

"%VENV_PYTHON%" "%CD%\scripts\launcher.py" --no-ai

set "EXIT_CODE=%errorlevel%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo Maho Overlay launcher exited with an error.
    echo Check .runtime\logs for service logs.
    pause
)

exit /b %EXIT_CODE%
