from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGridLayout,
    QPushButton, QFrame, QStackedWidget
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

class ModifyPage(QWidget):
    def __init__(self, stacked_widget: QStackedWidget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.setup_ui()
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f6fa;
                color: #2d3436;
            }
        """)

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(30)

        # Title
        title = QLabel("Network Configuration Manager")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #0984e3;")
        main_layout.addWidget(title)

        # Configuration Cards Grid
        grid_layout = QGridLayout()
        grid_layout.setSpacing(20)
        grid_layout.setContentsMargins(20, 20, 20, 20)

        card_data = [
            ("VRF Configuration", self.goto_create_vrf, "#74b9ff"),
            ("BGP Configuration", self.goto_implement_bgp, "#74b9ff"),
            ("MPLS Configuration", self.goto_implement_mpls, "#74b9ff"),
            ("OSPF Configuration", self.goto_ospf, "#74b9ff"),
            ("IS-IS Configuration", self.goto_isis, "#74b9ff"),
            ("View Configurations", self.goto_config, "#74b9ff")
        ]

        for i, (title, handler, color) in enumerate(card_data):
            card = self.create_card(title, handler, color)
            row, col = divmod(i, 3)
            grid_layout.addWidget(card, row, col)

        grid_wrapper = QWidget()
        grid_wrapper.setLayout(grid_layout)
        main_layout.addWidget(grid_wrapper)
        self.setLayout(main_layout)

    def create_card(self, title: str, handler, color: str):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 12px;
                padding: 20px;
            }}
            QLabel {{
                color: white;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton {{
                background-color: white;
                color: {color};
                border: 2px solid white;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
                margin-top: 15px;
            }}
            QPushButton:hover {{
                background-color: {color};
                color: white;
            }}
        """)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel(title)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        button = QPushButton("Configure")
        button.clicked.connect(handler)
        button.setCursor(Qt.CursorShape.PointingHandCursor)

        layout.addWidget(label)
        layout.addWidget(button)
        card.setLayout(layout)
        return card

    def goto_create_vrf(self):
        from frontend.vrf_config import VRFConfig
        self.vrf_window = VRFConfig()
        self.vrf_window.show()

    def goto_implement_bgp(self):
        from frontend.implement_bgp import ImplementBGPPage
        self.bgp_window = ImplementBGPPage()
        self.bgp_window.show()

    def goto_implement_mpls(self):
        from frontend.implement_mpls import MPLSPage
        self.mpls_window = MPLSPage()
        self.mpls_window.show()

    def goto_ospf(self):
        from frontend.ospf import OSPFConfig
        self.ospf_window = OSPFConfig()
        self.ospf_window.show()

    def goto_isis(self):
        from frontend.isis import ISISConfig
        self.isis_window = ISISConfig()
        self.isis_window.show()

    def goto_config(self):
        from frontend.config import ConfigPage
        self.config_window = ConfigPage()
        self.config_window.show()