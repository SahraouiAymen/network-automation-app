from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QMessageBox, QScrollArea, QFrame,
    QGroupBox, QFormLayout, QSizePolicy
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from backend.ospf import get_routers, apply_ospf_config, delete_ospf_config, delete_ospf_network

class OSPFConfig(QWidget):
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
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # Header
        header = QLabel("OSPF Configuration Manager")
        header.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #0984e3; margin-bottom: 20px;")
        main_layout.addWidget(header)

        # Router Selection Group
        router_group = QGroupBox("Router Selection")
        router_layout = QHBoxLayout()
        self.router_selector = QComboBox()
        self.router_selector.setFixedHeight(40)
        refresh_btn = QPushButton("Refresh Routers")
        refresh_btn.clicked.connect(self.load_routers)
        router_layout.addWidget(self.router_selector, 4)
        router_layout.addWidget(refresh_btn, 1)
        router_group.setLayout(router_layout)
        main_layout.addWidget(router_group)

        # Network Configuration Group
        config_group = QGroupBox("OSPF Networks Configuration")
        config_layout = QVBoxLayout()
        
        # OSPF ID Input
        ospf_id_layout = QHBoxLayout()
        ospf_id_label = QLabel("OSPF Process ID:")
        self.ospf_id_input = QLineEdit(placeholderText="Enter OSPF ID (e.g., 1)")
        ospf_id_layout.addWidget(ospf_id_label)
        ospf_id_layout.addWidget(self.ospf_id_input)
        config_layout.addLayout(ospf_id_layout)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        self.networks_frame = QWidget()
        self.networks_layout = QVBoxLayout(self.networks_frame)
        self.networks_layout.setSpacing(15)
        
        scroll.setWidget(self.networks_frame)
        config_layout.addWidget(scroll)
        
        add_btn = QPushButton("+ Add Network")
        add_btn.clicked.connect(self.add_network_input)
        add_btn.setFixedWidth(150)
        config_layout.addWidget(add_btn, 0, Qt.AlignmentFlag.AlignLeft)
        
        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)

        # Action Buttons
        action_group = QGroupBox("Configuration Actions")
        action_layout = QHBoxLayout()
        
        apply_btn = QPushButton("Apply OSPF Configuration")
        apply_btn.clicked.connect(self.submit_config)
        apply_btn.setStyleSheet("font-weight: bold;")
        
        del_all_btn = QPushButton("Delete All OSPF")
        del_all_btn.clicked.connect(self.delete_all_config)
        del_all_btn.setStyleSheet("background-color: #e74c3c;")
        
        
        action_layout.addWidget(apply_btn)
        action_layout.addWidget(del_all_btn)
        action_group.setLayout(action_layout)
        main_layout.addWidget(action_group)

        # Delete Specific Network Group
        del_group = QGroupBox("Delete Specific Network")
        del_layout = QFormLayout()
        del_layout.setHorizontalSpacing(15)
        
        self.del_net_input = QLineEdit(placeholderText="Network Address")
        self.del_mask_input = QLineEdit(placeholderText="Wildcard Mask")
        self.del_area_input = QLineEdit(placeholderText="Area ID")
        del_btn = QPushButton("Delete Network")
        del_btn.clicked.connect(self.delete_single_network)
        
        del_layout.addRow(QLabel("Network:"), self.del_net_input)
        del_layout.addRow(QLabel("Wildcard Mask:"), self.del_mask_input)
        del_layout.addRow(QLabel("Area ID:"), self.del_area_input)
        del_layout.addRow(del_btn)
        del_group.setLayout(del_layout)
        main_layout.addWidget(del_group)

        self.setLayout(main_layout)
        self.load_routers()
        self.add_network_input()

    def load_routers(self):
        self.router_selector.clear()
        routers = get_routers()
        if routers:
            self.router_selector.addItems([r["name"] for r in routers])

    def add_network_input(self):
        entry = QWidget()
        entry.setStyleSheet("background-color: white; border-radius: 5px;")
        layout = QHBoxLayout(entry)
        layout.setContentsMargins(10, 5, 10, 5)
        
        inputs = (
            QLineEdit(placeholderText="Network Address"),
            QLineEdit(placeholderText="Wildcard Mask"),
            QLineEdit(placeholderText="Area ID")
        )
        
        for field in inputs:
            field.setFixedHeight(35)
            layout.addWidget(field)
        
        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(30, 30)
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border-radius: 15px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        remove_btn.clicked.connect(lambda _, e=entry: self.remove_network_entry(e))
        layout.addWidget(remove_btn)
        
        self.networks_layout.addWidget(entry)
        self.networks_layout.setStretchFactor(entry, 1)

    def remove_network_entry(self, entry):
        entry.deleteLater()

    def submit_config(self):
        router = self.router_selector.currentText()
        if not router:
            QMessageBox.warning(self, "Error", "Please select a router first!")
            return

        ospf_id = self.ospf_id_input.text().strip()
        if not ospf_id:
            QMessageBox.warning(self, "Error", "Please enter OSPF ID!")
            return

        networks = []
        for i in range(self.networks_layout.count()):
            widget = self.networks_layout.itemAt(i).widget()
            if widget:
                inputs = widget.findChildren(QLineEdit)
                if len(inputs) == 3:
                    net_data = {
                        "network": inputs[0].text().strip(),
                        "mask": inputs[1].text().strip(),
                        "area": inputs[2].text().strip()
                    }
                    if all(net_data.values()):
                        networks.append(net_data)

        if not networks:
            QMessageBox.warning(self, "Error", "Add at least one valid network configuration!")
            return

        result = apply_ospf_config(router, networks, ospf_id)
        self.show_result("OSPF Configuration", result)

    def delete_all_config(self):
        router = self.router_selector.currentText()
        if not router:
            QMessageBox.warning(self, "Error", "Please select a router first!")
            return

        ospf_id = self.ospf_id_input.text().strip()
        if not ospf_id:
            QMessageBox.warning(self, "Error", "Please enter OSPF ID!")
            return

        confirm = QMessageBox.question(
            self, "Confirm Deletion",
            f"Delete ALL OSPF configuration (ID: {ospf_id}) on {router}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            result = delete_ospf_config(router, ospf_id)
            self.show_result("OSPF Deletion", result)

    def delete_single_network(self):
        router = self.router_selector.currentText()
        if not router:
            QMessageBox.warning(self, "Error", "Please select a router first!")
            return

        ospf_id = self.ospf_id_input.text().strip()
        if not ospf_id:
            QMessageBox.warning(self, "Error", "Please enter OSPF ID!")
            return

        network = {
            "network": self.del_net_input.text().strip(),
            "mask": self.del_mask_input.text().strip(),
            "area": self.del_area_input.text().strip()
        }
        if not all(network.values()):
            QMessageBox.warning(self, "Error", "Fill all network fields for deletion!")
            return

        confirm = QMessageBox.question(
            self, "Confirm Deletion",
            f"Delete network {network['network']} from OSPF configuration (ID: {ospf_id})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            result = delete_ospf_network(router, network['network'], network['mask'], network['area'], ospf_id)
            self.show_result("Network Deletion", result)

    def show_result(self, title, result):
        if isinstance(result, bool) and result:
            QMessageBox.information(self, title, "Operation completed successfully!")
            self.load_routers()
        else:
            QMessageBox.critical(self, "Error", f"Operation failed:\n{str(result)}")

    def go_back(self):
        if self.stacked_widget:
            self.stacked_widget.setCurrentIndex(0)