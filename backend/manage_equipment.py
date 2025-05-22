from pymongo import MongoClient


def get_routers():
    try:
        client = MongoClient("mongodb://localhost:27017/")
        db = client["NetworkApp"]
        collection = db["Routers"]
        document = collection.find_one({}, {"_id": 0, "routers": 1})
        return document.get("routers", []) if document else []
    except Exception as e:
        print(f"MongoDB Error: {e}")
        return []

def add_router(router_data):
    try:
        client = MongoClient("mongodb://localhost:27017/")
        db = client["NetworkApp"]
        collection = db["Routers"]
        
        result = collection.update_one(
            {},
            {"$push": {"routers": router_data}},
            upsert=True
        )
        return result.modified_count > 0 or result.upserted_id is not None
    except Exception as e:
        print(f"MongoDB Error: {e}")
        return False

def delete_router(identifier):
    try:
        client = MongoClient("mongodb://localhost:27017/")
        db = client["NetworkApp"]
        collection = db["Routers"]
        
        result = collection.update_one(
            {},
            {"$pull": {"routers": {
                "$or": [
                    {"name": identifier},
                    {"ip": identifier}
                ]
            }}}
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"MongoDB Error: {e}")
        return False