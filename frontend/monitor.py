from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, 
    QListWidget, QFrame, QGridLayout, QPushButton, QGroupBox, QMessageBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal
from backend.monitor import fetch_routers, validate_router_credentials, handle_logout_request
from frontend.stats_page import StatsWindow
from frontend.modify import ModifyPage
from frontend.manage_equipment import EquipmentManager

class RouterCard(QGroupBox):
    status_requested = pyqtSignal(dict)

    def __init__(self, router_data, parent=None):
        super().__init__(parent)
        self.router_data = router_data
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
            QGroupBox {
                background-color: #ffffff;
                border: 2px solid #74b9ff;
                border-radius: 10px;
                margin-top: 1ex;
            }
            QLabel { color: #2d3436; font-size: 14px; }
        """)

        layout = QVBoxLayout()
        title = QLabel(f"Router: {self.router_data['name']}")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #0984e3;")

        status_btn = QPushButton("View Statistics")
        status_btn.setStyleSheet("""
            QPushButton {
                background-color: #74b9ff;
                color: white;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover { background-color: #0984e3; }
        """)
        status_btn.clicked.connect(self.on_status_clicked)

        layout.addWidget(title)
        layout.addWidget(QLabel(f"IP Address: {self.router_data['ip']}"))
        layout.addWidget(status_btn)
        self.setLayout(layout)

    def on_status_clicked(self):
        if validate_router_credentials(self.router_data):
            self.status_requested.emit(self.router_data)
        else:
            QMessageBox.warning(self, "Invalid Credentials", 
                              "Missing required router credentials")

class MonitorPage(QWidget):
    logout_requested = pyqtSignal()
    refresh_needed = pyqtSignal()

    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.child_windows = []
        self.setup_ui()
        self.setStyleSheet("background-color: #f5f6fa;")
        self.refresh_needed.connect(self.load_routers)

    def setup_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Navigation panel
        nav_frame = self.create_navigation_panel()
        main_layout.addWidget(nav_frame)

        # Main content area
        content_layout = QVBoxLayout()
        content_layout.addWidget(self.create_header())
        content_layout.addWidget(self.create_router_grid())
        
        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)
        self.load_routers()

    def create_navigation_panel(self):
        frame = QFrame()
        frame.setFixedWidth(200)
        layout = QVBoxLayout()
        
        self.nav_list = QListWidget()
        self.nav_list.addItems(["Dashboard", "Manage Configuration", 
                              "Manage Equipment", "Logout"])
        self.nav_list.itemClicked.connect(self.handle_navigation)
        self.nav_list.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                border: 2px solid #74b9ff;
                border-radius: 8px;
                padding: 10px;
            }
            QListWidget::item {
                padding: 12px;
                color: #2d3436;
            }
            QListWidget::item:hover { background-color: #dfe6e9; }
            QListWidget::item:selected { background-color: #74b9ff; color: white; }
        """)
        
        layout.addWidget(QLabel("Navigation", 
                             styleSheet="font-size: 18px; color: #0984e3;"))
        layout.addWidget(self.nav_list)
        frame.setLayout(layout)
        return frame

    def create_header(self):
        header = QLabel("Network Monitoring Dashboard")
        header.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header.setStyleSheet("color: #0984e3; margin-bottom: 20px;")
        return header

    def create_router_grid(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        self.grid_content = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(15)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        
        self.grid_content.setLayout(self.grid_layout)
        scroll_area.setWidget(self.grid_content)
        return scroll_area

    def load_routers(self):
        self.clear_layout(self.grid_layout)
        routers = fetch_routers()
        
        for i, router in enumerate(routers):
            card = RouterCard(router)
            card.status_requested.connect(self.show_router_stats)
            self.grid_layout.addWidget(card, i // 3, i % 3)

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def show_router_stats(self, router_data):
        # Extract all required parameters from router_data
        stats_window = StatsWindow(
            router_name=router_data['name'],
            host=router_data['ip'],
            username=router_data['username'],
            password=router_data['password']
        )
        self.add_child_window(stats_window)
        stats_window.show()

    def add_child_window(self, window):
        self.child_windows.append(window)
        window.destroyed.connect(lambda: self.child_windows.remove(window))

    def handle_navigation(self, item):
        action = item.text()
        {
            "Logout": self.handle_logout,
            "Manage Configuration": self.open_modify_page,
            "Manage Equipment": self.open_equipment_manager,
            "Dashboard": self.refresh_needed.emit
        }.get(action, lambda: None)()

    def handle_logout(self):
        if handle_logout_request():
            confirm = QMessageBox.question(
                self, "Confirm Logout", "Are you sure you want to logout?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirm == QMessageBox.StandardButton.Yes:
                for window in self.child_windows:
                    window.close()
                self.child_windows.clear()
                self.logout_requested.emit()

    def open_modify_page(self):
        window = ModifyPage(self.stacked_widget)
        self.add_child_window(window)
        window.show()

    def open_equipment_manager(self):
        window = EquipmentManager(self.stacked_widget)
        self.add_child_window(window)
        window.show()