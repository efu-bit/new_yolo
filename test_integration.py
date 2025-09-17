from backend.gcs_service import GCSService
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment from backend/.env
load_dotenv(dotenv_path=Path(__file__).parent / 'backend' / '.env')

def test_gcs():
    print("\n--- Testing GCS Connection ---")
    gcs = GCSService()
    
    if not gcs.bucket:
        print("❌ GCS client not initialized. Check your .env file")
        print(f"GCS_BUCKET_NAME: {os.getenv('GCS_BUCKET_NAME')}")
        print(f"GOOGLE_APPLICATION_CREDENTIALS: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")
        return False
        
    print(f"✅ Connected to GCS bucket: {gcs.bucket_name}")
    
    # Test with a sample path from your data
    test_path = 'oguzhan/ikea_filtered_prompt_updated/0000d4775'
    print(f"\n--- Testing download: {test_path} ---")
    
    data = gcs.download_image_to_memory(test_path)
    if data:
        print(f"✅ Downloaded {len(data)} bytes")
        return True
    else:
        print("❌ Failed to download file")
        return False

def test_mongodb():
    print("\n--- Testing MongoDB Connection ---")
    try:
        client = MongoClient(os.getenv('MONGODB_URI'), serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        db = client[os.getenv('MONGODB_DB', 'furniture')]
        collection = db[os.getenv('MONGODB_COLLECTION', 'furniture')]
        print("✅ Connected to MongoDB")
        
        # Find a document with an image URL
        doc = collection.find_one({'original_url': {'$exists': True, '$ne': ''}})
        if doc:
            print("\n📄 Found document with image:")
            print(f"ID: {doc['_id']}")
            print(f"URL: {doc['original_url']}")
            print(f"Has embedding: {'✅' if doc.get('image_embedding') else '❌'}")
            return True
        else:
            print("❌ No documents with image URLs found")
            return False
            
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting integration tests...")
    
    gcs_success = test_gcs()
    mongo_success = test_mongodb()
    
    print("\n📊 Test Results:")
    print(f"GCS: {'✅' if gcs_success else '❌'}")
    print(f"MongoDB: {'✅' if mongo_success else '❌'}")
    
    if gcs_success and mongo_success:
        print("\n🎉 All tests passed! You can now run the application.")
    else:
        print("\n❌ Some tests failed. Please check the error messages above.")
