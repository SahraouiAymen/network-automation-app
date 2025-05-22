from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QMessageBox, QGroupBox, QFormLayout
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from backend.isis import load_routers, generate_isis_commands, generate_isis_delete_commands, apply_configuration

class ISISConfig(QWidget):
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
            QPushButton#backButton {
                background-color: #636e72;
            }
            QPushButton#backButton:hover {
                background-color: #2d3436;
            }
            QPushButton#deleteButton {
                background-color: #e74c3c;
            }
            QPushButton#deleteButton:hover {
                background-color: #c0392b;
            }
        """)

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()
        
        self.back_button = QPushButton("← Back")
        self.back_button.setObjectName("backButton")
        self.back_button.clicked.connect(self.close)
        self.back_button.setFixedWidth(100)
        
        header = QLabel("IS-IS Configuration Manager")
        header.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header.setStyleSheet("color: #0984e3;")
        
        header_layout.addWidget(self.back_button)
        header_layout.addWidget(header, 1, Qt.AlignmentFlag.AlignCenter)
        main_layout.addLayout(header_layout)

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

        # IS-IS Configuration Group
        config_group = QGroupBox("IS-IS Parameters")
        config_layout = QFormLayout()
        config_layout.setHorizontalSpacing(15)
        
        self.net_input = QLineEdit(placeholderText="49.0001.0000.0000.0001.00")
        self.area_input = QLineEdit(placeholderText="49.0001")
        self.level_combo = QComboBox()
        self.level_combo.addItems(["level-1-2", "level-1", "level-2"])
        
        config_layout.addRow(QLabel("Network Entity Title (NET):"), self.net_input)
        config_layout.addRow(QLabel("Area ID:"), self.area_input)
        config_layout.addRow(QLabel("IS-IS Level:"), self.level_combo)
        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)

        # Action Buttons
        action_layout = QHBoxLayout()
        self.delete_btn = QPushButton("Delete Configuration")
        self.delete_btn.setObjectName("deleteButton")
        self.delete_btn.clicked.connect(self.delete_config)
        
        self.apply_btn = QPushButton("Apply Configuration")
        self.apply_btn.clicked.connect(self.apply_config)
        
        action_layout.addWidget(self.delete_btn)
        action_layout.addWidget(self.apply_btn)
        main_layout.addLayout(action_layout)

        self.setLayout(main_layout)
        self.load_routers()

    def load_routers(self):
        self.router_selector.clear()
        routers = load_routers()
        if routers:
            self.router_selector.addItems([r["name"] for r in routers])
        else:
            self.router_selector.setPlaceholderText("No routers available")

    def apply_config(self):
        router_name = self.router_selector.currentText()
        net = self.net_input.text()
        area = self.area_input.text()
        level = self.level_combo.currentText()

        if not all([router_name, net, area]):
            QMessageBox.warning(self, "Error", "All fields are required!")
            return

        commands = generate_isis_commands(net, area, level)
        if apply_configuration(router_name, commands):
            QMessageBox.information(self, "Success", "IS-IS configuration applied successfully!")
        else:
            QMessageBox.critical(self, "Error", "Failed to apply configuration!")

    def delete_config(self):
        router_name = self.router_selector.currentText()
        area = self.area_input.text()

        if not router_name or not area:
            QMessageBox.warning(self, "Error", "Router and Area fields are required for deletion!")
            return

        confirm = QMessageBox.question(
            self, "Confirm Deletion",
            f"Delete IS-IS configuration for area {area} on {router_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            commands = generate_isis_delete_commands(area)
            if apply_configuration(router_name, commands):
                QMessageBox.information(self, "Success", "IS-IS configuration removed successfully!")
            else:
                QMessageBox.critical(self, "Error", "Failed to remove configuration!")