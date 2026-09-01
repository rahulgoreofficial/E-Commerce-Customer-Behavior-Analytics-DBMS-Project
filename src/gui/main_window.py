"""
Main Window — Sidebar navigation + stacked content area.
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QStackedWidget, QLabel, QStatusBar, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QIcon
from src.gui.pages.dashboard_page import DashboardPage
from src.gui.pages.customer_page import CustomerPage
from src.gui.pages.product_page import ProductPage
from src.gui.pages.funnel_page import FunnelPage
from src.gui.pages.reviews_page import ReviewsPage
from src.gui.pages.problems_page import ProblemsPage
from src.gui.pages.predictions_page import PredictionsPage
from src.gui.pages.simulator_page import SimulatorPage
from src.database.connection import db


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("E-Commerce Customer Behavior Analytics — Decision Support System")
        self.setMinimumSize(1280, 800)
        self.showMaximized()

        # Test DB connection
        if not db.test_connection():
            QMessageBox.warning(self, "Database Error",
                "Could not connect to PostgreSQL.\n\n"
                "Make sure PostgreSQL is running and the database 'ecom_analytics' exists.\n"
                "Check src/config.py for connection settings.\n\n"
                "The application will start but data won't load.")

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Sidebar ──
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 16, 0, 16)
        sidebar_layout.setSpacing(4)

        # App title
        title_label = QLabel("  📊 ECOM Analytics")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #7c6ff7; padding: 8px 16px; margin-bottom: 8px;")
        sidebar_layout.addWidget(title_label)

        subtitle = QLabel("  Decision Support System")
        subtitle.setStyleSheet("font-size: 10px; color: #666680; padding: 0 16px; margin-bottom: 16px;")
        sidebar_layout.addWidget(subtitle)

        # Navigation buttons
        self.nav_buttons = []
        pages_config = [
            ("📈  Dashboard", 0),
            ("👥  Customers", 1),
            ("📦  Products", 2),
            ("🔄  Funnel", 3),
            ("💬  Reviews", 4),
            ("⚠️  Problems", 5),
            ("🔮  Predictions", 6),
            ("⚡  Simulator", 7),
        ]

        for label, idx in pages_config:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setProperty("page_index", idx)
            btn.clicked.connect(lambda checked, i=idx: self.navigate_to(i))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sidebar_layout.addStretch()

        # DB status
        self.db_status = QLabel("  ● Connected" if db.test_connection() else "  ○ Disconnected")
        self.db_status.setStyleSheet(
            "color: #4ade80; font-size: 11px; padding: 8px 16px;" if db.test_connection()
            else "color: #f87171; font-size: 11px; padding: 8px 16px;"
        )
        sidebar_layout.addWidget(self.db_status)

        main_layout.addWidget(sidebar)

        # ── Content Area ──
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("QStackedWidget { background-color: #1a1b2e; }")
        
        # Add pages
        self.dashboard_page = DashboardPage()
        self.customer_page = CustomerPage()
        self.product_page = ProductPage()
        self.funnel_page = FunnelPage()
        self.reviews_page = ReviewsPage()
        self.problems_page = ProblemsPage()
        self.predictions_page = PredictionsPage()
        self.simulator_page = SimulatorPage()

        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.customer_page)
        self.stack.addWidget(self.product_page)
        self.stack.addWidget(self.funnel_page)
        self.stack.addWidget(self.reviews_page)
        self.stack.addWidget(self.problems_page)
        self.stack.addWidget(self.predictions_page)
        self.stack.addWidget(self.simulator_page)

        main_layout.addWidget(self.stack)

        # Status bar
        self.statusBar().showMessage("Ready")

        # Default to dashboard
        self.navigate_to(0)

    def navigate_to(self, index):
        """Switch to a page and update sidebar selection."""
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
            btn.setProperty("active", "true" if i == index else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # Refresh the page when navigated to
        page = self.stack.widget(index)
        if hasattr(page, 'refresh'):
            page.refresh()
