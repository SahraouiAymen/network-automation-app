from pymongo import MongoClient
import paramiko
import time
from datetime import datetime

client = MongoClient("mongodb://localhost:27017/")
db = client["NetworkApp"]
router_collection = db["Routers"]
ssh_logs = db["SSHLogs"]
config_logs = db["Logs"]

def get_routers():
    doc = router_collection.find_one({"routers": {"$exists": True}})
    return doc.get("routers", []) if doc else []

def router_connection(router_name):
    doc = router_collection.find_one(
        {"routers.name": router_name},
        {"_id": 0, "routers.$": 1}
    )
    if not doc or not doc.get("routers"):
        raise ValueError("Router not found")
    return doc["routers"][0]

def execute_ssh_commands(router, commands):
    logged_commands = []
    full_output = ""
    status = "failure"
    success = False
    error = None

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            router["ip"],
            username=router["username"],
            password=router["password"],
            timeout=10
        )
        channel = ssh.invoke_shell()
        time.sleep(1)

        if "enable_password" in router:
            channel.send("enable\n")
            time.sleep(1)
            channel.send(f"{router['enable_password']}\n")
            time.sleep(1)
            logged_commands.extend(["enable", "********"])

        logged_commands.extend(commands)
        for cmd in commands:
            channel.send(f"{cmd}\n")
            time.sleep(0.5)

        output = ""
        while True:
            if channel.recv_ready():
                output += channel.recv(4096).decode()
                time.sleep(0.5)
            else:
                break
        full_output = output.strip()
        
        success = "% Invalid" not in output and "error" not in output.lower()
        status = "success" if success else "failure"

    except Exception as e:
        error = str(e)
        full_output = f"SSH Error: {error}"
        status = "error"

    finally:
        log_entry = {
            "ip": router["ip"],
            "username": router["username"],
            "commands": logged_commands,
            "output": full_output,
            "status": status,
            "timestamp": datetime.now(),
            "error": error
        }
        ssh_logs.insert_one(log_entry)
        
        if 'ssh' in locals():
            ssh.close()

    return success if success else full_output

def apply_ospf_config(router_name, networks, ospf_id):
    try:
        router = router_connection(router_name)
        commands = ["configure terminal", f"router ospf {ospf_id}"]
        commands.extend(f"network {n['network']} {n['mask']} area {n['area']}" for n in networks)
        commands += ["end", "write memory"]
        result = execute_ssh_commands(router, commands)
        
        log_entry = {
            "action": "apply",
            "router": router_name,
            "ospf_id": ospf_id,
            "networks": networks,
            "timestamp": datetime.now(),
            "status": "success" if isinstance(result, bool) and result else "failure",
            "error": result if not isinstance(result, bool) else None
        }
        config_logs.insert_one(log_entry)
        
        return result
    except Exception as e:
        log_entry = {
            "action": "apply",
            "router": router_name,
            "ospf_id": ospf_id,
            "networks": networks,
            "timestamp": datetime.now(),
            "status": "error",
            "error": str(e)
        }
        config_logs.insert_one(log_entry)
        return str(e)

def delete_ospf_config(router_name, ospf_id):
    try:
        router = router_connection(router_name)
        commands = [
            "configure terminal",
            f"no router ospf {ospf_id}",
            "end",
            "write memory"
        ]
        result = execute_ssh_commands(router, commands)
        
        log_entry = {
            "action": "delete_all",
            "router": router_name,
            "ospf_id": ospf_id,
            "timestamp": datetime.now(),
            "status": "success" if isinstance(result, bool) and result else "failure",
            "error": result if not isinstance(result, bool) else None
        }
        config_logs.insert_one(log_entry)
        
        return result
    except Exception as e:
        log_entry = {
            "action": "delete_all",
            "router": router_name,
            "ospf_id": ospf_id,
            "timestamp": datetime.now(),
            "status": "error",
            "error": str(e)
        }
        config_logs.insert_one(log_entry)
        return str(e)

def delete_ospf_network(router_name, network, mask, area, ospf_id):
    try:
        router = router_connection(router_name)
        commands = [
            "configure terminal",
            f"router ospf {ospf_id}",
            f"no network {network} {mask} area {area}",
            "end",
            "write memory"
        ]
        result = execute_ssh_commands(router, commands)
        
        log_entry = {
            "action": "delete_network",
            "router": router_name,
            "ospf_id": ospf_id,
            "network": network,
            "mask": mask,
            "area": area,
            "timestamp": datetime.now(),
            "status": "success" if isinstance(result, bool) and result else "failure",
            "error": result if not isinstance(result, bool) else None
        }
        config_logs.insert_one(log_entry)
        
        return result if isinstance(result, bool) else "Network not found"
    except Exception as e:
        log_entry = {
            "action": "delete_network",
            "router": router_name,
            "ospf_id": ospf_id,
            "network": network,
            "mask": mask,
            "area": area,
            "timestamp": datetime.now(),
            "status": "error",
            "error": str(e)
        }
        config_logs.insert_one(log_entry)
        return str(e)