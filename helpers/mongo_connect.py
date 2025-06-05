import os
from typing import List, Optional, Dict, Any, Union
from pymongo import MongoClient, UpdateOne
from pymongo.collection import Collection


# Singleton MongoDB client
_client: Optional[MongoClient] = None

def get_mongo_client() -> Union[MongoClient, str]:
    global _client
    if _client is None:
        uri = os.getenv("MONGO_URI")

        if not uri:
            return "MongoDB environment variables are not fully set."

        try:
            _client = MongoClient(
                host=uri,
                maxPoolSize=10,
                serverSelectionTimeoutMS=5000
            )
        except Exception as e:
            return f"Failed to connect to MongoDB: {str(e)}"
    return _client

def _get_collection(collection_name: str) -> Union[Collection, str]:
    db_name = os.getenv("MONGO_DB")
    if not db_name:
        return "MONGO_DB environment variable is not set."

    client = get_mongo_client()
    if isinstance(client, str):
        return client  # error message string

    return client[db_name][collection_name]

def serialize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    doc["_id"] = str(doc["_id"])
    return doc

def mongo_find_one(query: Dict[str, Any], collection_name: str) -> Union[Dict[str, Any], str]:
    collection = _get_collection(collection_name)
    if isinstance(collection, str):
        return collection  # error message

    try:
        cursor = collection.find_one(query)
        return serialize_doc(cursor)
    except Exception as e:
        return f"Error fetching data: {str(e)}"
    
def mongo_create_one(query: Dict[str, Any], collection_name: str) -> Union[str, str]:
    collection = _get_collection(collection_name)
    if isinstance(collection, str):
        return collection  # error message

    try:
        data = collection.insert_one(query)
        return data.inserted_id
    except Exception as e:
        return f"Error creating data: {str(e)}"
