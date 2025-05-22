import paramiko
from pymongo import MongoClient
import time
from datetime import datetime

# MongoDB connection setup
client = MongoClient("mongodb://localhost:27017/")
db = client["NetworkApp"]
mpls_logs = db["Logs"]

def load_routers():
    try:
        client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=5000)
        db = client["NetworkApp"]
        doc = db["Routers"].find_one({}, {"routers": 1})
        return doc.get("routers", []) if doc else []
    except Exception as e:
        print(f"MongoDB Error: {e}")
        return []
def show_interfaces(router):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            router['ip'],
            username=router['username'],
            password=router['password'],
            timeout=10
        )
        
        stdin, stdout, stderr = ssh.exec_command("show ip interface brief")
        output = stdout.read().decode()
        interfaces = [line.split()[0] for line in output.splitlines() 
                     if line.strip() and not line.startswith('Interface')]
        return interfaces
    except Exception as e:
        raise Exception(f"SSH Error: {str(e)}")
    finally:
        if 'ssh' in locals():
            ssh.close()

def log_mpls_action(action, router, interfaces, status, error=None):
    log_entry = {
        "type": "MPLS",
        "action": action,
        "router": router["name"],
        "interfaces": interfaces,
        "timestamp": datetime.now(),
        "status": status,
        "error": error
    }
    mpls_logs.insert_one(log_entry)

def configure_mpls(router, interfaces):
    response = {"success": False, "output": "", "error": ""}
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            router['ip'],
            username=router['username'],
            password=router['password'],
            timeout=10
        )

        chan = ssh.invoke_shell()
        commands = [
            "configure terminal",
            "mpls ip",
            *[f"interface {intf}\nmpls ip\nexit" for intf in interfaces],
            "end",
            "write memory"
        ]

        full_output = ""
        for cmd in commands:
            chan.send(f"{cmd}\n")
            time.sleep(0.5)
            output = chan.recv(65535).decode()
            full_output += output
            
            if "% Invalid" in output:
                response["error"] = f"Command failed: {cmd}"
                break
        else:
            response.update({"success": True})

        log_mpls_action(
            "configure", 
            router,
            interfaces,
            "success" if response["success"] else "failure",
            response["error"] if not response["success"] else None
        )

    except Exception as e:
        error_msg = f"Connection error: {str(e)}"
        response["error"] = error_msg
        log_mpls_action("configure", router, interfaces, "error", error_msg)
    finally:
        if 'ssh' in locals():
            ssh.close()
    
    return response

def delete_mpls_config(router, interfaces):
    response = {"success": False, "output": "", "error": ""}
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            router['ip'],
            username=router['username'],
            password=router['password'],
            timeout=10
        )

        chan = ssh.invoke_shell()
        commands = [
            "configure terminal",
            *[f"interface {intf}\nno mpls ip\nexit" for intf in interfaces],
            "end",
            "write memory"
        ]

        full_output = ""
        for cmd in commands:
            chan.send(f"{cmd}\n")
            time.sleep(0.5)
            output = chan.recv(65535).decode()
            full_output += output
            
            if "% Invalid" in output:
                response["error"] = f"Command failed: {cmd}"
                break
        else:
            response.update({"success": True})

        log_mpls_action(
            "delete", 
            router,
            interfaces,
            "success" if response["success"] else "failure",
            response["error"] if not response["success"] else None
        )

    except Exception as e:
        error_msg = f"Connection error: {str(e)}"
        response["error"] = error_msg
        log_mpls_action("delete", router, interfaces, "error", error_msg)
    finally:
        if 'ssh' in locals():
            ssh.close()
    
    return response