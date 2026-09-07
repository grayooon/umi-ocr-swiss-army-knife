@echo off
setlocal DisableDelayedExpansion
echo Drag UmiOCR-data\runtime\python.exe here, then press Enter.
set /p "PY=Python path: "
set "PY=%PY:"=%"
if not exist "%PY%" (
 echo [FAIL] Python not found.
 pause
 exit /b 2
)
pushd "%~dp0"
"%PY%" -m unittest discover -s tests -v
set "RC=%ERRORLEVEL%"
popd
pause
exit /b %RC%
