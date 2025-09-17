# Setup and Run Script for Decor Detective

# Stop on first error
$ErrorActionPreference = "Stop"

# Set environment variables
$env:SAM2_CONFIG = "$PWD\backend\sam2\configs\sam2.1\sam2.1_hiera_t.yaml"
$env:SAM2_CHECKPOINT = "$PWD\backend\sam2\checkpoints\sam2.1_hiera_tiny.pt"

# Create virtual environment if it doesn't exist
if (-not (Test-Path -Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..."
.venv\Scripts\Activate.ps1

# Install requirements
Write-Host "Installing requirements..."
python -m pip install --upgrade pip
pip install -r backend/requirements.txt

# Add current directory to Python path
$env:PYTHONPATH = "$PWD"

# Run the server
Write-Host "`n✅ Starting Decor Detective Backend Server..."
Write-Host "📍 Server will be available at: http://localhost:8000"
Write-Host "📖 API docs will be available at: http://localhost:8000/docs`n"

# Run the FastAPI app
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
