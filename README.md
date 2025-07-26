# Network Automation Desktop Application (PFE Project)
This repository contains the source code for my final year PFE project: a PyQt6-based desktop application for automating and monitoring complex network infrastructure. The application is designed to streamline configuration deployment, monitor router health in real time, and support service provider-level routing technologies.

🌐 Key Features
User Authentication: Secure login integrated with MongoDB for user validation.

Real-Time Router Monitoring: Live CPU, memory, latency, and uptime charts using SSH via Paramiko.

Modular Configuration Pages:

VRF Creation: Configure VRFs with RD and RT, pulled from MongoDB router info.

BGP Setup: Configure internal or external BGP, including VPNv4 sessions.

MPLS Deployment: Select interfaces and deploy MPLS configurations.

OSPF Configuration: Deploy OSPF configurations across selected networks and areas.

SSH-Based Automation: Automate configuration deployment using Netmiko and Paramiko.

MongoDB Integration: Store and retrieve router data dynamically (CE, PE, P).

User-Friendly GUI: PyQt6 frontend with multi-page navigation (Login, Monitor, Modify, Stats).

🖥️ Technologies Used
Python 3

PyQt6

Netmiko & Paramiko

MongoDB

Matplotlib

GNS3 (for network emulation and testing)


/network_automation/
│
├── main.py
├── config.py
├── router_list.json
├── users.json
│
├── /frontend/
│   ├── login.py
│   ├── monitor.py
│   ├── modify.py
│   ├── automation.py
│
├── /backend/
│   ├── authentication.py
│   ├── monitor.py
│   ├── automation.py
