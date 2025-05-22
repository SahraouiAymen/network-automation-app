from backend.Connect import get_routers

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