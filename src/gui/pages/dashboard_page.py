"""
Dashboard Page — Real-Time KPI Cards, Live Pulse Stream, Conversion Funnel, Segments & Detected Problems.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
    QFrame, QPushButton, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont
import traceback


class KPICard(QFrame):
    """A single KPI metric card with trend and accent colors."""
    def __init__(self, title, value="--", change="", positive=True, accent_color="#7c6ff7"):
        super().__init__()
        self.setProperty("class", "kpi-card")
        self.setStyleSheet(f"""
            KPICard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #22233f, stop:1 #2a2b52);
                border: 1px solid #383968; border-radius: 12px; padding: 16px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; background: transparent; font-weight: bold;")
        layout.addWidget(self.title_label)

        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {accent_color}; background: transparent;")
        layout.addWidget(self.value_label)

        self.change_label = QLabel(change)
        color = "#10b981" if positive else "#f87171"
        self.change_label.setStyleSheet(f"font-size: 11px; color: {color}; background: transparent;")
        layout.addWidget(self.change_label)

    def update_values(self, value, change="", positive=True):
        self.value_label.setText(str(value))
        self.change_label.setText(change)
        color = "#10b981" if positive else "#f87171"
        self.change_label.setStyleSheet(f"font-size: 11px; color: {color}; background: transparent;")


