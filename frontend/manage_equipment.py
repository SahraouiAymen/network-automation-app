from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QLineEdit, QPushButton, QMessageBox, QGroupBox, QFormLayout,
    QFrame, QGridLayout
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from backend.manage_equipment import get_routers, add_router, delete_router

class EquipmentManager(QWidget):
    def __init__(self, stacked_widget=None):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.setWindowTitle("Router Management")
        self.setMinimumSize(1200, 800)
        self.setup_ui()
        self.load_routers()
        self.setup_styles()

    def setup_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f6fa;
                color: #2d3436;
            }
            QGroupBox {
                border: 2px solid #74b9ff;
                border-radius: 10px;
                margin-top: 1ex;
                padding: 15px;
            }
            QLineEdit {
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
            QPushButton#delete_btn {
                background-color: #e74c3c;
            }
            QPushButton#delete_btn:hover {
                background-color: #c0392b;
            }
            QFrame.router-card {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
            }
        """)

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # Header
        header = QLabel("Router Management")
        header.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header.setStyleSheet("color: #0984e3;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header)

        # Action Buttons Group
        action_group = QGroupBox("Router Actions")
        action_layout = QHBoxLayout()

        # Add Router Section
        add_form = self.create_add_form()
        action_layout.addWidget(add_form, 3)

        # Delete Router Section
        delete_form = self.create_delete_form()
        action_layout.addWidget(delete_form, 1)

        action_group.setLayout(action_layout)
        main_layout.addWidget(action_group)

        # Router List
        list_group = self.create_router_list()
        main_layout.addWidget(list_group)

        self.setLayout(main_layout)

    def create_add_form(self):
        group = QGroupBox("Add Router")
        layout = QFormLayout()

        self.name_input = QLineEdit()
        self.ip_input = QLineEdit()
        self.user_input = QLineEdit()
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)

        layout.addRow(QLabel("Name:"), self.name_input)
        layout.addRow(QLabel("IP Address:"), self.ip_input)
        layout.addRow(QLabel("Username:"), self.user_input)
        layout.addRow(QLabel("Password:"), self.pass_input)

        add_btn = QPushButton("Add Router")
        add_btn.clicked.connect(self.add_router)
        layout.addRow(add_btn)

        group.setLayout(layout)
        return group

    def create_delete_form(self):
        group = QGroupBox("Delete Router")
        layout = QFormLayout()

        self.delete_identifier_input = QLineEdit()
        layout.addRow(QLabel("Name/IP Address:"), self.delete_identifier_input)

        delete_btn = QPushButton("Delete")
        delete_btn.setObjectName("delete_btn")
        delete_btn.clicked.connect(self.delete_router)
        layout.addRow(delete_btn)

        group.setLayout(layout)
        return group

    def create_router_list(self):
        group = QGroupBox("Configured Routers")
        layout = QVBoxLayout()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        self.list_widget = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(15)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        
        self.list_widget.setLayout(self.grid_layout)
        self.scroll_area.setWidget(self.list_widget)
        layout.addWidget(self.scroll_area)

        group.setLayout(layout)
        return group

    def load_routers(self):
        routers = get_routers()
        self.clear_layout(self.grid_layout)
        
        for i, router in enumerate(routers):
            card = self.create_router_card(router, i)
            self.grid_layout.addWidget(card, i // 2, i % 2)

    def create_router_card(self, router, index):
        card = QFrame()
        card.setObjectName("router-card")
        layout = QVBoxLayout(card)
        
        info_layout = QVBoxLayout()
        info_layout.addWidget(self.create_info_label("Name", router['name']))
        info_layout.addWidget(self.create_info_label("IP", router['ip']))
        
        layout.addLayout(info_layout)
        return card

    def create_info_label(self, title, value):
        label = QLabel(f"<b>{title}:</b> {value}")
        label.setStyleSheet("font-size: 14px; color: #2d3436;")
        return label

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def add_router(self):
        router_data = {
            "name": self.name_input.text().strip(),
            "ip": self.ip_input.text().strip(),
            "username": self.user_input.text().strip(),
            "password": self.pass_input.text().strip()
        }
        
        if not all(router_data.values()):
            QMessageBox.warning(self, "Error", "All fields are required!")
            return
            
        if add_router(router_data):
            self.load_routers()
            self.clear_form()
            QMessageBox.information(self, "Success", "Router added successfully!")
        else:
            QMessageBox.critical(self, "Error", "Failed to add router!")

    def delete_router(self):
        identifier = self.delete_identifier_input.text().strip()
        if not identifier:
            QMessageBox.warning(self, "Error", "Name/IP field is required!")
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Delete router with name/IP '{identifier}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            if delete_router(identifier):
                self.load_routers()
                self.delete_identifier_input.clear()
                QMessageBox.information(self, "Success", "Router deleted successfully!")
            else:
                QMessageBox.critical(self, "Error", "No router found with that name or IP!")

    def clear_form(self):
        self.name_input.clear()
        self.ip_input.clear()
        self.user_input.clear()
        self.pass_input.clear()