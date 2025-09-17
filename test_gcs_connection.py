import os
from backend.gcs_service import GCSService
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from backend/.env
load_dotenv(dotenv_path=Path(__file__).parent / 'backend' / '.env')

def test_gcs_connection():
    print("🔍 Testing GCS connection...")
    
    # Initialize GCS service
    gcs = GCSService()
    
    if not gcs.bucket:
        print("❌ GCS not initialized. Please check your .env file and ensure GCS_BUCKET_NAME is set.")
        return
    
    # Test with one of your actual image paths
    test_paths = [
        "oguzhan/ikea_filtered_prompt_updated/0000d477506fdfc3ec19f83a927ff2b2.jpg",
        "oguzhan/ikea_filtered_prompt_updated/"  # Test directory listing
    ]
    
    for path in test_paths:
        print(f"\nTesting path: {path}")
        try:
            # Try to access the object
            if path.endswith('/'):
                # List objects in the directory
                blobs = list(gcs.bucket.list_blobs(prefix=path, max_results=5))
                print(f"✅ Found {len(blobs)} objects in directory")
                for blob in blobs[:3]:  # Show first 3 items
                    print(f" - {blob.name} ({blob.size} bytes)")
                if len(blobs) > 3:
                    print(f" - ... and {len(blobs)-3} more")
            else:
                # Try to download a file
                blob = gcs.bucket.blob(path)
                if blob.exists():
                    size = blob.size
                    print(f"✅ File exists! Size: {size} bytes")
                else:
                    print(f"❌ File does not exist: {path}")
        except Exception as e:
            print(f"❌ Error accessing {path}: {str(e)}")

if __name__ == "__main__":
    test_gcs_connection()
