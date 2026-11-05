@echo off

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

python -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --windowed ^
    --name PersianTypoFixer ^
    main.py

echo.
echo Build completed.
echo Executable:
echo dist\PersianTypoFixer\PersianTypoFixer.exe

pause