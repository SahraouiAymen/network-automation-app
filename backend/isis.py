from pymongo import MongoClient
import paramiko
import time
import socket
import datetime

def load_routers():
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
        db = client["NetworkApp"]
        routers = db["Routers"].find_one({}, {"routers": 1}).get("routers", [])
        return routers
    except Exception as e:
        print(f"MongoDB Error: {e}")
        return []

def generate_isis_commands(net: str, area: str, level: str) -> list:
    return [
        "conf t",
        f"router isis {area}",
        f"net {net}",
        f"is-type {level}",
        "exit",
        "wr"
    ]

def generate_isis_delete_commands(area: str) -> list:
    return [
        "conf t",
        f"no router isis {area}",
        "wr"
    ]

def apply_configuration(router_name: str, commands: list) -> bool:
    try:
        client = MongoClient("mongodb://localhost:27017/")
        db = client["NetworkApp"]
        router = db["Routers"].find_one(
            {"routers.name": router_name},
            {"_id": 0, "routers.$": 1}
        )["routers"][0]

        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(
            hostname=router["ip"],
            username=router["username"],
            password=router["password"],
            look_for_keys=False,
            allow_agent=False
        )

        shell = ssh_client.invoke_shell()
        shell.settimeout(2)

        # Get local IP as user IP
        user_ip = socket.gethostbyname(socket.gethostname())

        # Initial output (optional)
        time.sleep(1)
        initial_output = shell.recv(65535).decode()

        for cmd in commands:
            shell.send(cmd + '\n')
            time.sleep(1)  # Wait for command execution

            # Capture command output
            output = ""
            while True:
                if shell.recv_ready():
                    part = shell.recv(4096).decode('utf-8')
                    output += part
                else:
                    break

            # Create log entry
            log_entry = {
                "router_ip": router["ip"],
                "user_ip": user_ip,
                "command": cmd,
                "output": output,
                "status": "success",
                "timestamp": datetime.datetime.utcnow()
            }
            db.Logs.insert_one(log_entry)

        ssh_client.close()
        return True
    except Exception as e:
        # Prepare error log
        error_entry = {
            "router_ip": router["ip"] if 'router' in locals() else "unknown",
            "user_ip": user_ip if 'user_ip' in locals() else "unknown",
            "command": " ".join(commands) if 'commands' in locals() else "unknown",
            "output": str(e),
            "status": "error",
            "timestamp": datetime.datetime.utcnow()
        }
        # Attempt to log the error
        try:
            client = MongoClient("mongodb://localhost:27017/")
            db = client["NetworkApp"]
            db.Logs.insert_one(error_entry)
        except Exception as db_error:
            print(f"Failed to log error: {db_error}")
        print(f"Error applying configuration: {e}")
        return False