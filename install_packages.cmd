@echo off
setlocal enabledelayedexpansion

echo Creating virtual environment...
python -m venv .venv
call .venv\Scripts\activate.bat

:: Set pip to use a shorter path for cache
set PIP_CACHE_DIR=%TEMP%\pip-cache

:: Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

:: Install packages one by one with retry logic
for %%p in (
    "fastapi==0.114.2"
    "uvicorn[standard]==0.30.6"
    "pillow==10.4.0"
    "numpy==1.24.4"
    "torch==2.3.1 --index-url https://download.pytorch.org/whl/cpu"
    "transformers==4.43.4"
    "timm==1.0.9"
    "opencv-python-headless==4.10.0.84"
    "pymongo==4.8.0"
    "python-dotenv==1.0.1"
    "accelerate==0.33.0"
    "safetensors==0.4.4"
    "pydantic==2.8.2"
    "python-multipart==0.0.9"
    "requests==2.32.3"
    "tqdm==4.66.5"
) do (
    set pkg=%%~p
    set retry=0
    :retry_install
    echo Installing !pkg!...
    pip install !pkg! --no-cache-dir
    if !errorlevel! neq 0 (
        set /a retry+=1
        if !retry! le 3 (
            echo Retrying installation of !pkg! (attempt !retry! of 3)...
            timeout /t 5 >nul
            goto :retry_install
        ) else (
            echo Failed to install !pkg! after 3 attempts.
            pause
            exit /b 1
        )
    )
)

echo All packages installed successfully!
pause
