from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QListWidget, QMessageBox, QGroupBox, QScrollArea
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from backend.implement_mpls import load_routers, show_interfaces, configure_mpls, delete_mpls_config

class MPLSPage(QWidget):
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
            QComboBox, QListWidget {
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
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #dcdde1;
            }
            QListWidget::item:selected {
                background-color: #74b9ff;
                color: white;
            }
        """)
    
    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # Header
        header = QLabel("MPLS Configuration Manager")
        header.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #0984e3; margin-bottom: 20px;")
        main_layout.addWidget(header)

        # Router Selection Group
        router_group = QGroupBox("Router Selection")
        router_layout = QHBoxLayout()
        self.router_select = QComboBox()
        self.router_select.setFixedHeight(40)
        self.router_select.addItem("-- Select Router --", None)  # Default empty option
        refresh_btn = QPushButton("Refresh Routers")
        refresh_btn.clicked.connect(self.load_routers)
        show_intf_btn = QPushButton("Show Interfaces")
        show_intf_btn.clicked.connect(self.show_interfaces)
        router_layout.addWidget(self.router_select, 4)
        router_layout.addWidget(refresh_btn, 1)
        router_layout.addWidget(show_intf_btn, 1)
        router_group.setLayout(router_layout)
        main_layout.addWidget(router_group)

        # Interfaces Group
        intf_group = QGroupBox("Interface Selection")
        intf_layout = QVBoxLayout()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.interfaces_list = QListWidget()
        self.interfaces_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        scroll.setWidget(self.interfaces_list)
        
        intf_layout.addWidget(scroll)
        intf_group.setLayout(intf_layout)
        main_layout.addWidget(intf_group)

        # Action Buttons
        action_group = QGroupBox("Configuration Actions")
        action_layout = QHBoxLayout()
        
        self.submit_btn = QPushButton("Configure MPLS")
        self.submit_btn.clicked.connect(self.submit_mpls_config)
        self.submit_btn.setStyleSheet("font-weight: bold;")
        
        self.delete_btn = QPushButton("Delete MPLS")
        self.delete_btn.clicked.connect(self.delete_mpls_configuration)
        self.delete_btn.setStyleSheet("background-color: #e74c3c;")
        
        back_btn = QPushButton("Back")
        back_btn.clicked.connect(self.close)
        
        action_layout.addWidget(back_btn)
        action_layout.addWidget(self.delete_btn)
        action_layout.addWidget(self.submit_btn)
        action_group.setLayout(action_layout)
        main_layout.addWidget(action_group)

        self.setLayout(main_layout)
        self.load_routers()

    def load_routers(self):
        self.router_select.clear()
        self.router_select.addItem("-- Select Router --", None)  # Reset default
        routers = load_routers()
        if routers:
            for router in routers:
                self.router_select.addItem(
                    f"{router['name']} ({router['ip']})",
                    userData=router
                )

    def show_interfaces(self):
        selected_router = self.router_select.currentData()
        self.interfaces_list.clear()  # Clear previous interfaces
        
        if not selected_router:
            QMessageBox.warning(self, "Selection Error", "Please select a router first.")
            return
        
        try:
            interfaces = show_interfaces(selected_router)
            if not interfaces:
                QMessageBox.warning(self, "Interface Error", "No interfaces found on the router.")
                return
            
            self.interfaces_list.addItems(interfaces)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch interfaces: {str(e)}")

    def submit_mpls_config(self):
        selected_router = self.router_select.currentData()
        selected_interfaces = [item.text() for item in self.interfaces_list.selectedItems()]
        
        if not selected_router:
            QMessageBox.warning(self, "Input Error", "Please select a router first.")
            return
        if not selected_interfaces:
            QMessageBox.warning(self, "Input Error", "Please select at least one interface.")
            return
        
        try:
            response = configure_mpls(selected_router, selected_interfaces)
            if response["success"]:
                QMessageBox.information(self, "Success", 
                    f"MPLS configured successfully on {selected_router['name']}!\n"
                    f"Interfaces: {', '.join(selected_interfaces)}\n"
                    f"Output:\n{response['output']}")
            else:
                QMessageBox.critical(self, "Error", 
                    f"Configuration failed:\n{response['error']}")
                
        except Exception as e:
            QMessageBox.critical(self, "Exception", f"An error occurred: {str(e)}")

    def delete_mpls_configuration(self):
        selected_router = self.router_select.currentData()
        selected_interfaces = [item.text() for item in self.interfaces_list.selectedItems()]
        
        if not selected_router:
            QMessageBox.warning(self, "Input Error", "Please select a router first.")
            return
        if not selected_interfaces:
            QMessageBox.warning(self, "Input Error", "Please select at least one interface.")
            return
        
        confirm = QMessageBox.question(
            self, "Confirm Deletion",
            f"Remove MPLS from {len(selected_interfaces)} interfaces on {selected_router['name']}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                response = delete_mpls_config(selected_router, selected_interfaces)
                if response["success"]:
                    QMessageBox.information(self, "Success", 
                        f"MPLS removed successfully on {selected_router['name']}!\n"
                        f"Interfaces: {', '.join(selected_interfaces)}\n"
                        f"Output:\n{response['output']}")
                else:
                    QMessageBox.critical(self, "Error", 
                        f"Deletion failed:\n{response['error']}")
                        
            except Exception as e:
                QMessageBox.critical(self, "Exception", f"An error occurred: {str(e)}")