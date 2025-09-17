# Setup environment script
Write-Host "Creating new virtual environment..."
python -m venv venv_new

Write-Host "Activating virtual environment..."
.\venv_new\Scripts\activate

Write-Host "Upgrading pip..."
python -m pip install --upgrade pip

Write-Host "Installing requirements..."
pip install -r backend/requirements.txt

Write-Host "Environment setup complete!"
Write-Host "To start the backend server, run:"
Write-Host "  .\venv_new\Scripts\python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload"
