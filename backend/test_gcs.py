import os
from backend.gcs_service import GCSService
from backend.db import ProductsDb
from dotenv import load_dotenv
from pathlib import Path
import time

# Load environment variables from backend/.env explicitly (same folder as this file)
load_dotenv(dotenv_path=Path(__file__).with_name('.env'))

def test_gcs_connection():
    print("--- Testing GCS Connection ---")
    gcs = GCSService()
    
    if not gcs.bucket:
        print("❌ GCS client not initialized. Check your .env configuration.")
        return None
        
    print(f"✅ Connected to GCS bucket: {gcs.bucket_name}")
    return gcs

def test_image_download(gcs, gcs_path):
    print(f"\n--- Testing Image Download: {gcs_path} ---")
    
    # Test direct download
    start_time = time.time()
    image_bytes = gcs.download_image_to_memory(gcs_path)
    duration = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    if not image_bytes:
        print(f"❌ Failed to download image from {gcs_path}")
        return False
        
    print(f"✅ Downloaded {len(image_bytes):,} bytes in {duration:.2f}ms")
    
    # Test cache
    start_time = time.time()
    cached_bytes = gcs.download_image_to_memory(gcs_path)
    cache_duration = (time.time() - start_time) * 1000
    
    if cached_bytes and len(cached_bytes) == len(image_bytes):
        print(f"✅ Cache hit! Retrieved in {cache_duration:.2f}ms")
    else:
        print("❌ Cache test failed")
    
    return True

def test_db_connection():
    print("\n--- Testing MongoDB Connection ---")
    db = ProductsDb()
    
    if not db.collection:
        print("❌ MongoDB not connected. Check your MONGODB_URI in .env")
        return None
        
    print("✅ Connected to MongoDB")
    return db

def test_document_retrieval(db, sample_id=None):
    if not db or not db.collection:
        return
        
    print("\n--- Testing Document Retrieval ---")
    
    # Try to find a document with an image
    query = {"original_url": {"$exists": True, "$ne": ""}}
    if sample_id:
        query["_id"] = sample_id
    
    doc = db.collection.find_one(query)
    
    if not doc:
        print("❌ No documents with 'original_url' found in the database")
        return None
        
    print(f"✅ Found document with image: {doc.get('_id')}")
    print(f"   URL: {doc.get('original_url')}")
    print(f"   Has embedding: {'yes' if doc.get('image_embedding') else 'no'}")
    
    return doc

if __name__ == "__main__":
    # Test GCS connection
    gcs = test_gcs_connection()
    if not gcs:
        exit(1)
    
    # Test DB connection
    db = test_db_connection()
    
    # If DB is connected, try to find a document with an image
    doc = None
    if db:
        # You can pass a specific _id to test with: test_document_retrieval(db, ObjectId('your_id_here'))
        doc = test_document_retrieval(db)
    
    # Test with a specific image from the document if available
    if doc and 'original_url' in doc:
        # Extract the path from gs://bucket/path format
        gs_url = doc['original_url']
        if gs_url.startswith('gs://'):
            path_parts = gs_url[5:].split('/', 1)  # Remove 'gs://' and split
            if len(path_parts) > 1:
                bucket_name, object_path = path_parts
                if bucket_name == gcs.bucket_name:
                    test_image_download(gcs, object_path)
                else:
                    print(f"\n⚠️ Document bucket ({bucket_name}) doesn't match configured bucket ({gcs.bucket_name})")
                    print("Testing with document's path anyway...")
                    test_image_download(gcs, object_path)
    else:
        # Fallback to a test path if no document with URL found
        print("\n⚠️ No document with 'original_url' found. Using test path...")
        test_image_download(gcs, "oguzhan/ikea_filtered_prompt_updated/0000d4775...")  # Replace with your actual path
    
    print("\n✅ All tests completed")
