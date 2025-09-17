import sys
import os
import numpy as np
from pymongo import MongoClient

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import the database module
from db import ProductsDb

def test_database_connection():
    print("Testing database connection...")
    try:
        db = ProductsDb()
        print("✅ Database connection successful!")
        
        # Test fetching documents with embeddings
        print("\nTesting fetch_all_with_embeddings()...")
        docs = db.fetch_all_with_embeddings()
        print(f"Found {len(docs)} documents with embeddings")
        
        if docs:
            print("\nSample document fields:")
            sample = docs[0]
            for key, value in sample.items():
                if key not in ['embedding', 'image_embedding']:
                    print(f"- {key}: {value}")
            
            # Check embedding fields
            if 'embedding' in sample:
                print(f"- embedding: array of length {len(sample['embedding'])}")
            if 'image_embedding' in sample:
                print(f"- image_embedding: array of length {len(sample['image_embedding'])}")
            
            # Test vector search with a sample embedding
            test_vector_search(db, sample)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_vector_search(db, sample_doc):
    print("\nTesting vector search...")
    
    # Get an embedding from the sample document
    embedding = None
    if 'image_embedding' in sample_doc and sample_doc['image_embedding']:
        embedding = sample_doc['image_embedding']
    elif 'embedding' in sample_doc and sample_doc['embedding']:
        embedding = sample_doc['embedding']
    
    if embedding:
        print(f"Using embedding of length {len(embedding)}")
        results = db.vector_search(embedding, top_k=3)
        print(f"Found {len(results)} similar items")
        for i, r in enumerate(results, 1):
            print(f"\nResult {i}:")
            print(f"- ID: {r.get('_id')}")
            print(f"- Name: {r.get('name')}")
            print(f"- Similarity: {r.get('similarity', 0):.4f}")
    else:
        print("No embedding found in sample document")

if __name__ == "__main__":
    test_database_connection()
