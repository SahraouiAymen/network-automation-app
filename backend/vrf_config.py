import paramiko
from pymongo import MongoClient
import re
import time
from datetime import datetime

# MongoDB Configuration
VRF_LOGS = MongoClient("mongodb://localhost:27017/")["NetworkApp"]["Logs"]
ROUTER_DB = MongoClient("mongodb://localhost:27017/")["NetworkApp"]["Routers"]

def log_vrf_action(action, status, router, config, error=None):
    """Log VRF actions to MongoDB"""
    log_entry = {
        "type": "VRF",
        "action": action,
        "status": status,
        "router": {
            "name": router.get('name'),
            "ip": router.get('ip')
        },
        "config": config,
        "timestamp": datetime.now(),
        "error": error
    }
    VRF_LOGS.insert_one(log_entry)

def fetch_routers_from_db():
    """Fetch routers from MongoDB with error handling"""
    try:
        return ROUTER_DB.find_one().get("routers", [])
    except Exception as e:
        print(f"Database Error: {e}")
        return []

def fetch_interfaces(router):
    """Fetch router interfaces via SSH with logging"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(
            router['ip'],
            username=router['username'],
            password=router['password'],
            timeout=10
        )
        
        stdin, stdout, stderr = ssh.exec_command("show ip interface brief")
        output = stdout.read().decode()
        
        interfaces = [
            line.split()[0] 
            for line in output.splitlines() 
            if line.strip() and not line.startswith('Interface')
        ]
        
        # Log interface fetch operation
        VRF_LOGS.insert_one({
            "type": "VRF",
            "action": "fetch_interfaces",
            "status": "success",
            "router": router['name'],
            "ip": router['ip'],
            "timestamp": datetime.now(),
            "interface_count": len(interfaces)
        })
        
        return interfaces
        
    except Exception as e:
        error_msg = f"Interface fetch failed: {str(e)}"
        log_entry = {
            "type": "VRF",
            "action": "fetch_interfaces",
            "status": "error",
            "router": router['name'],
            "ip": router['ip'],
            "timestamp": datetime.now(),
            "error": error_msg
        }
        VRF_LOGS.insert_one(log_entry)
        raise Exception(error_msg)
    finally:
        ssh.close()

def validate_vrf_name(name):
    """Validate VRF naming convention"""
    return re.match(r"^[a-zA-Z0-9_-]{1,32}$", name)

def execute_ssh_commands(router, commands):
    """Execute SSH commands with enhanced logging"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    full_output = ""
    
    try:
        ssh.connect(
            router['ip'],
            username=router['username'],
            password=router['password'],
            timeout=10
        )
        chan = ssh.invoke_shell()
        
        # Read initial prompt
        while not full_output.endswith(('#', '>')):
            full_output += chan.recv(1024).decode()

        # Execute commands
        for cmd in commands:
            chan.send(f"{cmd}\n")
            time.sleep(0.5)
            resp = chan.recv(4096).decode()
            full_output += resp
            if any(err in resp for err in ["% Invalid", "% Error"]):
                raise ValueError(f"Command failed: {cmd}\n{resp}")

        # Save configuration
        chan.send("write memory\n")
        time.sleep(1)
        return full_output
    
    except Exception as e:
        raise  # Re-raise for upper layer handling
    finally:
        ssh.close()
def send_vrf_configuration(router, vrf_name, rd_value, rt_value, interface=None):
    """Main VRF configuration function with full logging"""
    response = {"success": False, "output": "", "error": ""}
    config = {
        "vrf_name": vrf_name,
        "rd": rd_value,
        "rt": rt_value,
        "interface": interface
    }

    try:
        if not validate_vrf_name(vrf_name):
            raise ValueError("Invalid VRF name (max 32 chars, alphanumeric)")
        
        if not re.match(r"^\d+:\d+$", rd_value):
            raise ValueError("Invalid RD format (ASN:NN or IP:NN)")
        commands = [
            "configure terminal",
            f"ip vrf {vrf_name}",
            f"rd {rd_value}",
            f"route-target export {rt_value}",
            f"route-target import {rt_value}",
            "exit"
        ]
        if interface and interface != "-- Optional Interface --":
            commands += [
                f"interface {interface}",
                f"ip vrf forwarding {vrf_name}",
                "exit"
            ]
        commands.append("end")
        
        # Execute
        output = execute_ssh_commands(router, commands)
        response.update(success=True, output=output)
        log_vrf_action("create", "success", router, config)

    except Exception as e:
        error_msg = str(e)
        response["error"] = error_msg
        log_vrf_action("create", "failed", router, config, error_msg)
    
    return response

def remove_vrf_configuration(router, vrf_name):
    """VRF removal function with full logging"""
    response = {"success": False, "output": "", "error": ""}
    config = {"vrf_name": vrf_name}

    try:
        commands = [
            "configure terminal",
            f"no ip vrf {vrf_name}",
            "end",
            "write memory"
        ]
        output = execute_ssh_commands(router, commands)
        response.update(success=True, output=output)
        log_vrf_action("delete", "success", router, config)

    except Exception as e:
        error_msg = str(e)
        response["error"] = error_msg
        log_vrf_action("delete", "failed", router, config, error_msg)
    
    return response