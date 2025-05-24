from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, 
    QListWidget, QFrame, QGridLayout, QPushButton, QGroupBox, 
    QMessageBox, QInputDialog,QLineEdit
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from backend.monitor import fetch_routers, validate_router_credentials, handle_logout_request, fetch_full_logs, validate_admin
from frontend.stats_page import StatsWindow
from frontend.modify import ModifyPage
from frontend.manage_equipment import EquipmentManager
from datetime import datetime
from bson import ObjectId

class LogEntrySection(QGroupBox):
    def __init__(self, log_data, parent=None):
        super().__init__(parent)
        self.log_data = log_data
        self.setup_ui()
        
    def setup_ui(self):
        self.setStyleSheet("""
            QGroupBox {
                background-color: #ffffff;
                border: 2px solid #74b9ff;
                border-radius: 8px;
                margin: 10px;
                padding: 15px;
            }
            QLabel {
                color: #2d3436;
                font-size: 14px;
                margin: 4px 0;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Display ObjectID header
        obj_id = str(self.log_data.get('_id', ''))
        id_label = QLabel(f"Document ID: {obj_id}")
        id_label.setStyleSheet("font-weight: bold; color: #0984e3; font-size: 16px;")
        layout.addWidget(id_label)
        
        # Display all fields
        for key, value in self.log_data.items():
            if key == '_id':
                continue
                
            field_layout = QHBoxLayout()
            
            key_label = QLabel(f"{key.capitalize()}:")
            key_label.setStyleSheet("min-width: 120px;")
            
            value_label = QLabel(self.format_value(key, value))
            
            field_layout.addWidget(key_label)
            field_layout.addWidget(value_label)
            layout.addLayout(field_layout)
        
        self.setLayout(layout)
    
    def format_value(self, key, value):
        if key == 'timestamp':
            return value.strftime("%Y-%m-%d %H:%M:%S") if value else "N/A"
        if key == 'networks':
            return self.format_networks(value)
        if isinstance(value, ObjectId):
            return str(value)
        if isinstance(value, list):
            return ", ".join(map(str, value))
        return str(value)
    
    def format_networks(self, networks):
        if not isinstance(networks, list):
            return "N/A"
        return "\n".join([f"{n.get('network', '?')}/{n.get('mask', '?')} (Area {n.get('area', '?')})" for n in networks])

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
        self.admin_clicks = 0
        self.setup_ui()
        self.setup_hidden_logs()
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

    def setup_hidden_logs(self):
        """Initialize hidden logs container"""
        self.log_scroll = QScrollArea()
        self.log_scroll.setWidgetResizable(True)
        self.log_scroll.setStyleSheet("border: none; background: transparent;")
        
        self.log_container = QWidget()
        self.log_layout = QVBoxLayout()
        self.log_container.setLayout(self.log_layout)
        
        self.log_scroll.setWidget(self.log_container)
        self.log_scroll.hide()
        self.layout().addWidget(self.log_scroll)

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

    def mousePressEvent(self, event):
        """Hidden activation: Triple right-click"""
        if event.button() == Qt.MouseButton.RightButton:
            self.admin_clicks += 1
            if self.admin_clicks == 3:
                self.verify_admin_access()
            QTimer.singleShot(2000, self.reset_admin_counter)

    def reset_admin_counter(self):
        self.admin_clicks = 0

    def verify_admin_access(self):
        """Admin password verification"""
        password, ok = QInputDialog.getText(
            self, "Admin Access", 
            "Enter admin password:", 
            QLineEdit.EchoMode.Password
        )
        
        if ok and validate_admin(password):
            self.show_logs_interface()
        else:
            QMessageBox.warning(self, "Access Denied", "Incorrect password")

    def show_logs_interface(self):
        """Display all log entries in individual sections"""
        try:
            # Clear previous logs
            while self.log_layout.count():
                item = self.log_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Load and display new logs
            logs = fetch_full_logs()
            if not logs:
                QMessageBox.information(self, "Info", "No logs found in database")
                return
                
            for log in logs:
                log_section = LogEntrySection(log)
                self.log_layout.addWidget(log_section)
            
            self.log_layout.addStretch()
            self.log_scroll.show()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load logs: {str(e)}")

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