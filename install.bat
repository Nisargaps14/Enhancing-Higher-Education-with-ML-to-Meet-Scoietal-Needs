@echo off
setlocal EnableDelayedExpansion

:: -------------------------------
:: 1. Check for Python 3.9
:: -------------------------------
echo Checking for Python 3.9...
python --version > temp_py_ver.txt 2>nul
findstr /C:"Python 3.9" temp_py_ver.txt >nul
if %ERRORLEVEL% NEQ 0 (
    echo Python 3.9 not found. Installing...
    powershell -Command "Start-BitsTransfer -Source https://www.python.org/ftp/python/3.9.13/python-3.9.13-amd64.exe -Destination python39_installer.exe"
    python39_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    del python39_installer.exe
    echo Python 3.9 installed.
) else (
    echo Python 3.9 found.
)
del temp_py_ver.txt >nul 2>nul

:: -------------------------------
:: 2. Create virtual environment if not exists
:: -------------------------------
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo Installing requirements...
    venv\Scripts\pip install -r requirements.txt
) else (
    echo Virtual environment already exists.
)

:: -------------------------------
:: 3. Run train_model.py
:: -------------------------------
echo Running training script...
venv\Scripts\python train_model.py

echo Done.
pause
