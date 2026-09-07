@echo off
setlocal DisableDelayedExpansion
set "PY=%~dp0..\..\..\runtime\python.exe"
if not exist "%PY%" (
  echo [FAIL] Put the plugin folder inside UmiOCR-data\plugins first.
  pause
  exit /b 2
)
"%PY%" "%~dp0setup.py" --action models --tier tiny %*
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" echo [FAIL] Exit code %RC%. Read the message above.
pause
exit /b %RC%