class DashboardPage(QWidget):
    """Real-Time Dynamic Decision Support Dashboard."""

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._setup_auto_refresh()

    def _setup_ui(self):
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        # ── Header ──
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("📈 Executive Decision Dashboard")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #ffffff;")
        subtitle = QLabel("Real-time behavioral telemetry, transaction velocity & automated issue detection")
        subtitle.setStyleSheet("font-size: 12px; color: #8888aa;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch()

        # Live Pulse Auto-refresh checkbox
        self.live_mode_chk = QCheckBox("⚡ Live Pulse Mode (5s)")
        self.live_mode_chk.setChecked(False)
        self.live_mode_chk.setStyleSheet("""
            QCheckBox { color: #38bdf8; font-weight: bold; font-size: 12px; padding: 6px 12px; background: #1a1c38; border: 1px solid #333660; border-radius: 6px; }
            QCheckBox::indicator { width: 14px; height: 14px; }
        """)
        self.live_mode_chk.stateChanged.connect(self._toggle_live_mode)
        header.addWidget(self.live_mode_chk)

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setStyleSheet("""
            QPushButton { background: #3b3a6e; color: #ffffff; border-radius: 6px; padding: 7px 16px; font-weight: bold; font-size: 12px; }
            QPushButton:hover { background: #4b4a8e; }
        """)
        self.refresh_btn.clicked.connect(self.refresh)
        header.addWidget(self.refresh_btn)
        layout.addLayout(header)

        # ── KPI Cards Grid ──
        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(14)
        self.kpi_revenue = KPICard("REVENUE (7 DAYS)", "₹0", accent_color="#38bdf8")
        self.kpi_orders = KPICard("ORDERS", "0", accent_color="#818cf8")
        self.kpi_customers = KPICard("ACTIVE CUSTOMERS", "0", accent_color="#c084fc")
        self.kpi_conversion = KPICard("CONVERSION RATE", "0%", accent_color="#10b981")
        self.kpi_abandonment = KPICard("CART ABANDONMENT", "0%", positive=False, accent_color="#f87171")
        self.kpi_sentiment = KPICard("CUSTOMER CSAT / RATING", "0.0 ★", accent_color="#fbbf24")

        kpi_grid.addWidget(self.kpi_revenue, 0, 0)
        kpi_grid.addWidget(self.kpi_orders, 0, 1)
        kpi_grid.addWidget(self.kpi_customers, 0, 2)
        kpi_grid.addWidget(self.kpi_conversion, 0, 3)
        kpi_grid.addWidget(self.kpi_abandonment, 0, 4)
        kpi_grid.addWidget(self.kpi_sentiment, 0, 5)
        layout.addLayout(kpi_grid)

        # ── Live Activity Pulse Stream & Funnel Row ──
        stream_row = QHBoxLayout()
        stream_row.setSpacing(16)

        # 1. Live Activity Feed (ALIVE & DYNAMIC)
        stream_card = QFrame()
        stream_card.setStyleSheet("QFrame { background: #22233d; border: 1px solid #2a2b4a; border-radius: 12px; padding: 14px; }")
        stream_layout = QVBoxLayout(stream_card)
        
        s_head = QHBoxLayout()
        s_title = QLabel("⚡ Live Event & Transaction Pulse Stream")
        s_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #38bdf8; background: transparent;")
        s_head.addWidget(s_title)
        s_head.addStretch()
        self.live_indicator = QLabel("● STREAMING ACTIVE")
        self.live_indicator.setStyleSheet("color: #10b981; font-size: 10px; font-weight: bold; background: transparent;")
        s_head.addWidget(self.live_indicator)
        stream_layout.addLayout(s_head)

        self.stream_table = QTableWidget()
        self.stream_table.setColumnCount(4)
        self.stream_table.setHorizontalHeaderLabels(["Type", "Action / Amount", "Details / Product", "Actor"])
        self.stream_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.stream_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.stream_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.stream_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.stream_table.setFixedHeight(220)
        self.stream_table.setStyleSheet("""
            QTableWidget { background: #16172a; border: 1px solid #252644; border-radius: 6px; color: #e2e8f0; font-size: 11px; }
            QHeaderView::section { background: #1f2038; color: #94a3b8; padding: 4px; border: none; font-size: 10px; font-weight: bold; }
        """)
        self.stream_table.setSelectionBehavior(QTableWidget.SelectRows)
        stream_layout.addWidget(self.stream_table)
        stream_row.addWidget(stream_card, 3)

        # 2. Conversion Funnel Card
        funnel_card = QFrame()
        funnel_card.setStyleSheet("QFrame { background: #22233d; border: 1px solid #2a2b4a; border-radius: 12px; padding: 14px; }")
        funnel_layout = QVBoxLayout(funnel_card)
        funnel_title = QLabel("🔄 Conversion Funnel Velocity")
        funnel_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #a5b4fc; background: transparent;")
        funnel_layout.addWidget(funnel_title)

        self.funnel_info = QLabel("Loading funnel metrics...")
        self.funnel_info.setStyleSheet("font-size: 12px; color: #cbd5e1; background: transparent; line-height: 1.6; font-family: 'Consolas', monospace;")
        self.funnel_info.setWordWrap(True)
        funnel_layout.addWidget(self.funnel_info)
        funnel_layout.addStretch()
        stream_row.addWidget(funnel_card, 2)

        layout.addLayout(stream_row)

        # ── Segments & DB Health Row ──
        info_row = QHBoxLayout()
        info_row.setSpacing(16)

        # Segment Distribution
        seg_card = QFrame()
        seg_card.setStyleSheet("QFrame { background: #22233d; border: 1px solid #2a2b4a; border-radius: 12px; padding: 14px; }")
        seg_layout = QVBoxLayout(seg_card)
        seg_title = QLabel("👥 Customer Segments Distribution")
        seg_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #c084fc; background: transparent;")
        seg_layout.addWidget(seg_title)
        self.segment_info = QLabel("Loading segments...")
        self.segment_info.setStyleSheet("font-size: 12px; color: #a0a0c0; background: transparent; line-height: 1.6; font-family: 'Consolas', monospace;")
        self.segment_info.setWordWrap(True)
        seg_layout.addWidget(self.segment_info)
        seg_layout.addStretch()
        info_row.addWidget(seg_card)

        # Database Status
        db_card = QFrame()
        db_card.setStyleSheet("QFrame { background: #22233d; border: 1px solid #2a2b4a; border-radius: 12px; padding: 14px; }")
        db_layout = QVBoxLayout(db_card)
        db_title = QLabel("🗄️ PostgreSQL Database Sizing")
        db_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #38bdf8; background: transparent;")
        db_layout.addWidget(db_title)
        self.db_info = QLabel("Loading database metrics...")
        self.db_info.setStyleSheet("font-size: 12px; color: #a0a0c0; background: transparent; line-height: 1.6; font-family: 'Consolas', monospace;")
        self.db_info.setWordWrap(True)
        db_layout.addWidget(self.db_info)
        db_layout.addStretch()
        info_row.addWidget(db_card)

        layout.addLayout(info_row)

        # ── Detected Problems Section ──
        problems_card = QFrame()
        problems_card.setStyleSheet("QFrame { background: #22233d; border: 1px solid #2a2b4a; border-radius: 12px; padding: 16px; }")
        problems_layout = QVBoxLayout(problems_card)
        problems_title = QLabel("⚠️ Automated Decision Support & Operational Bottlenecks")
        problems_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #f87171; background: transparent;")
        problems_layout.addWidget(problems_title)
        self.problems_info = QLabel("Analyzing system health...")
        self.problems_info.setStyleSheet("font-size: 12px; color: #cbd5e1; background: transparent; line-height: 1.8;")
        self.problems_info.setWordWrap(True)
        problems_layout.addWidget(self.problems_info)
        layout.addWidget(problems_card)

        layout.addStretch()
        scroll.setWidget(content)
        page_layout.addWidget(scroll)

        # Initial load
        self.refresh()

    def _setup_auto_refresh(self):
        """Setup 5s interval timer for live stream telemetry."""
        self._timer = QTimer(self)
        self._timer.setInterval(5000)
        self._timer.timeout.connect(self._on_auto_refresh)

    def _toggle_live_mode(self, state):
        if self.live_mode_chk.isChecked():
            self._timer.start()
            self.live_indicator.setText("● LIVE STREAMING ACTIVE (5s)")
            self.live_indicator.setStyleSheet("color: #10b981; font-size: 10px; font-weight: bold; background: transparent;")
        else:
            self._timer.stop()
            self.live_indicator.setText("○ PAUSED")
            self.live_indicator.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: bold; background: transparent;")

    def _on_auto_refresh(self):
        """Called periodically by timer."""
        self.refresh(silent=True)

    def refresh(self, silent=False):
        """Load live telemetry and data from PostgreSQL."""
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
                self.kpi_revenue.update_values(
                    f"₹{revenue:,.0f}",
                    f"{'▲' if rev_change >= 0 else '▼'} {abs(rev_change):.1f}% vs prev week",
                    rev_change >= 0
                )
                self.kpi_orders.update_values(f"{orders:,}")
                self.kpi_customers.update_values(f"{customers:,}")
                self.kpi_conversion.update_values(f"{conv_rate:.1f}%")
                self.kpi_abandonment.update_values(f"{aband_rate:.1f}%", "", aband_rate < 70)

            # Sentiment KPI
            try:
                rev_sum = analytics.get_review_sentiment_summary()
                if rev_sum and len(rev_sum) > 0:
                    rs = rev_sum[0]
                    avg_stars = float(rs.get('avg_rating', 0))
                    avg_sent = float(rs.get('avg_sentiment', 0))
                    self.kpi_sentiment.update_values(f"{avg_stars:.1f} ★", f"Net Polarity: {avg_sent:+.2f}", avg_sent >= 0)
            except Exception:
                pass

            # Live Activity Stream
            stream = analytics.get_live_activity_stream(15)
            self.stream_table.setRowCount(len(stream or []))
            for i, item in enumerate(stream or []):
                act_type = str(item.get('activity_type', 'EVENT'))
                type_item = QTableWidgetItem(act_type)
                if act_type == 'ORDER':
                    type_item.setForeground(QColor("#38bdf8"))
                elif act_type == 'REVIEW':
                    type_item.setForeground(QColor("#f59e0b"))
                else:
                    type_item.setForeground(QColor("#10b981"))

                action_item = QTableWidgetItem(str(item.get('action', '')))
                detail_item = QTableWidgetItem(str(item.get('details', '')))
                actor_item = QTableWidgetItem(f"{item.get('actor', '')} ({item.get('context', '')})")

                self.stream_table.setItem(i, 0, type_item)
                self.stream_table.setItem(i, 1, action_item)
                self.stream_table.setItem(i, 2, detail_item)
                self.stream_table.setItem(i, 3, actor_item)

            # Segments
            segments = analytics.get_rfm_segments()
            if segments:
                seg_text = "\n".join([f"  {s['segment']:12s}  —  {s['count']} customers  (Avg LTV: ₹{float(s['avg_ltv']):,.0f})" for s in segments])
                self.segment_info.setText(seg_text)
            else:
                self.segment_info.setText("No segment data available.")

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
                    f"\n  Overall Conversion: {purchases/max(views,1)*100:.2f}%"
                )

            # Database sizes
            tables = analytics.get_table_sizes()
            if tables:
                db_text = "\n".join([f"  {t['table_name']:22s}  {int(t['row_count']):>8,} rows" for t in tables])
                total = sum(int(t['row_count']) for t in tables)
                db_text += f"\n\n  Total: {total:,} records across {len(tables)} tables"
                self.db_info.setText(db_text)

            # Problems
            try:
                from src.engine.problem_detector import problem_detector
                problems = problem_detector.detect_all_problems()
                if problems:
                    p_text = ""
                    for p in problems[:5]:
                        severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}.get(p.severity, "⚪")
                        p_text += f"  {severity_icon} <b>[{p.severity.upper()}] {p.title}</b>\n"
                        p_text += f"      Priority: <b>{p.priority_score:.0f}/100</b> | {p.description}\n\n"
                    self.problems_info.setText(p_text)
                else:
                    self.problems_info.setText("  ✅ No critical anomalies detected. System operational metrics are optimal.")
            except Exception as pe:
                self.problems_info.setText(f"  Problem detection note: {pe}")

        except Exception as e:
            if not silent:
                print(f"Error loading dashboard: {e}")
                traceback.print_exc()
