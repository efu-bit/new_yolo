#!/usr/bin/env python3
import os
import sys
import subprocess

# Set environment variables
os.environ["SAM2_CONFIG"] = "backend/sam2/configs/sam2.1/sam2.1_hiera_t.yaml"
os.environ["SAM2_CHECKPOINT"] = "backend/sam2/checkpoints/sam2.1_hiera_tiny.pt"

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

try:
    # Import and run the FastAPI app directly
    import uvicorn
    from backend.app import app
    
    print("✅ Starting Decor Detective Backend Server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📖 API docs will be available at: http://localhost:8000/docs")
    print("🔄 Press Ctrl+C to stop the server")
    
    # Start the server
    uvicorn.run(
        "backend.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt"])
    print("✅ Packages installed. Please run this script again.")
    
except Exception as e:
    print(f"❌ Error starting server: {e}")
    import traceback
    traceback.print_exc()
