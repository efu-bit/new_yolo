@echo off
setlocal enabledelayedexpansion

echo [1/4] Setting up environment...
set PYTHONPATH=%~dp0
set SAM2_CONFIG=backend\sam2\configs\sam2.1\sam2.1_hiera_t.yaml
set SAM2_CHECKPOINT=backend\sam2\checkpoints\sam2.1_hiera_tiny.pt

echo [2/4] Activating virtual environment...
if exist "%~dp0.venv\Scripts\activate.bat" (
    call "%~dp0.venv\Scripts\activate.bat"
    if errorlevel 1 (
        echo Failed to activate virtual environment. Creating a new one...
        python -m venv .venv
        if errorlevel 1 (
            echo Failed to create virtual environment. Please check Python installation.
            pause
            exit /b 1
        )
        call "%~dp0.venv\Scripts\activate.bat"
        if errorlevel 1 (
            echo Failed to activate new virtual environment.
            pause
            exit /b 1
        )
        echo Installing required packages...
        pip install -r backend/requirements.txt
        if errorlevel 1 (
            echo Failed to install required packages.
            pause
            exit /b 1
        )
    )
)

echo [3/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not in PATH or not installed.
    pause
    exit /b 1
)

echo [4/4] Starting backend server...
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload

if errorlevel 1 (
    echo Failed to start server.
    pause
    exit /b 1
)
