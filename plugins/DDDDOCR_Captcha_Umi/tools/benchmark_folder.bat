@echo off
setlocal DisableDelayedExpansion
set "PLUGIN_DIR=%~dp0.."
for %%I in ("%PLUGIN_DIR%\..\..") do set "UMI_DATA=%%~fI"
set "UMI_PY=%UMI_DATA%\runtime\python.exe"
if not exist "%UMI_PY%" (
  echo [Error] Cannot find Umi-OCR Python:
  echo %UMI_PY%
  pause
  exit /b 2
)
set /p "IMG_DIR=Captcha folder: "
pushd "%UMI_DATA%"
"%UMI_PY%" "%~dp0benchmark_folder.py" "%IMG_DIR%" --output "%PLUGIN_DIR%\ddddocr_benchmark.tsv"
set "RC=%ERRORLEVEL%"
popd
if "%RC%"=="0" echo Result: %PLUGIN_DIR%\ddddocr_benchmark.tsv
pause
exit /b %RC%
