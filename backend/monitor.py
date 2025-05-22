
from backend.Connect import get_routers
from pymongo import MongoClient

CLIENT = MongoClient("mongodb://localhost:27017/")
DB = CLIENT["NetworkApp"]

def fetch_full_logs():
    """Retrieve all logs with ObjectIds"""
    try:
        return list(DB.Logs.find().sort("timestamp", -1))
    except Exception as e:
        print(f"Database error: {e}")
        return []

def validate_admin(password):
    return password == "admin123"  # Set your password here
def fetch_routers():
    """Get all routers from database"""
    try:
        return get_routers()
    except Exception as e:
        print(f"Database error: {e}")
        return []

def validate_router_credentials(router_data):
    """Validate router credentials structure"""
    required_keys = ['name', 'ip', 'username', 'password']
    return all(key in router_data for key in required_keys)

def handle_logout_request():
    """Perform any backend cleanup before logout"""
    print("Performing backend logout cleanup")
    return True

