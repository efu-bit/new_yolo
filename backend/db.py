import os
import time
from typing import List, Dict, Any
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv(dotenv_path=Path(__file__).with_name('.env'))

class ProductsDb:
    def __init__(self):
        # Use the connection string from environment or default
        uri = os.getenv("MONGODB_URI")
        db_name = os.getenv("MONGODB_DB", "furniture")
        collection_name = os.getenv("MONGODB_COLLECTION", "furniture")

        self.collection = None

        if not uri:
            # Start with DB disabled if URI missing
            print("⚠️ MongoDB disabled: set MONGODB_URI in .env to enable search")
            return

        try:
            # Connect with a short timeout to fail fast if there are issues
            client = MongoClient(uri, serverSelectionTimeoutMS=10000)

            # Test the connection
            client.admin.command('ping')
            print("✅ Successfully connected to MongoDB")

            self.collection = client[db_name][collection_name]
            print(f"✅ Using collection: {db_name}.{collection_name}")

        except Exception as e:
            print(f"❌ Failed to connect to MongoDB (check URI, DB/collection, network, and URL-encoding for special characters in password): {e}")
            print("⚠️ MongoDB disabled: backend will start without DB. Set a valid MONGODB_URI to enable search.")
            self.collection = None

    def vector_search(self, query_vector: List[float], top_k: int = 12) -> List[Dict[str, Any]]:
        """
        Perform vector search using MongoDB's vector search with dot product similarity.
        """
        if self.collection is None:
            print("ℹ️ MongoDB disabled: returning empty search results")
            return []

        try:
            start_time = time.time()

            pipeline = [
                {
                    "$vectorSearch": {
                        "index": "vdot768",  # Using dot product index as specified
                        "path": "image_embedding",
                        "queryVector": query_vector,
                        "numCandidates": 100,  # Number of candidates to consider
                        "limit": top_k,
                        "similarity": "dotProduct"  # Use dot product similarity
                    }
                },
                {
                    "$project": {
                        "_id": 1,
                        "name": 1,
                        "price": 1,
                        "brand": 1,
                        "rating": 1,
                        "imageUrl": 1,
                        "original_url": 1,  # Include original_url in the projection
                        "inStock": 1,
                        "similarity": {"$meta": "vectorSearchScore"}
                    }
                }
            ]

            results = list(self.collection.aggregate(pipeline))
            search_time = time.time() - start_time

            print(f"✅ Found {len(results)} results in {search_time:.2f}s using dot product search")
            return results

        except Exception as e:
            print(f"❌ Vector search failed: {e}")
            return []
    
    def fetch_all_with_embeddings(self) -> List[Dict[str, Any]]:
        """Fetch all documents with embeddings for fallback search"""
        if self.collection is None:
            return []
        return list(self.collection.find({
            "image_embedding": {"$exists": True, "$ne": []}
        }))