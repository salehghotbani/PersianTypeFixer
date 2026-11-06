@echo off
setlocal
cd /d "%~dp0"
set "BOOTSTRAP_PYTHON=python"
if exist ".venv\Scripts\python.exe" set "BOOTSTRAP_PYTHON=.venv\Scripts\python.exe"
set "APP_PYTHON=build\.venv\Scripts\python.exe"
set "PIP_CONFIG_FILE=nul"
set "PIP_EXTRA_INDEX_URL="
set "PIP_INDEX_URL=https://pypi.org/simple"
set "PIP_DISABLE_PIP_VERSION_CHECK=1"

if not exist "%APP_PYTHON%" "%BOOTSTRAP_PYTHON%" -m venv build\.venv
if errorlevel 1 exit /b 1
"%APP_PYTHON%" -m pip install -r requirements-build.txt
if errorlevel 1 exit /b 1
"%APP_PYTHON%" -m unittest discover -s tests -v
if errorlevel 1 exit /b 1
"%APP_PYTHON%" tools\prepare_release.py
if errorlevel 1 exit /b 1
"%APP_PYTHON%" -m PyInstaller --noconfirm --clean PersianTypoFixer.spec
if errorlevel 1 exit /b 1
"%APP_PYTHON%" tools\build_installer.py
if errorlevel 1 exit /b 1
"%APP_PYTHON%" tools\package_release.py
if errorlevel 1 exit /b 1

echo.
echo Build completed.
echo Release files:
echo dist\release\

endlocal
