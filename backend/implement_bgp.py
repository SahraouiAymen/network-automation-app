import paramiko
from pymongo import MongoClient
import time
from datetime import datetime

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["NetworkApp"]
logs_collection = db["Logs"]

def log_bgp_action(action, router, config, status, error=None):
    log_entry = {
        "type": "BGP",
        "action": action,
        "router": router["name"],
        "ip": router["ip"],
        "config": config,
        "timestamp": datetime.now(),
        "status": status,
        "error": error
    }
    logs_collection.insert_one(log_entry)

def load_routers():
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
        db = client["NetworkApp"]
        routers = db["Routers"].find_one({}, {"routers": 1}).get("routers", [])
        return routers
    except Exception as e:
        print(f"MongoDB Error: {e}")
        return []

def configure_bgp(router, bgp_type, local_asn, neighbor_ip, neighbor_asn, prefix, mask):
    response = {"success": False, "output": "", "error": ""}
    config = {
        "bgp_type": bgp_type,
        "local_asn": local_asn,
        "neighbor_ip": neighbor_ip,
        "neighbor_asn": neighbor_asn,
        "prefix": prefix,
        "mask": mask
    }
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(router['ip'],
                   username=router['username'],
                   password=router['password'],
                   timeout=10)
        
        chan = ssh.invoke_shell()
        chan.settimeout(10)
        
        output = ""
        while not output.endswith(('#', '>')):
            output += chan.recv(1024).decode()

        commands = [
            'configure terminal',
            f'router bgp {local_asn}',
            f'neighbor {neighbor_ip} remote-as {neighbor_asn}',
            'address-family ipv4 unicast',
            f'network {prefix} {mask}',
            f'neighbor {neighbor_ip} activate',
            'exit-address-family'
        ]

        if 'iBGP' in bgp_type and local_asn == neighbor_asn:
            commands[3:3] = [
                'bgp log-neighbor-changes',
                f'neighbor {neighbor_ip} update-source Loopback0',
                f'neighbor {neighbor_ip} route-reflector-client'
            ]

        for cmd in commands:
            chan.send(cmd + '\n')
            time.sleep(0.5)
            output = chan.recv(65535).decode()
            response['output'] += output
            
            if '% Invalid' in output:
                raise Exception(f"Command failed: {cmd}\n{output}")

        chan.send('end\nwrite memory\n')
        time.sleep(1)
        response['output'] += chan.recv(65535).decode()
        response['success'] = True
        log_bgp_action("configure", router, config, "success")
        
    except Exception as e:
        error_msg = str(e)
        response['error'] = error_msg
        log_bgp_action("configure", router, config, "error", error_msg)
    finally:
        ssh.close()
    
    return response

def configure_vpnv4(router, local_asn, neighbor_ip):
    response = {"success": False, "output": "", "error": ""}
    config = {
        "local_asn": local_asn,
        "neighbor_ip": neighbor_ip
    }
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(router['ip'],
                   username=router['username'],
                   password=router['password'],
                   timeout=10)
        
        chan = ssh.invoke_shell()
        chan.settimeout(10)
        
        output = ""
        while not output.endswith(('#', '>')):
            output += chan.recv(1024).decode()

        commands = [
            'configure terminal',
            f'router bgp {local_asn}',
            'address-family vpnv4',
            f'neighbor {neighbor_ip} activate',
            f'neighbor {neighbor_ip} send-community extended',
            'exit-address-family',
            'end',
            'write memory'
        ]

        for cmd in commands:
            chan.send(cmd + '\n')
            time.sleep(0.5)
            output = chan.recv(65535).decode()
            response['output'] += output
            
            if '% Invalid' in output:
                raise Exception(f"Command failed: {cmd}\n{output}")

        response['success'] = True
        log_bgp_action("configure_vpnv4", router, config, "success")
        
    except Exception as e:
        error_msg = str(e)
        response['error'] = error_msg
        log_bgp_action("configure_vpnv4", router, config, "error", error_msg)
    finally:
        ssh.close()
    
    return response