from pymongo import MongoClient
import paramiko
import re
import datetime
import socket

def get_router_list():
    """Fetch validated routers from MongoDB"""
    try:
        client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=5000)
        db = client["NetworkApp"]
        doc = db["Routers"].find_one({"routers": {"$exists": True}})
        return [router for router in doc.get("routers", []) 
                if all(key in router for key in ['name', 'ip', 'username', 'password'])] if doc else []
    except Exception as e:
        print(f"MongoDB Error: {e}")
        return []

def log_command(router_ip, user_ip, command, output, status):
    """Store command execution details in Logs collection"""
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
        db = client["NetworkApp"]
        
        log_entry = {
            "router_ip": router_ip,
            "user_ip": user_ip,
            "command": command,
            "output": output[:10000],  # Store first 10k characters
            "status": status,
            "timestamp": datetime.datetime.now()
        }
        
        db["Logs"].insert_one(log_entry)
    except Exception as e:
        print(f"Command logging failed: {e}")

def get_running_config_sections(router, user_ip):
    """Get running config with command logging"""
    try:
        config = ssh_get_running_config(router, user_ip)
        return split_config_sections(config)
    except Exception as e:
        log_command(
            router['ip'], 
            user_ip,
            "show running-config",
            str(e),
            "error"
        )
        raise RuntimeError(f"Configuration retrieval failed: {str(e)}")

def ssh_get_running_config(router, user_ip):
    """SSH connection handler with command logging"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(
            hostname=router['ip'],
            username=router['username'],
            password=router['password'],
            timeout=10,
            banner_timeout=20
        )
        
        # Execute and log command
        command = "show running-config"
        stdin, stdout, stderr = ssh.exec_command(command)
        raw_output = stdout.read().decode(errors="ignore")
        error_output = stderr.read().decode(errors="ignore")
        full_output = f"{raw_output}\n{error_output}".strip()

        if error_output:
            log_command(
                router['ip'],
                user_ip,
                command,
                full_output,
                "error"
            )
            raise RuntimeError(f"Command error: {error_output}")
            
        if not raw_output:
            log_command(
                router['ip'],
                user_ip,
                command,
                "No output received from device",
                "error"
            )
            raise RuntimeError("No configuration output")

        # Log successful execution
        log_command(
            router['ip'],
            user_ip,
            command,
            raw_output[:10000],  # Truncate to 10k characters
            "success"
        )
            
        return raw_output
        
    except Exception as e:
        raise RuntimeError(f"Connection error: {str(e)}")
    finally:
        ssh.close()

def split_config_sections(config):
    """Parse configuration into sections"""
    sections = {}
    current_section = "Global Configuration"
    current_lines = []
    
    section_pattern = re.compile(
        r"^(interface|router|line|vlan|ip route|route-map|access-list|banner|ntp|snmp-server)\s+.+$",
        re.IGNORECASE
    )
    
    for line in config.splitlines():
        line = line.strip()
        if not line:
            continue
            
        if section_pattern.match(line):
            if current_lines:
                sections[current_section] = "\n".join(current_lines)
            current_section = line
            current_lines = []
        else:
            current_lines.append(line)
    
    if current_lines:
        sections[current_section] = "\n".join(current_lines)
    
    if "version" in config.lower():
        sections["System Info"] = "\n".join(
            line for line in config.splitlines() 
            if "version" in line.lower() or "hostname" in line.lower()
        )
        
    return sections