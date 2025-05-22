from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QScrollArea, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from backend.config import get_router_list, get_running_config_sections
import socket

class ConfigPage(QWidget):
    def __init__(self, stacked_widget=None):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.setup_ui()
        self.apply_styles()
        self.load_routers()

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget { background-color: #f5f6fa; color: #2d3436; }
            QGroupBox {
                border: 2px solid #74b9ff;
                border-radius: 10px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                color: #0984e3;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
            QComboBox, QPushButton {
                border: 1px solid #74b9ff;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #74b9ff;
                color: white;
            }
            QPushButton:hover { background-color: #0984e3; }
            QTableWidget {
                background-color: white;
                border: 1px solid #dcdde1;
            }
            QHeaderView::section {
                background-color: #74b9ff;
                color: white;
                padding: 8px;
            }
            QTableWidget::item { padding: 8px; border-bottom: 1px solid #dcdde1; }
        """)

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # Header
        header = QLabel("Router Configuration Viewer")
        header.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #0984e3; margin-bottom: 20px;")
        main_layout.addWidget(header)

        # Router Selection
        router_group = QGroupBox("Router Selection")
        router_layout = QHBoxLayout()
        self.router_selector = QComboBox()
        self.router_selector.setFixedHeight(40)
        self.fetch_btn = QPushButton("Fetch Configuration")
        self.fetch_btn.setFixedHeight(40)
        self.fetch_btn.clicked.connect(self.fetch_configuration)
        router_layout.addWidget(self.router_selector, 4)
        router_layout.addWidget(self.fetch_btn, 1)
        router_group.setLayout(router_layout)
        main_layout.addWidget(router_group)

        # Configuration Table
        table_group = QGroupBox("Configuration Details")
        table_layout = QVBoxLayout()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Section", "Configuration"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        scroll.setWidget(self.table)
        table_layout.addWidget(scroll)
        table_group.setLayout(table_layout)
        main_layout.addWidget(table_group)

        # Navigation
        back_btn = QPushButton("Back")
        back_btn.clicked.connect(self.close)
        main_layout.addWidget(back_btn)

        self.setLayout(main_layout)

    def get_user_ip(self):
        """Get reliable client IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            print(f"IP Detection Error: {e}")
            return "127.0.0.1"

    def load_routers(self):
        self.router_selector.clear()
        routers = get_router_list()
        if not routers:
            QMessageBox.warning(self, "Warning", "No configured routers found")
            return
        for router in routers:
            self.router_selector.addItem(
                f"{router['name']} ({router['ip']})",
                userData=router
            )

    def fetch_configuration(self):
        if not self.router_selector.currentData():
            QMessageBox.warning(self, "Warning", "Please select a router first")
            return

        try:
            router = self.router_selector.currentData()
            user_ip = self.get_user_ip()
            sections = get_running_config_sections(router, user_ip)
            self.populate_table(sections)
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                f"Failed to retrieve configuration:\n{str(e)}")

    def populate_table(self, sections):
        self.table.setRowCount(0)
        for row, (section, config) in enumerate(sections.items()):
            self.table.insertRow(row)
            section_item = QTableWidgetItem(section)
            section_item.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            config_item = QTableWidgetItem(config)
            config_item.setFont(QFont("Arial", 12))
            self.table.setItem(row, 0, section_item)
            self.table.setItem(row, 1, config_item)
            self.table.resizeRowToContents(row)