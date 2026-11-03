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
echo Drag the release folder containing ZIPs and SHA256SUMS.txt here.
set /p "RELEASE=Release folder: "
set "RELEASE=%RELEASE:"=%"
if not exist "%RELEASE%\" (
 echo [FAIL] Release folder not found.
 pause
 exit /b 2
)
pushd "%~dp0"
"%PY%" scripts\make_release.py --verify "%RELEASE%"
set "RC=%ERRORLEVEL%"
popd
pause
exit /b %RC%
