"""Customer Analytics Page — RFM segments, customer list, customer detail."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QComboBox, QPushButton, QFrame, QScrollArea, QHeaderView
)
from PySide6.QtCore import Qt


class CustomerPage(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel("👥 Customer Analytics")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #ffffff;")
        header.addWidget(title)
        header.addStretch()

        self.segment_filter = QComboBox()
        self.segment_filter.addItems(["All Segments", "VIP", "Loyal", "Potential", "New", "Regular", "At Risk", "Churned"])
        self.segment_filter.currentTextChanged.connect(self._on_filter_change)
        self.segment_filter.setFixedWidth(160)
        header.addWidget(self.segment_filter)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh)
        refresh_btn.setFixedWidth(100)
        header.addWidget(refresh_btn)
        layout.addLayout(header)

        # Segment summary
        self.segment_summary = QLabel("Loading segment data...")
        self.segment_summary.setStyleSheet("font-size: 13px; color: #a0a0c0; line-height: 1.6;")
        self.segment_summary.setWordWrap(True)
        layout.addWidget(self.segment_summary)

        # Customer table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Code", "Segment", "Lifetime Value", "City", "Age Group", "Gender", "Channel"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.itemSelectionChanged.connect(self._on_select)
        layout.addWidget(self.table, stretch=2)

        # Customer detail panel
        self.detail_frame = QFrame()
        self.detail_frame.setStyleSheet("QFrame { background: #22233d; border: 1px solid #2a2b4a; border-radius: 12px; padding: 16px; }")
        detail_layout = QVBoxLayout(self.detail_frame)
        detail_title = QLabel("Customer Details")
        detail_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #c0c0e0; background: transparent;")
        detail_layout.addWidget(detail_title)
        self.detail_label = QLabel("Select a customer from the table above to see details.")
        self.detail_label.setStyleSheet("font-size: 13px; color: #a0a0c0; background: transparent; line-height: 1.6;")
        self.detail_label.setWordWrap(True)
        detail_layout.addWidget(self.detail_label)
        layout.addWidget(self.detail_frame, stretch=1)

    def refresh(self):
        try:
            from src.analytics.sql_analytics import analytics

            # Segment summary
            segments = analytics.get_rfm_segments()
            if segments:
                total = sum(int(s['count']) for s in segments)
                lines = [f"Total Customers: {total:,}\n"]
                for s in segments:
                    pct = int(s['count']) / max(total, 1) * 100
                    bar = "█" * int(pct / 3) + "░" * (33 - int(pct / 3))
                    lines.append(f"  {s['segment']:12s}  {bar}  {int(s['count']):>5}  ({pct:.1f}%)  Avg LTV: ₹{float(s['avg_ltv']):,.0f}")
                self.segment_summary.setText("\n".join(lines))

            # Customer list
            segment = self.segment_filter.currentText()
            seg_param = None if segment == "All Segments" else segment
            customers = analytics.get_customer_list(segment=seg_param, limit=200)
            self._populate_table(customers)

        except Exception as e:
            self.segment_summary.setText(f"Error: {e}")

    def _populate_table(self, customers):
        self.table.setRowCount(len(customers) if customers else 0)
        for i, c in enumerate(customers or []):
            self.table.setItem(i, 0, QTableWidgetItem(str(c.get('customer_id', ''))))
            self.table.setItem(i, 1, QTableWidgetItem(str(c.get('customer_code', ''))))
            
            seg_item = QTableWidgetItem(str(c.get('segment', '')))
            seg_colors = {'VIP': '#a78bfa', 'Loyal': '#4ade80', 'At Risk': '#f87171', 'Churned': '#ef4444', 'New': '#60a5fa'}
            seg_item.setForeground(Qt.GlobalColor.white)
            self.table.setItem(i, 2, seg_item)
            
            ltv = float(c.get('lifetime_value', 0))
            self.table.setItem(i, 3, QTableWidgetItem(f"₹{ltv:,.0f}"))
            self.table.setItem(i, 4, QTableWidgetItem(str(c.get('city', ''))))
            self.table.setItem(i, 5, QTableWidgetItem(str(c.get('age_group', ''))))
            self.table.setItem(i, 6, QTableWidgetItem(str(c.get('gender', ''))))
            self.table.setItem(i, 7, QTableWidgetItem(str(c.get('preferred_channel', ''))))

    def _on_filter_change(self, text):
        self.refresh()

    def _on_select(self):
        rows = self.table.selectionModel().selectedRows()
        if rows:
            row = rows[0].row()
            cust_id = self.table.item(row, 0).text()
            self._load_detail(int(cust_id))

    def _load_detail(self, customer_id):
        try:
            from src.analytics.sql_analytics import analytics
            detail = analytics.get_customer_detail(customer_id)
            events = analytics.get_customer_events(customer_id, limit=10)

            if detail:
                d = detail[0]
                text = (
                    f"Customer: {d.get('customer_code', 'N/A')}  |  Segment: {d.get('segment', 'N/A')}  |  LTV: ₹{float(d.get('lifetime_value', 0)):,.0f}\n\n"
                    f"  Sessions: {d.get('total_sessions', 0)}  |  Events: {d.get('total_events', 0)}  |  Orders: {d.get('total_orders', 0)}\n"
                    f"  Spent: ₹{float(d.get('total_spent', 0)):,.0f}  |  Reviews: {d.get('total_reviews', 0)}  |  Returns: {d.get('total_returns', 0)}\n"
                    f"  Abandoned Carts: {d.get('abandoned_carts', 0)}  |  Last Order: {d.get('last_order_date', 'Never')}\n"
                )

                if events:
                    text += "\nRecent Activity:\n"
                    for ev in events[:8]:
                        prod = ev.get('product_name', '')[:30] if ev.get('product_name') else ''
                        text += f"  {ev['event_timestamp']}  {ev['event_type']:20s}  {prod}\n"

                self.detail_label.setText(text)
            else:
                self.detail_label.setText("No detail found.")

        except Exception as e:
            self.detail_label.setText(f"Error: {e}")
