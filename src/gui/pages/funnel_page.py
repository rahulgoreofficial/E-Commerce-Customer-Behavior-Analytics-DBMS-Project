"""Funnel Analytics Page — Conversion funnel breakdown by device/channel/time."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QScrollArea
)
from PySide6.QtCore import Qt


class FunnelPage(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("🔄 Funnel & Behavior Analytics")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #ffffff;")
        header.addWidget(title)
        header.addStretch()
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh)
        refresh_btn.setFixedWidth(100)
        header.addWidget(refresh_btn)
        layout.addLayout(header)

        # Overall funnel
        self.funnel_card = self._make_card("Conversion Funnel (30 Days)")
        self.funnel_label = self.funnel_card.findChild(QLabel, "content")
        layout.addWidget(self.funnel_card)

        # By device
        self.device_card = self._make_card("Funnel by Device")
        self.device_label = self.device_card.findChild(QLabel, "content")
        layout.addWidget(self.device_card)

        # Weekly trend
        self.trend_card = self._make_card("Weekly Funnel Trend")
        self.trend_label = self.trend_card.findChild(QLabel, "content")
        layout.addWidget(self.trend_card)

        # Cohort
        self.cohort_card = self._make_card("Cohort Retention Analysis")
        self.cohort_label = self.cohort_card.findChild(QLabel, "content")
        layout.addWidget(self.cohort_card)

        layout.addStretch()
        scroll.setWidget(content)
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)

    def _make_card(self, title_text):
        card = QFrame()
        card.setStyleSheet("QFrame { background: #22233d; border: 1px solid #2a2b4a; border-radius: 12px; padding: 16px; }")
        layout = QVBoxLayout(card)
        title = QLabel(title_text)
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #c0c0e0; background: transparent;")
        layout.addWidget(title)
        content = QLabel("Loading...")
        content.setObjectName("content")
        content.setStyleSheet("font-size: 13px; color: #a0a0c0; background: transparent; line-height: 1.6; font-family: 'Consolas', monospace;")
        content.setWordWrap(True)
        layout.addWidget(content)
        return card

    def refresh(self):
        try:
            from src.analytics.sql_analytics import analytics

            # Overall funnel
            funnel = analytics.get_funnel_data(30)
            if funnel:
                f = funnel[0]
                v, c, ch, p = int(f['view_sessions']), int(f['cart_sessions']), int(f['checkout_sessions']), int(f['purchase_sessions'])
                bar_v = "█" * 40
                bar_c = "█" * max(1, int(40 * c / max(v, 1)))
                bar_ch = "█" * max(1, int(40 * ch / max(v, 1)))
                bar_p = "█" * max(1, int(40 * p / max(v, 1)))
                text = (
                    f"  Views      {bar_v}  {v:,}  (100%)\n"
                    f"  Cart       {bar_c:40s}  {c:,}  ({c/max(v,1)*100:.1f}%)  ▼ {(1-c/max(v,1))*100:.1f}% drop\n"
                    f"  Checkout   {bar_ch:40s}  {ch:,}  ({ch/max(v,1)*100:.1f}%)  ▼ {(1-ch/max(c,1))*100:.1f}% drop\n"
                    f"  Purchase   {bar_p:40s}  {p:,}  ({p/max(v,1)*100:.1f}%)  ▼ {(1-p/max(ch,1))*100:.1f}% drop\n"
                )
                self.funnel_card.findChild(QLabel, "content").setText(text)

            # By device
            device = analytics.get_funnel_by_device(30)
            if device:
                lines = [f"  {'Device':<12s} {'Views':>8s} {'Carts':>8s} {'Checkouts':>10s} {'Purchases':>10s} {'Conv%':>8s}"]
                lines.append("  " + "─" * 60)
                for d in device:
                    lines.append(
                        f"  {str(d['device']):<12s} {int(d['views']):>8,} {int(d['carts']):>8,} "
                        f"{int(d['checkouts']):>10,} {int(d['purchases']):>10,} {float(d['conversion_pct']):>7.2f}%"
                    )
                self.device_card.findChild(QLabel, "content").setText("\n".join(lines))

            # Weekly trend
            trend = analytics.get_funnel_weekly_trend(8)
            if trend:
                lines = [f"  {'Week':<12s} {'Views':>8s} {'Carts':>8s} {'Purchases':>10s} {'V→C%':>8s} {'C→P%':>8s}"]
                lines.append("  " + "─" * 60)
                for t in trend:
                    lines.append(
                        f"  {str(t['week_start']):<12s} {int(t['view_sessions']):>8,} {int(t['cart_sessions']):>8,} "
                        f"{int(t['purchase_sessions']):>10,} {float(t['view_to_cart_pct']):>7.1f}% {float(t['cart_to_purchase_pct']):>7.1f}%"
                    )
                self.trend_card.findChild(QLabel, "content").setText("\n".join(lines))

            # Cohort
            cohort = analytics.get_cohort_retention()
            if cohort:
                lines = [f"  {'Cohort':<12s} {'Size':>6s} {'M0':>6s} {'M1':>6s} {'M2':>6s} {'M3':>6s} {'M4':>6s} {'M5':>6s}"]
                lines.append("  " + "─" * 60)
                for c in cohort[-8:]:
                    size = int(c['cohort_size'])
                    lines.append(
                        f"  {str(c['cohort_month']):<12s} {size:>6} "
                        f"{int(c['month_0']):>6} {int(c['month_1']):>6} {int(c['month_2']):>6} "
                        f"{int(c['month_3']):>6} {int(c['month_4']):>6} {int(c['month_5']):>6}"
                    )
                self.cohort_card.findChild(QLabel, "content").setText("\n".join(lines))

        except Exception as e:
            self.funnel_card.findChild(QLabel, "content").setText(f"Error: {e}")
