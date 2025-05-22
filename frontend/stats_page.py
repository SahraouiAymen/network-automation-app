from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGridLayout, 
    QHBoxLayout, QPushButton, QGroupBox, QFrame,
    QMessageBox
)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from backend.Router_stats import get_router_stats

class StatsWindow(QWidget):
    update_error = pyqtSignal(str)
    
    def __init__(self, router_name, host, username, password, parent=None):
        super().__init__(parent)
        self.router_name = router_name
        self.host = host  # Now accepts hostnames
        self.credentials = (username, password)
        
        self.setWindowTitle(f"{router_name} Statistics")
        self.setGeometry(200, 100, 800, 650)
        
        # Data storage
        self.cpu_data = []
        self.memory_data = []
        self.max_points = 20
        self.last_uptime = "N/A"
        
        # UI elements
        self.init_ui()
        self.setup_charts()
        self.start_monitoring()

        self.update_error.connect(self.show_error_message)

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header with status
        header = QHBoxLayout()
        self.status_label = QLabel("◌ Connecting...")
        self.status_label.setFont(QFont("Arial", 10))
        
        self.title = QLabel(f"Router Monitoring: {self.router_name}")
        self.title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        
        self.btn_back = QPushButton("← Back")
        self.btn_back.clicked.connect(self.close)
        
        header.addWidget(self.btn_back)
        header.addWidget(self.title)
        header.addWidget(self.status_label)
        main_layout.addLayout(header)

        # Charts grid
        grid = QGridLayout()
        self.cpu_group = self.create_chart_box("CPU Usage", "%", "#3498db")
        self.mem_group = self.create_chart_box("Memory Usage", "%", "#2ecc71")
        grid.addWidget(self.cpu_group, 0, 0)
        grid.addWidget(self.mem_group, 0, 1)
        
        # Uptime display
        uptime_frame = QFrame()
        uptime_layout = QHBoxLayout()
        uptime_layout.setContentsMargins(15, 10, 15, 10)
        
        self.uptime_label = QLabel("Uptime: Initializing...")
        self.uptime_label.setFont(QFont("Arial", 12))
        self.uptime_label.setStyleSheet("color: #7f8c8d;")
        uptime_layout.addWidget(self.uptime_label)
        
        uptime_frame.setLayout(uptime_layout)
        grid.addWidget(uptime_frame, 1, 0, 1, 2)
        
        main_layout.addLayout(grid)
        self.setLayout(main_layout)
        self.apply_styles()

    def create_chart_box(self, title, unit, color):
        box = QGroupBox(title)
        layout = QVBoxLayout()
        
        # Value display
        lbl = QLabel("--")
        lbl.setObjectName("value_label")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {color}; margin-bottom: 10px;")
        
        # Chart setup
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.set_facecolor("#f5f6fa")
        ax.tick_params(colors="#2d3436")
        ax.set_ylim(0, 100)
        ax.set_xlim(0, self.max_points)
        
        canvas = FigureCanvas(fig)
        canvas.setStyleSheet("background: transparent;")
        
        layout.addWidget(lbl)
        layout.addWidget(canvas)
        box.setLayout(layout)
        return box

    def setup_charts(self):
        # Initialize CPU chart
        self.cpu_ax = self.cpu_group.findChild(FigureCanvas).figure.axes[0]
        self.cpu_line, = self.cpu_ax.plot([], [], color="#3498db")
        
        # Initialize Memory chart
        self.mem_ax = self.mem_group.findChild(FigureCanvas).figure.axes[0]
        self.mem_line, = self.mem_ax.plot([], [], color="#2ecc71")

    def start_monitoring(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.safe_update)
        self.timer.start(15000)  # 15 seconds
        self.safe_update()  # Initial update

    def safe_update(self):
        try:
            stats = get_router_stats(self.host, *self.credentials)
            if stats.get('error'):
                raise Exception(stats['error'])
                
            self.process_stats(stats)
            self.status_label.setText("◌ Connected")
            self.status_label.setStyleSheet("color: #27ae60;")
        except Exception as e:
            self.handle_error(str(e))
            self.status_label.setText("◌ Connection Error")
            self.status_label.setStyleSheet("color: #e74c3c;")

    def process_stats(self, stats):
        """Update all stats with validation"""
        # CPU
        if stats.get('cpu') is not None and 0 <= stats['cpu'] <= 100:
            self.update_dataset(self.cpu_data, stats['cpu'])
            self.update_cpu_chart()
        
        # Memory
        if stats.get('memory') is not None and 0 <= stats['memory'] <= 100:
            self.update_dataset(self.memory_data, stats['memory'])
            self.update_mem_chart()
        
        # Uptime
        uptime = stats.get('uptime', "N/A")
        if uptime != "N/A":
            self.last_uptime = uptime
        self.uptime_label.setText(f"Uptime: {self.last_uptime}")

    def update_dataset(self, dataset, value):
        """Maintain rolling data window"""
        dataset.append(value)
        if len(dataset) > self.max_points:
            dataset.pop(0)

    def update_cpu_chart(self):
        """Update CPU chart specifically"""
        value_label = self.cpu_group.findChild(QLabel, "value_label")
        canvas = self.cpu_group.findChild(FigureCanvas)
        
        if self.cpu_data:
            value_label.setText(f"{self.cpu_data[-1]:.1f}%")
            self.cpu_line.set_data(range(len(self.cpu_data)), self.cpu_data)
            self.cpu_ax.relim()
            self.cpu_ax.autoscale_view(True, True, True)
            canvas.draw_idle()

    def update_mem_chart(self):
        """Update Memory chart specifically"""
        value_label = self.mem_group.findChild(QLabel, "value_label")
        canvas = self.mem_group.findChild(FigureCanvas)
        
        if self.memory_data:
            value_label.setText(f"{self.memory_data[-1]:.1f}%")
            self.mem_line.set_data(range(len(self.memory_data)), self.memory_data)
            self.mem_ax.relim()
            self.mem_ax.autoscale_view(True, True, True)
            canvas.draw_idle()

    def handle_error(self, message):
        """Handle error states"""
        self.update_error.emit(message)
        self.uptime_label.setText(f"Uptime: {self.last_uptime} (Last Known)")

    def show_error_message(self, message):
        """Enhanced error diagnostics with hostname support"""
        if "DNS resolution" in message:
            guidance = (f"Hostname resolution failed for '{self.host}':\n"
                       "1. Verify the device name is correct\n"
                       "2. Check DNS/hosts file configuration\n"
                       "3. Try using the IP address instead")
        elif "Connection failed" in message:
            guidance = ("Connection attempt failed:\n"
                       "1. Verify device is reachable\n"
                       "2. Check SSH port (22) accessibility\n"
                       "3. Validate credentials")
        else:
            guidance = "Check network configuration and try again"

        QMessageBox.critical(
            self,
            "Connection Error",
            f"{message}\n\n{guidance}",
            QMessageBox.StandardButton.Ok
        )

    def apply_styles(self):
        self.setStyleSheet("""
            QGroupBox {
                border: 2px solid #ecf0f1;
                border-radius: 8px;
                padding-top: 20px;
                margin-top: 10px;
            }
            QGroupBox::title {
                color: #2c3e50;
                font-weight: bold;
                padding: 0 8px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QFrame {
                background-color: #f8f9fa;
                border-radius: 6px;
            }
        """)

    def closeEvent(self, event):
        self.timer.stop()
        super().closeEvent(event)