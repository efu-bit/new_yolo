# Fix Python Environment Script
Write-Host "=== Python Environment Diagnostic ===" -ForegroundColor Cyan

# Check Python installation
Write-Host "`n[1/4] Checking Python installation..." -ForegroundColor Yellow
$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source

if ($pythonPath) {
    Write-Host "✅ Python found at: $pythonPath" -ForegroundColor Green
    $pythonVersion = python --version 2>&1
    Write-Host "   $pythonVersion"
} else {
    Write-Host "❌ Python not found in PATH" -ForegroundColor Red
    Write-Host "   Please ensure Python is installed and added to your system PATH"
    exit 1
}

# Check virtual environment
Write-Host "`n[2/4] Checking virtual environment..." -ForegroundColor Yellow
$venvPath = ".venv"

if (Test-Path $venvPath) {
    Write-Host "✅ Virtual environment found at: $venvPath" -ForegroundColor Green
    
    # Activate the virtual environment
    $activateScript = ".\$venvPath\Scripts\Activate.ps1"
    if (Test-Path $activateScript) {
        try {
            . $activateScript
            Write-Host "✅ Virtual environment activated successfully" -ForegroundColor Green
        } catch {
            Write-Host "❌ Failed to activate virtual environment: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "❌ Could not find activation script at: $activateScript" -ForegroundColor Red
    }
} else {
    Write-Host "❌ Virtual environment not found at: $venvPath" -ForegroundColor Red
    Write-Host "   Creating a new virtual environment..."
    python -m venv $venvPath
    if ($?) {
        Write-Host "✅ Virtual environment created successfully" -ForegroundColor Green
        . ".\$venvPath\Scripts\Activate.ps1"
    } else {
        Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
}

# Check required packages
Write-Host "`n[3/4] Checking required packages..." -ForegroundColor Yellow
$requiredPackages = @("fastapi", "uvicorn", "python-dotenv", "pymongo", "numpy", "pillow", "torch", "transformers")

foreach ($pkg in $requiredPackages) {
    $installed = python -c "import $pkg" 2>&1
    if ($?) {
        $version = python -c "import $pkg; print($pkg.__version__ if hasattr($pkg, '__version__') else 'unknown version')" 2>&1
        Write-Host "✅ $pkg is installed ($version)" -ForegroundColor Green
    } else {
        Write-Host "❌ $pkg is not installed" -ForegroundColor Red
        Write-Host "   Installing $pkg..."
        pip install $pkg
        if (-not $?) {
            Write-Host "   ❌ Failed to install $pkg" -ForegroundColor Red
        }
    }
}

# Check environment variables
Write-Host "`n[4/4] Checking environment variables..." -ForegroundColor Yellow
$requiredVars = @("SAM2_CONFIG", "SAM2_CHECKPOINT")
$allSet = $true

foreach ($var in $requiredVars) {
    $value = [System.Environment]::GetEnvironmentVariable($var)
    if ($value) {
        Write-Host "✅ $var is set" -ForegroundColor Green
    } else {
        Write-Host "❌ $var is not set" -ForegroundColor Red
        $allSet = $false
    }
}

if (-not $allSet) {
    Write-Host "`n⚠️  Some required environment variables are not set" -ForegroundColor Yellow
    Write-Host "   Please set the following environment variables:"
    foreach ($var in $requiredVars) {
        if (-not [System.Environment]::GetEnvironmentVariable($var)) {
            Write-Host "   - $var"
        }
    }
}

# Try to start the server if everything looks good
if ($allSet) {
    Write-Host "`n🚀 Attempting to start the backend server..." -ForegroundColor Cyan
    $env:SAM2_CONFIG = [System.Environment]::GetEnvironmentVariable("SAM2_CONFIG")
    $env:SAM2_CHECKPOINT = [System.Environment]::GetEnvironmentVariable("SAM2_CHECKPOINT")
    
    try {
        python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
    } catch {
        Write-Host "❌ Failed to start server: $_" -ForegroundColor Red
    }
} else {
    Write-Host "`n❌ Please fix the issues above before starting the server" -ForegroundColor Red
}
