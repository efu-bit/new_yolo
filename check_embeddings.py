import os
from pymongo import MongoClient

def check_database():
    # Get MongoDB connection details from environment or use defaults
    uri = os.getenv("MONGODB_URI", "mongodb+srv://efsun:efsun@cluster0.st3vdm4.mongodb.net/")
    db_name = os.getenv("MONGODB_DB", "TattoMongoReady_queries")
    collection_name = os.getenv("MONGODB_COLLECTION", "TattoMongoReady_queries")
    
    print(f"Connecting to MongoDB at {uri}")
    print(f"Database: {db_name}, Collection: {collection_name}")
    
    try:
        client = MongoClient(uri)
        db = client[db_name]
        collection = db[collection_name]
        
        # Check if collection exists
        if collection_name not in db.list_collection_names():
            print(f"Error: Collection '{collection_name}' does not exist in database '{db_name}'")
            return
        
        # Count total documents
        total_docs = collection.count_documents({})
        print(f"Total documents in collection: {total_docs}")
        
        # Count documents with embeddings
        with_embeddings = collection.count_documents({
            "$or": [
                {"image_embedding": {"$exists": True, "$ne": []}},
                {"embedding": {"$exists": True, "$ne": []}}
            ]
        })
        print(f"Documents with embeddings: {with_embeddings}")
        
        # Get sample document with embedding
        sample = collection.find_one({
            "$or": [
                {"image_embedding": {"$exists": True, "$ne": []}},
                {"embedding": {"$exists": True, "$ne": []}}
            ]
        })
        
        if sample:
            print("\nSample document with embedding:")
            print(f"ID: {sample.get('_id')}")
            
            # Check which embedding field exists and its length
            if 'image_embedding' in sample:
                print(f"Found 'image_embedding' field with length: {len(sample['image_embedding']) if sample['image_embedding'] else 0}")
            if 'embedding' in sample:
                print(f"Found 'embedding' field with length: {len(sample['embedding']) if sample['embedding'] else 0}")
            
            # Print available fields
            print("\nAvailable fields in document:")
            for key in sample.keys():
                if key not in ['image_embedding', 'embedding']:
                    print(f"- {key}: {sample[key] if not isinstance(sample[key], (list, dict)) else type(sample[key])}")
        else:
            print("No documents with embeddings found in the collection.")
            
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")

if __name__ == "__main__":
    check_database()
