"""Product Analytics Page — Product performance table and problem products."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QComboBox, QPushButton, QFrame, QHeaderView
)
from PySide6.QtCore import Qt


class ProductPage(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("📦 Product Analytics")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #ffffff;")
        header.addWidget(title)
        header.addStretch()

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Sort by Views", "Sort by Purchases", "Sort by Cart Rate", "Sort by Rating", "Sort by Returns"])
        self.sort_combo.currentTextChanged.connect(self._on_sort_change)
        self.sort_combo.setFixedWidth(180)
        header.addWidget(self.sort_combo)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh)
        refresh_btn.setFixedWidth(100)
        header.addWidget(refresh_btn)
        layout.addLayout(header)

        # Product table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Product", "Category", "Price", "Views", "Cart Adds",
            "Purchases", "View→Cart %", "Rating", "Returns"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table, stretch=2)

        # Problem products
        problem_card = QFrame()
        problem_card.setStyleSheet("QFrame { background: #22233d; border: 1px solid #2a2b4a; border-radius: 12px; padding: 16px; }")
        problem_layout = QVBoxLayout(problem_card)
        ptitle = QLabel("⚠️ Problem Products (High Views, Low Conversion)")
        ptitle.setStyleSheet("font-size: 14px; font-weight: bold; color: #f87171; background: transparent;")
        problem_layout.addWidget(ptitle)
        self.problem_label = QLabel("Loading...")
        self.problem_label.setStyleSheet("font-size: 13px; color: #a0a0c0; background: transparent; line-height: 1.6;")
        self.problem_label.setWordWrap(True)
        problem_layout.addWidget(self.problem_label)
        layout.addWidget(problem_card, stretch=1)

    def refresh(self):
        try:
            from src.analytics.sql_analytics import analytics
            sort_map = {
                "Sort by Views": "total_views", "Sort by Purchases": "total_purchases",
                "Sort by Cart Rate": "view_to_cart_rate", "Sort by Rating": "avg_rating",
                "Sort by Returns": "total_returns"
            }
            sort_by = sort_map.get(self.sort_combo.currentText(), "total_views")
            products = analytics.get_product_performance(limit=100, sort_by=sort_by)
            self._populate_table(products)

            problems = analytics.get_problem_products()
            if problems:
                lines = []
                for p in problems[:10]:
                    lines.append(f"  ⚠ {p['product_name'][:40]:40s}  Views: {p['total_views']}  Cart%: {float(p['view_to_cart_rate']):.1f}%  Rating: {float(p['avg_rating']):.1f}")
                self.problem_label.setText("\n".join(lines))
            else:
                self.problem_label.setText("  ✅ No products with critically low conversion detected.")
        except Exception as e:
            self.problem_label.setText(f"Error: {e}")

    def _populate_table(self, products):
        self.table.setRowCount(len(products) if products else 0)
        for i, p in enumerate(products or []):
            self.table.setItem(i, 0, QTableWidgetItem(str(p.get('product_name', ''))[:40]))
            self.table.setItem(i, 1, QTableWidgetItem(str(p.get('category_name', ''))))
            self.table.setItem(i, 2, QTableWidgetItem(f"₹{float(p.get('price', 0)):,.0f}"))
            self.table.setItem(i, 3, QTableWidgetItem(str(p.get('total_views', 0))))
            self.table.setItem(i, 4, QTableWidgetItem(str(p.get('total_cart_adds', 0))))
            self.table.setItem(i, 5, QTableWidgetItem(str(p.get('total_purchases', 0))))
            self.table.setItem(i, 6, QTableWidgetItem(f"{float(p.get('view_to_cart_rate', 0)):.1f}%"))
            self.table.setItem(i, 7, QTableWidgetItem(f"{float(p.get('avg_rating', 0)):.1f}"))
            self.table.setItem(i, 8, QTableWidgetItem(str(p.get('total_returns', 0))))

    def _on_sort_change(self):
        self.refresh()
