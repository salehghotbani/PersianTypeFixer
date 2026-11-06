@echo off
setlocal
cd /d "%~dp0"
set "APP_PYTHON=python"
if exist ".venv\Scripts\python.exe" set "APP_PYTHON=.venv\Scripts\python.exe"

"%APP_PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
"%APP_PYTHON%" -m pip install "pyinstaller>=6.0,<7"
if errorlevel 1 exit /b 1
"%APP_PYTHON%" -m unittest discover -s tests -v
if errorlevel 1 exit /b 1
"%APP_PYTHON%" -m PyInstaller --noconfirm --clean PersianTypoFixer.spec
if errorlevel 1 exit /b 1

echo.
echo Build completed.
echo Executable:
echo dist\PersianTypoFixer\PersianTypoFixer.exe

endlocal
