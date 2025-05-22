from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QComboBox, QLineEdit, QMessageBox, QGroupBox, QFormLayout)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from backend.implement_bgp import configure_bgp, configure_vpnv4, load_routers

class ImplementBGPPage(QWidget):
    def __init__(self, stacked_widget=None):
        super().__init__()
        self.setMinimumSize(1200, 800)
        self.stacked_widget = stacked_widget
        self.setup_ui()
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f6fa;
                color: #2d3436;
            }
            QGroupBox {
                border: 2px solid #74b9ff;
                border-radius: 10px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
                color: #0984e3;
            }
            QLineEdit, QComboBox {
                border: 1px solid #74b9ff;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #74b9ff;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px 24px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0984e3;
            }
        """)

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Header
        header = QLabel("BGP Configuration")
        header.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #0984e3; margin-bottom: 30px;")
        main_layout.addWidget(header)

        # Router Selection Group
        router_group = QGroupBox("Router Selection")
        router_layout = QHBoxLayout()
        self.router_select = QComboBox()
        self.router_select.setFixedHeight(40)
        refresh_button = QPushButton("Refresh Routers")
        refresh_button.clicked.connect(self.load_routers)
        router_layout.addWidget(self.router_select, 4)
        router_layout.addWidget(refresh_button, 1)
        router_group.setLayout(router_layout)
        main_layout.addWidget(router_group)

        # BGP Configuration Group
        bgp_group = QGroupBox("Base BGP Configuration")
        bgp_form = QFormLayout()
        
        self.bgp_type = QComboBox()
        self.bgp_type.addItems(["Internal BGP (iBGP)", "External BGP (eBGP)"])
        self.local_asn_input = QLineEdit()
        self.neighbor_ip_input = QLineEdit()
        self.neighbor_asn_input = QLineEdit()
        self.network_prefix_input = QLineEdit()
        self.subnet_mask_input = QLineEdit()

        bgp_form.addRow(QLabel("BGP Type:"), self.bgp_type)
        bgp_form.addRow(QLabel("Local ASN:"), self.local_asn_input)
        bgp_form.addRow(QLabel("Neighbor IP:"), self.neighbor_ip_input)
        bgp_form.addRow(QLabel("Neighbor ASN:"), self.neighbor_asn_input)
        bgp_form.addRow(QLabel("Network Prefix:"), self.network_prefix_input)
        bgp_form.addRow(QLabel("Subnet Mask:"), self.subnet_mask_input)
        bgp_group.setLayout(bgp_form)
        main_layout.addWidget(bgp_group)

        # VPNv4 Configuration Group
        vpn_group = QGroupBox("VPNv4 Configuration (Optional)")
        vpn_form = QFormLayout()
        
        self.vpn_neighbor_ip = QLineEdit()
        self.vpn_local_asn = QLineEdit()
        
        vpn_form.addRow(QLabel("Local ASN:"), self.vpn_local_asn)
        vpn_form.addRow(QLabel("Neighbor IP:"), self.vpn_neighbor_ip)
        vpn_group.setLayout(vpn_form)
        main_layout.addWidget(vpn_group)

        # Buttons
        button_layout = QHBoxLayout()
        self.submit_bgp = QPushButton("Apply BGP Config")
        self.submit_bgp.clicked.connect(self.submit_bgp_config)
        self.submit_vpn = QPushButton("Apply VPNv4 Config")
        self.submit_vpn.clicked.connect(self.submit_vpn_config)
        back_button = QPushButton("Back")
        back_button.clicked.connect(self.go_back)

        button_layout.addWidget(back_button)
        button_layout.addWidget(self.submit_bgp)
        button_layout.addWidget(self.submit_vpn)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        self.load_routers()

    def load_routers(self):
        self.router_select.clear()
        routers = load_routers()
        if not routers:
            QMessageBox.warning(self, "Database Error", "No routers found in the database.")
            return
        
        for router in routers:
            self.router_select.addItem(f"{router['name']} ({router['ip']})", router)

    def submit_bgp_config(self):
        selected_router = self.router_select.currentData()
        if not selected_router:
            QMessageBox.warning(self, "Input Error", "Please select a router.")
            return

        fields = {
            "Local ASN": self.local_asn_input.text(),
            "Neighbor IP": self.neighbor_ip_input.text(),
            "Neighbor ASN": self.neighbor_asn_input.text(),
            "Network Prefix": self.network_prefix_input.text(),
            "Subnet Mask": self.subnet_mask_input.text()
        }
        
        if not all(fields.values()):
            missing = [name for name, value in fields.items() if not value]
            QMessageBox.warning(self, "Input Error", f"Missing fields: {', '.join(missing)}")
            return

        try:
            response = configure_bgp(
                router=selected_router,
                bgp_type=self.bgp_type.currentText(),
                local_asn=self.local_asn_input.text(),
                neighbor_ip=self.neighbor_ip_input.text(),
                neighbor_asn=self.neighbor_asn_input.text(),
                prefix=self.network_prefix_input.text(),
                mask=self.subnet_mask_input.text()
            )
            
            if response["success"]:
                QMessageBox.information(self, "Success", "BGP configuration applied successfully!")
            else:
                QMessageBox.critical(self, "Error", f"Failed: {response['error']}")
                
        except Exception as e:
            QMessageBox.critical(self, "Exception", f"Error: {str(e)}")

    def submit_vpn_config(self):
        selected_router = self.router_select.currentData()
        if not selected_router:
            QMessageBox.warning(self, "Input Error", "Please select a router.")
            return

        fields = {
            "Local ASN": self.vpn_local_asn.text(),
            "Neighbor IP": self.vpn_neighbor_ip.text()
        }
        
        if not all(fields.values()):
            QMessageBox.warning(self, "Input Error", "Both VPNv4 fields are required!")
            return

        try:
            response = configure_vpnv4(
                router=selected_router,
                local_asn=self.vpn_local_asn.text(),
                neighbor_ip=self.vpn_neighbor_ip.text()
            )
            
            if response["success"]:
                QMessageBox.information(self, "Success", "VPNv4 configuration applied successfully!")
            else:
                QMessageBox.critical(self, "Error", f"Failed: {response['error']}")
                
        except Exception as e:
            QMessageBox.critical(self, "Exception", f"Error: {str(e)}")

    def go_back(self):
        self.close()