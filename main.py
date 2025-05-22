import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from frontend.login import LoginWindow
from frontend.monitor import MonitorPage

class MainApplication(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Network Configuration Tool")
        self.setGeometry(100, 100, 1300, 700)
        
        
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
       
        self.login_page = LoginWindow(self.on_login_success)
        self.stacked_widget.addWidget(self.login_page)
        
        
        self.stacked_widget.setCurrentWidget(self.login_page)

    def handle_logout(self):
        self.stacked_widget.setCurrentIndex(0)
        if hasattr(self, 'monitor_page'):
            self.monitor_page.deleteLater()
            del self.monitor_page

    def on_login_success(self):
        print("Login successful, switching to monitor page")
        # Create and add monitor page
        self.monitor_page = MonitorPage(self.stacked_widget)
        # Connect logout signal to handler
        self.monitor_page.logout_requested.connect(self.handle_logout)
        self.stacked_widget.addWidget(self.monitor_page)
        self.stacked_widget.setCurrentWidget(self.monitor_page)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainApplication()
    main_window.show()
    sys.exit(app.exec())