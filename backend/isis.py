from pymongo import MongoClient
import paramiko
import time
import socket
import datetime
import re

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "NetworkApp"

def load_routers():
    try:
        with MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000) as client:
            db = client[DB_NAME]
            routers = db["Routers"].find_one({}, {"routers": 1})
            return routers["routers"] if routers and "routers" in routers else []
    except Exception as e:
        print(f"MongoDB Error: {e}")
        return []

def validate_net(net):
    """Validate NET format (49.xxxx.xxxx.xxxx.xxxx.xx)"""
    pattern = r"^49\.([0-9A-Fa-f]{4}\.){4}[0-9A-Fa-f]{2}$"
    return re.match(pattern, net) is not None

def validate_area(area):
    """Validate Area ID format (49.xxxx)"""
    pattern = r"^49\.\d{4}$"
    return re.match(pattern, area) is not None

def get_router_details(router_name):
    try:
        with MongoClient(MONGO_URI) as client:
            db = client[DB_NAME]
            router = db["Routers"].find_one(
                {"routers.name": router_name},
                {"_id": 0, "routers.$": 1}
            )
            return router["routers"][0] if router and "routers" in router else None
    except Exception as e:
        print(f"Database Error: {e}")
        return None

def log_operation(router_ip, user_ip, commands, output, status):
    try:
        with MongoClient(MONGO_URI) as client:
            db = client[DB_NAME]
            log_entry = {
                "router_ip": router_ip,
                "user_ip": user_ip,
                "commands": commands,
                "output": output,
                "status": status,
                "timestamp": datetime.datetime.utcnow()
            }
            db.Logs.insert_one(log_entry)
    except Exception as e:
        print(f"Logging Error: {e}")

def execute_ssh_commands(router, commands):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    output = ""
    
    try:
        ssh_client.connect(
            hostname=router["ip"],
            username=router["username"],
            password=router["password"],
            look_for_keys=False,
            allow_agent=False,
            timeout=10
        )
        
        shell = ssh_client.invoke_shell()
        shell.settimeout(15)
        
        time.sleep(1)
        while shell.recv_ready():
            shell.recv(1024)
        
        for cmd in commands:
            shell.send(cmd + '\n')
            time.sleep(1)
            while not shell.recv_ready():
                time.sleep(0.5)
            part = shell.recv(4096).decode('utf-8')
            output += part
        
        shell.send("wr\n")
        time.sleep(2)
        output += shell.recv(4096).decode('utf-8')
        
        return True, output
    except Exception as e:
        return False, str(e)
    finally:
        ssh_client.close()

def apply_isis_configuration(router_name, net, area, level):
    if not validate_net(net):
        return {"status": "error", "message": "Invalid NET format. Use 49.XXXX.XXXX.XXXX.XXXX.XX"}
    if not validate_area(area):
        return {"status": "error", "message": "Invalid Area ID format. Use 49.XXXX"}
    
    router = get_router_details(router_name)
    if not router:
        return {"status": "error", "message": "Router not found in database"}
    

    commands = [
        "conf t",
        f"router isis {area}",
        f"net {net}",
        f"is-type {level}",
        "exit",
        "exit"
    ]
    
    success, output = execute_ssh_commands(router, commands)
    user_ip = socket.gethostbyname(socket.gethostname())
    
    status = "success" if success else "error"
    log_operation(router["ip"], user_ip, commands, output, status)
    
    if success:
        return {"status": "success", "message": "Configuration applied successfully"}
    else:
        return {"status": "error", "message": f"SSH Error: {output}"}

def delete_isis_configuration(router_name, area):
    if not validate_area(area):
        return {"status": "error", "message": "Invalid Area ID format. Use 49.XXXX"}
    
    router = get_router_details(router_name)
    if not router:
        return {"status": "error", "message": "Router not found in database"}
    
    commands = [
        "conf t",
        f"no router isis {area}",
        "exit"
    ]
    
    success, output = execute_ssh_commands(router, commands)
    user_ip = socket.gethostbyname(socket.gethostname())
    
    status = "success" if success else "error"
    log_operation(router["ip"], user_ip, commands, output, status)
    
    if success:
        return {"status": "success", "message": "Configuration removed successfully"}
    else:
        return {"status": "error", "message": f"SSH Error: {output}"}