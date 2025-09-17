#!/usr/bin/env python3
"""
Test script for GCS image proxy functionality
"""

import os
import requests
from backend.gcs_service import GCSService
from backend.db import ProductsDb
from dotenv import load_dotenv
from pathlib import Path

# Load environment from backend/.env
load_dotenv(dotenv_path=Path(__file__).parent / 'backend' / '.env')

def test_gcs_service():
    """Test GCS service directly"""
    print("🧪 Testing GCS Service...")
    gcs = GCSService()
    
    if not gcs.bucket:
        print("❌ GCS service not initialized")
        return False
    
    print(f"✅ GCS service initialized with bucket: {gcs.bucket_name}")
    return True

def test_database_connection():
    """Test database and get sample image URLs"""
    print("\n🧪 Testing Database Connection...")
    db = ProductsDb()
    
    if db.collection is None:
        print("❌ Database not connected")
        return None
    
    print("✅ Database connected")
    
    # Find a document with an image URL
    doc = db.collection.find_one({"original_url": {"$exists": True, "$ne": ""}})
    if doc:
        print(f"✅ Found sample document:")
        print(f"   ID: {doc['_id']}")
        print(f"   URL: {doc['original_url']}")
        return doc['original_url']
    else:
        print("❌ No documents with image URLs found")
        return None

def test_gcs_direct_download(gcs_url):
    """Test direct GCS download"""
    print(f"\n🧪 Testing Direct GCS Download...")
    gcs = GCSService()
    
    if not gcs_url:
        print("❌ No GCS URL provided")
        return False
    
    # Test streaming the image
    image_data, content_type = gcs.stream_image(gcs_url)
    
    if image_data:
        print(f"✅ Successfully downloaded {len(image_data)} bytes")
        print(f"   Content type: {content_type}")
        return True
    else:
        print("❌ Failed to download image")
        return False

def test_proxy_endpoint(gcs_url):
    """Test the FastAPI proxy endpoint"""
    print(f"\n🧪 Testing Proxy Endpoint...")
    
    if not gcs_url or not gcs_url.startswith("gs://"):
        print("❌ Invalid GCS URL")
        return False
    
    # Extract filename from gs://bucket/path
    path_parts = gcs_url.split("/", 3)
    if len(path_parts) < 4:
        print("❌ Invalid GCS URL format")
        return False
    
    filename = path_parts[3]
    proxy_url = f"http://localhost:8000/images/{filename}"
    
    print(f"   GCS URL: {gcs_url}")
    print(f"   Proxy URL: {proxy_url}")
    
    try:
        response = requests.get(proxy_url, timeout=30)
        if response.status_code == 200:
            print(f"✅ Proxy endpoint working! Downloaded {len(response.content)} bytes")
            print(f"   Content-Type: {response.headers.get('Content-Type')}")
            return True
        else:
            print(f"❌ Proxy endpoint failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to FastAPI server. Make sure it's running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Proxy test failed: {e}")
        return False

def main():
    print("🚀 Starting GCS Image Proxy Tests\n")
    
    # Test 1: GCS Service
    gcs_ok = test_gcs_service()
    
    # Test 2: Database
    sample_url = test_database_connection()
    
    # Test 3: Direct GCS download
    direct_ok = False
    if gcs_ok and sample_url:
        direct_ok = test_gcs_direct_download(sample_url)
    
    # Test 4: Proxy endpoint
    proxy_ok = False
    if sample_url:
        proxy_ok = test_proxy_endpoint(sample_url)
    
    # Summary
    print(f"\n📊 Test Results:")
    print(f"   GCS Service: {'✅' if gcs_ok else '❌'}")
    print(f"   Database: {'✅' if sample_url else '❌'}")
    print(f"   Direct Download: {'✅' if direct_ok else '❌'}")
    print(f"   Proxy Endpoint: {'✅' if proxy_ok else '❌'}")
    
    if all([gcs_ok, sample_url, direct_ok, proxy_ok]):
        print("\n🎉 All tests passed! Your image proxy is working correctly.")
    else:
        print("\n❌ Some tests failed. Check the error messages above.")
        
        if not proxy_ok and direct_ok:
            print("\n💡 If direct download works but proxy fails:")
            print("   1. Make sure FastAPI server is running: uvicorn backend.app:app --reload")
            print("   2. Check that the /images/{filename:path} endpoint exists")

if __name__ == "__main__":
    main()
