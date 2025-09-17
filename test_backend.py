import sys
import os

def test_imports():
    print("Testing imports...")
    try:
        from backend.embedding_service import EmbeddingService
        from backend.db import ProductsDb
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Python path:", sys.path)
        return False

def test_environment():
    print("\nTesting environment...")
    required_vars = ["SAM2_CONFIG", "SAM2_CHECKPOINT"]
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        print("Current environment variables:")
        for var in required_vars:
            print(f"  {var}: {os.getenv(var) or 'Not set'}")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

if __name__ == "__main__":
    print("Starting backend test...\n")
    imports_ok = test_imports()
    env_ok = test_environment()
    
    print("\nTest summary:")
    print(f"- Imports: {'✅' if imports_ok else '❌'}")
    print(f"- Environment: {'✅' if env_ok else '❌'}")
    
    if imports_ok and env_ok:
        print("\nTrying to start the FastAPI server...")
        try:
            from backend.app import app
            import uvicorn
            print("✅ Server imports successful")
            print("\nIf you see this, the server should start. Press Ctrl+C to stop.")
            uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)
        except Exception as e:
            print(f"❌ Error starting server: {e}")
    else:
        print("\n❌ Fix the issues above before starting the server")
