@echo off
echo Installing required packages...

call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo Failed to activate virtual environment
    pause
    exit /b 1
)

echo Installing packages from requirements.txt...
pip install --upgrade pip
pip install -r backend\requirements.txt

if errorlevel 1 (
    echo Failed to install packages
    pause
    exit /b 1
)

echo All packages installed successfully!
pause
