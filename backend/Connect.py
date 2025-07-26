from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import bcrypt

def get_db_connection():
    """Establish a secure connection to MongoDB"""
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
        client.server_info()
        return client["NetworkApp"]
    except ConnectionFailure as e:
        print(f"Database connection failed: {e}")
        raise
    except Exception as e:
        print(f"Unexpected database error: {e}")
        raise

def get_user(username: str):
    """Retrieve user with password hash securely"""
    try:
        db = get_db_connection()
        return db.credentials.find_one(
            {"users.username": username},
            {"_id": 0, "users.$": 1}
        )
    except Exception as e:
        print(f"User retrieval error: {e}")
        return None

def verify_credentials(username: str, password: str) -> bool:
    """Securely verify credentials using bcrypt"""
    try:
        user_data = get_user(username)
        if not user_data or not user_data.get('users'):
            return False  # User not found
            
        stored_hash = user_data['users'][0]['password'].encode('utf-8')
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash)
    except Exception as e:
        print(f"Credential verification error: {e}")
        return False

def create_user(username: str, password: str) -> bool:
    """Create new user with hashed password"""
    try:
        if get_user(username):
            return False  # User exists

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        db = get_db_connection()
        result = db.credentials.update_one(
            {},
            {"$push": {"users": {
                "username": username,
                "password": hashed.decode('utf-8')
            }}},
            upsert=True
        )
        return result.acknowledged
    except Exception as e:
        print(f"User creation error: {e}")
        return False

def get_routers():
    """Retrieve network routers safely"""
    try:
        db = get_db_connection()
        routers = db.Routers.find_one({}, {"_id": 0, "routers": 1})
        return routers.get('routers', []) if routers else []
    except Exception as e:
        print(f"Router retrieval error: {e}")
        return []
def authenticate_user(username: str, password: str) -> bool:
    """Authentication interface layer"""
    try:
        return verify_credentials(username, password)
    except Exception as e:
        print(f"Authentication system error: {e}")
        return False