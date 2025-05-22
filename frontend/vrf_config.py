from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QMessageBox, QGroupBox, QFormLayout
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from backend.vrf_config import fetch_routers_from_db, fetch_interfaces, send_vrf_configuration, remove_vrf_configuration

class VRFConfig(QWidget):
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
        header = QLabel("VRF Configuration Manager")
        header.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #0984e3; margin-bottom: 30px;")
        main_layout.addWidget(header)

        # Router Selection Group
        router_group = QGroupBox("Router Selection")
        router_layout = QHBoxLayout()
        self.router_combo = QComboBox()
        self.router_combo.setFixedHeight(40)
        self.router_combo.currentIndexChanged.connect(self.update_interfaces)
        refresh_btn = QPushButton("Refresh Routers")
        refresh_btn.clicked.connect(self.load_routers)
        router_layout.addWidget(self.router_combo, 4)
        router_layout.addWidget(refresh_btn, 1)
        router_group.setLayout(router_layout)
        main_layout.addWidget(router_group)

        # VRF Configuration Group
        config_group = QGroupBox("Create VRF")
        form_layout = QFormLayout()
        form_layout.setHorizontalSpacing(30)
        form_layout.setVerticalSpacing(15)

        self.vrf_input = QLineEdit(placeholderText="VRF Name")
        self.rd_input = QLineEdit(placeholderText="Route Distinguisher")
        self.rt_input = QLineEdit(placeholderText="Route Target")
        self.interface_combo = QComboBox()

        form_layout.addRow(QLabel("VRF Name*:"), self.vrf_input)
        form_layout.addRow(QLabel("Route Distinguisher*:"), self.rd_input)
        form_layout.addRow(QLabel("Route Target*:"), self.rt_input)
        form_layout.addRow(QLabel("Interface (optional):"), self.interface_combo)
        config_group.setLayout(form_layout)
        main_layout.addWidget(config_group)

        # Remove VRF Group
        remove_group = QGroupBox("Remove VRF")
        remove_layout = QHBoxLayout()
        self.remove_vrf_input = QLineEdit(placeholderText="VRF Name to remove")
        remove_btn = QPushButton("Remove VRF")
        remove_btn.clicked.connect(self.remove_vrf)
        remove_btn.setStyleSheet("background-color: #e74c3c;")
        remove_layout.addWidget(self.remove_vrf_input)
        remove_layout.addWidget(remove_btn)
        remove_group.setLayout(remove_layout)
        main_layout.addWidget(remove_group)

        # Action Buttons
        button_layout = QHBoxLayout()
        submit_btn = QPushButton("Create VRF")
        submit_btn.clicked.connect(self.submit_configuration)
        submit_btn.setStyleSheet("font-weight: bold;")
        
        back_btn = QPushButton("Back")
        back_btn.clicked.connect(self.close_window)
        
        button_layout.addWidget(back_btn)
        button_layout.addWidget(submit_btn)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        self.load_routers()
    
    def close_window(self):
        self.close()

    def load_routers(self):
        self.router_combo.clear()
        self.interface_combo.clear()
        try:
            routers = fetch_routers_from_db()
            self.router_combo.addItem("-- Select Router --", None)
            if routers:
                for router in routers:
                    self.router_combo.addItem(
                        f"{router['name']} ({router['ip']})",
                        userData=router
                    )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load routers: {str(e)}")

    def update_interfaces(self):
        self.interface_combo.clear()
        router = self.router_combo.currentData()
        if router:
            try:
                interfaces = fetch_interfaces(router)
                self.interface_combo.addItem("-- Optional Interface --")
                self.interface_combo.addItems(interfaces)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load interfaces: {str(e)}")

    def submit_configuration(self):
        fields = {
            "VRF Name": self.vrf_input.text().strip(),
            "Route Distinguisher": self.rd_input.text().strip(),
            "Route Target": self.rt_input.text().strip(),
            "Interface": self.interface_combo.currentText(),
            "Router": self.router_combo.currentData()
        }

        # Validate required fields
        required = ["VRF Name", "Route Distinguisher", "Route Target", "Router"]
        missing = [name for name in required if not fields[name]]
        if missing:
            QMessageBox.warning(self, "Input Error", f"Missing required fields: {', '.join(missing)}")
            return

        # Handle optional interface
        interface = fields["Interface"] if fields["Interface"] != "-- Optional Interface --" else None

        try:
            response = send_vrf_configuration(
                router=fields["Router"],
                vrf_name=fields["VRF Name"],
                rd_value=fields["Route Distinguisher"],
                rt_value=fields["Route Target"],
                interface=interface
            )

            if response["success"]:
                QMessageBox.information(self, "Success", 
                    f"VRF '{fields['VRF Name']}' created successfully!\n"
                    f"Router: {fields['Router']['name']}\n")
                self.clear_form()
            else:
                QMessageBox.critical(self, "Error", 
                    f"Configuration failed:\n{response['error']}")

        except Exception as e:
            QMessageBox.critical(self, "Exception", f"An error occurred: {str(e)}")

    def remove_vrf(self):
        vrf_name = self.remove_vrf_input.text().strip()
        router = self.router_combo.currentData()

        if not vrf_name:
            QMessageBox.warning(self, "Input Error", "Please enter a VRF name to remove")
            return
        if not router:
            QMessageBox.warning(self, "Input Error", "Please select a router")
            return

        confirm = QMessageBox.question(
            self, "Confirm Removal",
            f"Remove VRF '{vrf_name}' from {router['name']}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                response = remove_vrf_configuration(router, vrf_name)
                if response["success"]:
                    QMessageBox.information(self, "Success", 
                        f"VRF '{vrf_name}' removed successfully!\n")
                    self.remove_vrf_input.clear()
                else:
                    QMessageBox.critical(self, "Error", 
                        f"Removal failed:\n{response['error']}")
                        
            except Exception as e:
                QMessageBox.critical(self, "Exception", f"An error occurred: {str(e)}")

    def clear_form(self):
        self.vrf_input.clear()
        self.rd_input.clear()
        self.rt_input.clear()
        self.router_combo.setCurrentIndex(0)
        self.interface_combo.clear()