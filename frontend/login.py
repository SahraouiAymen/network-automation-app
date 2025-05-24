from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, 
    QVBoxLayout,QGroupBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from backend.Connect import authenticate_user

class LoginWindow(QWidget):
    def __init__(self, on_success_callback):
        super().__init__()
        self.on_success_callback = on_success_callback
        self.setup_ui()
        self.setup_styles()

    def setup_ui(self):
        self.setWindowTitle("Network Manager")
        self.setMinimumSize(800, 800)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(30)

        # Security branding
        self.add_security_branding(main_layout)
        
        # Login form
        form_group = QGroupBox("Login")
        form_layout = QVBoxLayout()
        
        self.username_input = self.create_input_field("Username")
        self.password_input = self.create_input_field("Password", is_password=True)
        
        form_layout.addWidget(QLabel("Username:"))
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(QLabel("Password:"))
        form_layout.addWidget(self.password_input)
        
        auth_btn = self.create_auth_button()
        form_layout.addWidget(auth_btn)
        
        form_group.setLayout(form_layout)
        main_layout.addWidget(form_group)
        self.setLayout(main_layout)

    def setup_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                font-family: 'Segoe UI';
            }
            QGroupBox {
                border: 2px solid #4a90e2;
                border-radius: 15px;
                padding: 25px;
                margin-top: 20px;
                font-size: 16px;
                color: #2c3e50;
            }
            QLineEdit {
                border: 2px solid #ced4da;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #4a90e2;
            }
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 14px 28px;
                font-size: 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
        """)

    def add_security_branding(self, layout):
        
        title = QLabel("Automation Of Network Configuration")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #74b9ff; margin-bottom: 25px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(title)

    def create_input_field(self, placeholder, is_password=False):
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        field.setMinimumHeight(45)
        if is_password:
            field.setEchoMode(QLineEdit.EchoMode.Password)
            field.setProperty("passwordField", True)
        return field

    def create_auth_button(self):
        btn = QPushButton("Login")
        btn.clicked.connect(self.validate_login)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumSize(180, 50)
        return btn

    def validate_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not all([username, password]):
            self.show_error("Validation Error", 
                "All fields must be completed")
            return

        self.on_success_callback()


