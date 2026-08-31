"""
Main Application Entry Point — PySide6 Desktop Application.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from src.gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("E-Commerce Customer Behavior Analytics")
    app.setOrganizationName("DBMS Project")

    # Set application-wide font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Set dark theme stylesheet
    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


STYLESHEET = """
/* ── Global ── */
QWidget {
    background-color: #1a1b2e;
    color: #e0e0e8;
    font-family: 'Segoe UI', sans-serif;
}

/* ── Main Window ── */
QMainWindow {
    background-color: #1a1b2e;
}

/* ── Sidebar ── */
#sidebar {
    background-color: #12132a;
    border-right: 1px solid #2a2b4a;
}

#sidebar QPushButton {
    background-color: transparent;
    color: #8888aa;
    border: none;
    border-radius: 8px;
    padding: 12px 16px;
    text-align: left;
    font-size: 13px;
    margin: 2px 8px;
}

#sidebar QPushButton:hover {
    background-color: #252648;
    color: #c0c0e0;
}

#sidebar QPushButton:checked, #sidebar QPushButton[active="true"] {
    background-color: #2d2e5e;
    color: #7c6ff7;
    font-weight: bold;
    border-left: 3px solid #7c6ff7;
}

/* ── Cards ── */
.card {
    background-color: #22233d;
    border: 1px solid #2a2b4a;
    border-radius: 12px;
    padding: 16px;
}

/* ── KPI Cards ── */
.kpi-card {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #252648, stop:1 #2d2e5e);
    border: 1px solid #3a3b6a;
    border-radius: 12px;
    padding: 16px;
}

.kpi-value {
    font-size: 28px;
    font-weight: bold;
    color: #ffffff;
}

.kpi-label {
    font-size: 12px;
    color: #8888aa;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.kpi-change-positive {
    color: #4ade80;
    font-size: 12px;
}

.kpi-change-negative {
    color: #f87171;
    font-size: 12px;
}

/* ── Tables ── */
QTableWidget, QTableView {
    background-color: #1e1f38;
    border: 1px solid #2a2b4a;
    border-radius: 8px;
    gridline-color: #2a2b4a;
    selection-background-color: #3d3e6e;
    alternate-background-color: #22233d;
}

QHeaderView::section {
    background-color: #252648;
    color: #a0a0c0;
    border: none;
    border-bottom: 2px solid #7c6ff7;
    padding: 8px;
    font-weight: bold;
    font-size: 12px;
}

QTableWidget::item {
    padding: 6px;
    border-bottom: 1px solid #2a2b4a;
}

/* ── Buttons ── */
QPushButton {
    background-color: #7c6ff7;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #6a5ce8;
}

QPushButton:pressed {
    background-color: #5a4cd0;
}

QPushButton:disabled {
    background-color: #3a3b5a;
    color: #666680;
}

QPushButton.secondary {
    background-color: #2d2e5e;
    color: #c0c0e0;
    border: 1px solid #3a3b6a;
}

QPushButton.secondary:hover {
    background-color: #3d3e6e;
}

QPushButton.danger {
    background-color: #dc2626;
}

QPushButton.danger:hover {
    background-color: #b91c1c;
}

QPushButton.success {
    background-color: #16a34a;
}

/* ── Severity Badges ── */
.severity-critical {
    background-color: #dc2626;
    color: white;
    border-radius: 4px;
    padding: 2px 8px;
    font-weight: bold;
    font-size: 11px;
}

.severity-high {
    background-color: #ea580c;
    color: white;
    border-radius: 4px;
    padding: 2px 8px;
    font-weight: bold;
    font-size: 11px;
}

.severity-medium {
    background-color: #ca8a04;
    color: white;
    border-radius: 4px;
    padding: 2px 8px;
    font-weight: bold;
    font-size: 11px;
}

.severity-low {
    background-color: #2563eb;
    color: white;
    border-radius: 4px;
    padding: 2px 8px;
    font-weight: bold;
    font-size: 11px;
}

/* ── Inputs ── */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #22233d;
    color: #e0e0e8;
    border: 1px solid #3a3b6a;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
}

QLineEdit:focus, QComboBox:focus {
    border-color: #7c6ff7;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

/* ── Scroll Bars ── */
QScrollBar:vertical {
    background-color: #1a1b2e;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #3a3b6a;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #7c6ff7;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* ── Tabs ── */
QTabWidget::pane {
    border: 1px solid #2a2b4a;
    border-radius: 8px;
    background-color: #1e1f38;
}

QTabBar::tab {
    background-color: #22233d;
    color: #8888aa;
    border: none;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
}

QTabBar::tab:selected {
    background-color: #1e1f38;
    color: #7c6ff7;
    font-weight: bold;
    border-bottom: 2px solid #7c6ff7;
}

/* ── Labels ── */
.page-title {
    font-size: 22px;
    font-weight: bold;
    color: #ffffff;
}

.section-title {
    font-size: 16px;
    font-weight: bold;
    color: #c0c0e0;
}

/* ── Status Bar ── */
QStatusBar {
    background-color: #12132a;
    color: #8888aa;
    border-top: 1px solid #2a2b4a;
}

/* ── Group Box ── */
QGroupBox {
    border: 1px solid #2a2b4a;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
    color: #c0c0e0;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}

/* ── Progress Bar ── */
QProgressBar {
    background-color: #22233d;
    border: none;
    border-radius: 6px;
    height: 8px;
    text-align: center;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c6ff7, stop:1 #a78bfa);
    border-radius: 6px;
}

/* ── Tool Tips ── */
QToolTip {
    background-color: #2d2e5e;
    color: #e0e0e8;
    border: 1px solid #3a3b6a;
    border-radius: 4px;
    padding: 4px 8px;
}
"""


if __name__ == "__main__":
    main()
