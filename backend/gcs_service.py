import os
import io
import time
from typing import Optional, Dict, Tuple
from google.cloud import storage
from dotenv import load_dotenv
from functools import lru_cache
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).with_name('.env'))

class GCSService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GCSService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
        
    def _initialize(self):
        self.bucket_name = os.getenv('GCS_BUCKET_NAME')
        self.client = None
        self.bucket = None
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour
        self.cache_size_mb = 100
        
        if not self.bucket_name:
            print("❌ GCS_BUCKET_NAME missing in .env file")
            return
            
        try:
            # Use default credentials only - no service account files
            self.client = storage.Client()
            self.bucket = self.client.bucket(self.bucket_name)
            print(f"✅ Initialized GCS client with bucket: {self.bucket_name}")
            
        except Exception as e:
            print(f"❌ Failed to initialize GCS client: {e}")
            print("💡 To authenticate:")
            print("   1. Install gcloud CLI: https://cloud.google.com/sdk/docs/install")
            print("   2. Run: gcloud auth application-default login")
            print("   3. Or run on Google Cloud with default service account")
    
    def stream_image(self, gcs_path: str) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Stream an image from GCS to memory.
        Returns a tuple of (image_bytes, content_type) or (None, None) on error.
        """
        if not self.bucket:
            print("❌ GCS client not initialized")
            return None, None
            
        # Check cache first
        current_time = time.time()
        if gcs_path in self.cache:
            data, timestamp = self.cache[gcs_path]
            if current_time - timestamp < self.cache_ttl:
                print(f"✅ Cache hit for {gcs_path}")
                return data, self.get_content_type(gcs_path)
            else:
                # Remove expired item
                del self.cache[gcs_path]
            
        try:
            # Handle gs:// URLs by extracting the path
            if gcs_path.startswith("gs://"):
                # Extract path after bucket name
                parts = gcs_path.replace("gs://", "").split("/", 1)
                if len(parts) > 1:
                    gcs_path = parts[1]
                else:
                    print(f"❌ Invalid GCS path format: {gcs_path}")
                    return None, None
            
            # Remove leading slash if present
            gcs_path = gcs_path.lstrip('/')
            blob = self.bucket.blob(gcs_path)
            
            if not blob.exists():
                print(f"❌ File not found in GCS: {gcs_path}")
                return None, None
                
            # Download to memory
            image_bytes = blob.download_as_bytes()
            
            # Cache the result
            self.cache[gcs_path] = (image_bytes, current_time)
            self._clean_cache()
            
            # Get content type
            content_type = self.get_content_type(gcs_path)
            
            print(f"✅ Downloaded image from GCS: {gcs_path} ({len(image_bytes)} bytes)")
            return image_bytes, content_type
            
        except Exception as e:
            print(f"❌ Error streaming {gcs_path}: {e}")
            return None, None
    
    def get_content_type(self, filename: str) -> str:
        """Get content type based on file extension"""
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        content_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'svg': 'image/svg+xml',
            'bmp': 'image/bmp',
            'tiff': 'image/tiff',
            'ico': 'image/x-icon'
        }
        return content_types.get(ext, 'image/jpeg')
    
    def _clean_cache(self):
        """Remove expired items and enforce size limit"""
        current_time = time.time()
        
        # Remove expired items
        expired_keys = [
            key for key, (data, timestamp) in self.cache.items()
            if current_time - timestamp > self.cache_ttl
        ]
        for key in expired_keys:
            del self.cache[key]
        
        # Enforce size limit (rough estimate)
        total_size_mb = sum(len(data) for data, _ in self.cache.values()) / (1024 * 1024)
        if total_size_mb > self.cache_size_mb:
            # Remove oldest items
            sorted_items = sorted(self.cache.items(), key=lambda x: x[1][1])
            while total_size_mb > self.cache_size_mb * 0.8 and sorted_items:
                key_to_remove = sorted_items.pop(0)[0]
                data_size = len(self.cache[key_to_remove][0]) / (1024 * 1024)
                del self.cache[key_to_remove]
                total_size_mb -= data_size
