import os
import sys
import numpy as np
import requests
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from backend/.env
load_dotenv(dotenv_path=Path(__file__).parent / 'backend' / '.env')

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import the database module
from db import ProductsDb

def test_database_connection():
    print("Testing database connection...")
    try:
        db = ProductsDb()
        print("✅ Database connection successful!")
        return db
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return None

def test_vector_search(db, vector_size=768):
    print("\nTesting vector search...")
    try:
        # Create a random query vector of the specified size
        query_vector = np.random.rand(vector_size).astype(np.float32).tolist()
        
        print(f"Searching with {len(query_vector)}-dimensional vector...")
        results = db.vector_search(query_vector, top_k=5)
        
        if not results:
            print("⚠️  No results found. This could be normal if the database is empty.")
        else:
            print(f"✅ Found {len(results)} results:")
            for i, r in enumerate(results, 1):
                print(f"\n  {i}. ID: {r.get('_id')}")
                print(f"     Similarity: {r.get('similarity', 0):.4f}")
                print(f"     Name: {r.get('name', 'N/A')}")
                print(f"     Brand: {r.get('brand', 'N/A')}")
                print(f"     Price: {r.get('price', 'N/A')}")
                print(f"     Rating: {r.get('rating', 'N/A')}")
                print(f"     In Stock: {r.get('inStock', 'N/A')}")
                
                # Check image URL
                image_url = r.get('imageUrl')
                if image_url:
                    print(f"     Image URL: {image_url}")
                    try:
                        # Try to make a HEAD request to check if the image is accessible
                        response = requests.head(image_url, timeout=5)
                        if response.status_code == 200:
                            print("     ✅ Image URL is accessible")
                        else:
                            print(f"     ⚠️  Image URL returned status code: {response.status_code}")
                    except Exception as e:
                        print(f"     ❌ Failed to access image URL: {str(e)}")
                else:
                    print("     ❌ No image URL found")
        
        return results
    except Exception as e:
        print(f"❌ Vector search failed: {e}")
        return None

if __name__ == "__main__":
    # Load environment variables
    load_dotenv(dotenv_path=Path(__file__).parent / 'backend' / '.env')
    
    # Test database connection
    db = test_database_connection()
    
    if db:
        # Test vector search with a 768-dimensional vector
        test_vector_search(db, vector_size=768)
