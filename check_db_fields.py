import os
from pprint import pprint
from dotenv import load_dotenv
from pathlib import Path
from pymongo import MongoClient

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent / 'backend' / '.env')

def check_database_fields():
    try:
        # Get MongoDB connection details
        uri = os.getenv("MONGODB_URI")
        db_name = os.getenv("MONGODB_DB", "TattoMongoReady_queries")
        collection_name = os.getenv("MONGODB_COLLECTION", "TattoMongoReady_queries")
        
        if not uri:
            print("❌ MONGODB_URI environment variable is not set")
            return
            
        # Connect to MongoDB
        client = MongoClient(uri)
        db = client[db_name]
        collection = db[collection_name]
        
        print(f"✅ Connected to MongoDB: {db_name}.{collection_name}")
        
        # Check total documents
        total_docs = collection.count_documents({})
        print(f"\n📊 Total documents: {total_docs}")
        
        # Check for any image URL fields in the first few documents
        print("\n🔍 Checking for image URL fields in documents...")
        
        # Get all possible field names in the collection
        sample_doc = collection.find_one()
        if not sample_doc:
            print("❌ No documents found in the collection")
            return
            
        print("\n📋 Document fields (first document):")
        for field, value in sample_doc.items():
            if field == '_id':
                continue
            field_type = type(value).__name__
            if isinstance(value, dict):
                field_type += f" (keys: {', '.join(list(value.keys())[:3])}{'...' if len(value) > 3 else ''})"
            print(f"- {field}: {field_type}")
        
        # Check for any field that might contain image URLs
        print("\n🔍 Checking for potential image URL fields...")
        potential_url_fields = set()
        for doc in collection.find().limit(100):
            for field, value in doc.items():
                if field.lower() in ['url', 'image', 'img', 'src', 'original_url', 'image_url']:
                    potential_url_fields.add(field)
                elif isinstance(value, str) and any(x in field.lower() for x in ['url', 'image', 'img', 'src']):
                    potential_url_fields.add(field)
        
        if potential_url_fields:
            print("\n🔍 Found potential URL fields:")
            for field in sorted(potential_url_fields):
                # Count non-empty values for this field
                count = collection.count_documents({
                    field: {"$exists": True, "$ne": None, "$ne": ""}
                })
                if count > 0:
                    print(f"- {field}: {count} documents")
        else:
            print("\n❌ No potential URL fields found in the first 100 documents")
        
        # Look specifically for image URLs in the first 5 documents
        print("\n🔍 Checking first 5 documents for image data:")
        for i, doc in enumerate(collection.find().limit(5)):
            print(f"\n📄 Document {i+1} (ID: {doc.get('_id')}):")
            
            # Check for any field that might contain image data
            image_data = {}
            for field, value in doc.items():
                field_lower = field.lower()
                if any(x in field_lower for x in ['url', 'image', 'img', 'src', 'pic', 'photo']):
                    if isinstance(value, str) and value.strip():
                        image_data[field] = value if len(str(value)) < 100 else f"[{type(value).__name__} length: {len(str(value))}]"
                    elif isinstance(value, dict):
                        image_data[field] = {k: f"[{type(v).__name__}]" for k, v in list(value.items())[:3]}
                        if len(value) > 3:
                            image_data[field]['...'] = f"... and {len(value) - 3} more"
                    elif value is not None:
                        image_data[field] = f"[{type(value).__name__}] {value}"
            
            if image_data:
                print("  Found image-related data:")
                for field, value in image_data.items():
                    print(f"  - {field}: {value}")
            else:
                print("  No image-related data found")
            
            # Print document structure
            print("\n  Document structure:")
            for field, value in doc.items():
                if field == '_id':
                    continue
                value_type = type(value).__name__
                if isinstance(value, dict):
                    value_type = f"dict with keys: {', '.join(list(value.keys())[:3])}"
                    if len(value) > 3:
                        value_type += "..."
                elif isinstance(value, (list, tuple)):
                    value_type = f"{value_type}[{len(value)}]"
                print(f"  - {field}: {value_type}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_database_fields()
