"""Dashboard Page — KPI cards, revenue trend, funnel overview, segment distribution."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
    QFrame, QPushButton, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import traceback


class KPICard(QFrame):
    """A single KPI metric card."""
    def __init__(self, title, value="--", change="", positive=True):
        super().__init__()
        self.setProperty("class", "kpi-card")
        self.setStyleSheet("""
            KPICard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #252648, stop:1 #2d2e5e);
                border: 1px solid #3a3b6a; border-radius: 12px; padding: 16px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 11px; color: #8888aa; text-transform: uppercase; letter-spacing: 1px; background: transparent;")
        layout.addWidget(self.title_label)

        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet("font-size: 26px; font-weight: bold; color: #ffffff; background: transparent;")
        layout.addWidget(self.value_label)

        self.change_label = QLabel(change)
        color = "#4ade80" if positive else "#f87171"
        self.change_label.setStyleSheet(f"font-size: 11px; color: {color}; background: transparent;")
        layout.addWidget(self.change_label)

    def update_values(self, value, change="", positive=True):
        self.value_label.setText(str(value))
        self.change_label.setText(change)
        color = "#4ade80" if positive else "#f87171"
        self.change_label.setStyleSheet(f"font-size: 11px; color: {color}; background: transparent;")


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        self._initialized = False
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        title = QLabel("📈 Dashboard")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #ffffff;")
        header.addWidget(title)
        header.addStretch()

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh)
        self.refresh_btn.setFixedWidth(120)
        header.addWidget(self.refresh_btn)
        layout.addLayout(header)

        # KPI Row
        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(16)
        self.kpi_revenue = KPICard("REVENUE (7 DAYS)", "₹0")
        self.kpi_orders = KPICard("ORDERS", "0")
        self.kpi_customers = KPICard("ACTIVE CUSTOMERS", "0")
        self.kpi_conversion = KPICard("CONVERSION RATE", "0%")
        self.kpi_abandonment = KPICard("CART ABANDONMENT", "0%", positive=False)

        kpi_grid.addWidget(self.kpi_revenue, 0, 0)
        kpi_grid.addWidget(self.kpi_orders, 0, 1)
        kpi_grid.addWidget(self.kpi_customers, 0, 2)
        kpi_grid.addWidget(self.kpi_conversion, 0, 3)
        kpi_grid.addWidget(self.kpi_abandonment, 0, 4)
        layout.addLayout(kpi_grid)

        # Info sections
        info_row = QHBoxLayout()
        info_row.setSpacing(16)

        # Segment Distribution
        seg_card = QFrame()
        seg_card.setStyleSheet("QFrame { background: #22233d; border: 1px solid #2a2b4a; border-radius: 12px; padding: 16px; }")
        seg_layout = QVBoxLayout(seg_card)
        seg_title = QLabel("Customer Segments")
        seg_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #c0c0e0; background: transparent;")
        seg_layout.addWidget(seg_title)
        self.segment_info = QLabel("Loading...")
        self.segment_info.setStyleSheet("font-size: 13px; color: #a0a0c0; background: transparent; line-height: 1.6;")
        self.segment_info.setWordWrap(True)
        seg_layout.addWidget(self.segment_info)
        seg_layout.addStretch()
        info_row.addWidget(seg_card)

        # Funnel Overview
        funnel_card = QFrame()
        funnel_card.setStyleSheet("QFrame { background: #22233d; border: 1px solid #2a2b4a; border-radius: 12px; padding: 16px; }")
        funnel_layout = QVBoxLayout(funnel_card)
        funnel_title = QLabel("Conversion Funnel (30 Days)")
        funnel_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #c0c0e0; background: transparent;")
        funnel_layout.addWidget(funnel_title)
        self.funnel_info = QLabel("Loading...")
        self.funnel_info.setStyleSheet("font-size: 13px; color: #a0a0c0; background: transparent; line-height: 1.6;")
        self.funnel_info.setWordWrap(True)
        funnel_layout.addWidget(self.funnel_info)
        funnel_layout.addStretch()
        info_row.addWidget(funnel_card)

        # Table Sizes
        db_card = QFrame()
        db_card.setStyleSheet("QFrame { background: #22233d; border: 1px solid #2a2b4a; border-radius: 12px; padding: 16px; }")
        db_layout = QVBoxLayout(db_card)
        db_title = QLabel("Database Status")
        db_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #c0c0e0; background: transparent;")
        db_layout.addWidget(db_title)
        self.db_info = QLabel("Loading...")
        self.db_info.setStyleSheet("font-size: 13px; color: #a0a0c0; background: transparent; line-height: 1.6;")
        self.db_info.setWordWrap(True)
        db_layout.addWidget(self.db_info)
        db_layout.addStretch()
        info_row.addWidget(db_card)

        layout.addLayout(info_row)

        # Recent Problems Preview
        problems_card = QFrame()
        problems_card.setStyleSheet("QFrame { background: #22233d; border: 1px solid #2a2b4a; border-radius: 12px; padding: 16px; }")
        problems_layout = QVBoxLayout(problems_card)
        problems_title = QLabel("⚠️ Detected Problems")
        problems_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #c0c0e0; background: transparent;")
        problems_layout.addWidget(problems_title)
        self.problems_info = QLabel("Loading...")
        self.problems_info.setStyleSheet("font-size: 13px; color: #a0a0c0; background: transparent; line-height: 1.8;")
        self.problems_info.setWordWrap(True)
        problems_layout.addWidget(self.problems_info)
        layout.addWidget(problems_card)

        layout.addStretch()
        scroll.setWidget(content)

        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)

    def refresh(self):
        """Load data from database."""
        try:
            from src.analytics.sql_analytics import analytics

            # KPIs
            kpis = analytics.get_dashboard_kpis(7)
            if kpis:
                k = kpis[0]
                revenue = float(k.get('revenue', 0))
                orders = int(k.get('orders', 0))
                customers = int(k.get('customers', 0))
                conv_rate = float(k.get('conversion_rate', 0))
                aband_rate = float(k.get('abandonment_rate', 0))
                prev_revenue = float(k.get('prev_revenue', 0))

                rev_change = ((revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
                self.kpi_revenue.update_values(f"₹{revenue:,.0f}", f"{'▲' if rev_change >= 0 else '▼'} {abs(rev_change):.1f}% vs prev week", rev_change >= 0)
                self.kpi_orders.update_values(str(orders))
                self.kpi_customers.update_values(str(customers))
                self.kpi_conversion.update_values(f"{conv_rate:.1f}%")
                self.kpi_abandonment.update_values(f"{aband_rate:.1f}%", "", aband_rate < 70)

            # Segments
            segments = analytics.get_rfm_segments()
            if segments:
                seg_text = "\n".join([f"  {s['segment']:12s}  —  {s['count']} customers  (Avg LTV: ₹{float(s['avg_ltv']):,.0f})" for s in segments])
                self.segment_info.setText(seg_text)
            else:
                self.segment_info.setText("No segment data available. Run seed data first.")

            # Funnel
            funnel = analytics.get_funnel_data(30)
            if funnel:
                f = funnel[0]
                views = int(f.get('view_sessions', 0))
                carts = int(f.get('cart_sessions', 0))
                checkouts = int(f.get('checkout_sessions', 0))
                purchases = int(f.get('purchase_sessions', 0))
                self.funnel_info.setText(
                    f"  👁  Views:      {views:,}\n"
                    f"  🛒 Cart:       {carts:,}  ({carts/max(views,1)*100:.1f}%)\n"
                    f"  💳 Checkout:   {checkouts:,}  ({checkouts/max(carts,1)*100:.1f}%)\n"
                    f"  ✅ Purchase:   {purchases:,}  ({purchases/max(checkouts,1)*100:.1f}%)\n"
                    f"\n  Overall: {purchases/max(views,1)*100:.2f}%"
                )
            else:
                self.funnel_info.setText("No funnel data available.")

            # DB Status
            tables = analytics.get_table_sizes()
            if tables:
                db_text = "\n".join([f"  {t['table_name']:22s}  {int(t['row_count']):>8,} rows" for t in tables])
                total = sum(int(t['row_count']) for t in tables)
                db_text += f"\n\n  Total: {total:,} rows across {len(tables)} tables"
                self.db_info.setText(db_text)
            else:
                self.db_info.setText("Could not load table sizes.")

            # Problems
            try:
                from src.engine.problem_detector import problem_detector
                problems = problem_detector.detect_all_problems()
                if problems:
                    p_text = ""
                    for p in problems[:5]:
                        severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}.get(p.severity, "⚪")
                        p_text += f"  {severity_icon} [{p.severity.upper()}] {p.title}\n"
                        p_text += f"      Priority: {p.priority_score:.0f}/100 | {p.description[:80]}\n\n"
                    self.problems_info.setText(p_text)
                else:
                    self.problems_info.setText("  ✅ No significant problems detected. System is healthy.")
            except Exception:
                self.problems_info.setText("  Problem detection not available yet.")

        except Exception as e:
            self.segment_info.setText(f"Error loading data: {e}\n\nMake sure PostgreSQL is running and data is seeded.")
            traceback.print_exc()
