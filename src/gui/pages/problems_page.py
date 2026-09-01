"""Problems Page — Detected business problems with evidence and recommendations."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QScrollArea, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt


class ProblemsPage(QWidget):
    def __init__(self):
        super().__init__()
        self._problems = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Left: Problem list
        left = QVBoxLayout()
        header = QHBoxLayout()
        title = QLabel("⚠️ Detected Problems")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #ffffff;")
        header.addWidget(title)
        header.addStretch()
        refresh_btn = QPushButton("🔄 Detect")
        refresh_btn.clicked.connect(self.refresh)
        refresh_btn.setFixedWidth(100)
        header.addWidget(refresh_btn)
        left.addLayout(header)

        self.problem_list = QListWidget()
        self.problem_list.setStyleSheet("""
            QListWidget { background: #1e1f38; border: 1px solid #2a2b4a; border-radius: 8px; }
            QListWidget::item { padding: 12px; border-bottom: 1px solid #2a2b4a; }
            QListWidget::item:selected { background: #2d2e5e; }
            QListWidget::item:hover { background: #252648; }
        """)
        self.problem_list.currentRowChanged.connect(self._on_select)
        left.addWidget(self.problem_list)

        left_widget = QWidget()
        left_widget.setLayout(left)
        layout.addWidget(left_widget, stretch=1)

        # Right: Problem detail
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        right_content = QWidget()
        right_layout = QVBoxLayout(right_content)
        right_layout.setSpacing(12)

        self.detail_title = QLabel("Select a problem to view details")
        self.detail_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        self.detail_title.setWordWrap(True)
        right_layout.addWidget(self.detail_title)

        self.severity_label = QLabel("")
        self.severity_label.setStyleSheet("font-size: 12px; padding: 4px 12px; border-radius: 4px;")
        right_layout.addWidget(self.severity_label)

        self.desc_label = QLabel("")
        self.desc_label.setStyleSheet("font-size: 13px; color: #c0c0e0; line-height: 1.5;")
        self.desc_label.setWordWrap(True)
        right_layout.addWidget(self.desc_label)

        # Evidence card
        evidence_card = QFrame()
        evidence_card.setStyleSheet("QFrame { background: #22233d; border: 1px solid #2a2b4a; border-radius: 12px; padding: 16px; }")
        ev_layout = QVBoxLayout(evidence_card)
        ev_title = QLabel("📊 Evidence")
        ev_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #c0c0e0; background: transparent;")
        ev_layout.addWidget(ev_title)
        self.evidence_label = QLabel("")
        self.evidence_label.setStyleSheet("font-size: 13px; color: #a0a0c0; background: transparent; line-height: 1.8;")
        self.evidence_label.setWordWrap(True)
        ev_layout.addWidget(self.evidence_label)
        right_layout.addWidget(evidence_card)

        # Recommendations card
        rec_card = QFrame()
        rec_card.setStyleSheet("QFrame { background: #22233d; border: 1px solid #2a2b4a; border-radius: 12px; padding: 16px; }")
        rec_layout = QVBoxLayout(rec_card)
        rec_title = QLabel("💡 Recommendations")
        rec_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #4ade80; background: transparent;")
        rec_layout.addWidget(rec_title)
        self.rec_label = QLabel("")
        self.rec_label.setStyleSheet("font-size: 13px; color: #a0a0c0; background: transparent; line-height: 1.8;")
        self.rec_label.setWordWrap(True)
        rec_layout.addWidget(self.rec_label)
        right_layout.addWidget(rec_card)

        # What-If card
        whatif_card = QFrame()
        whatif_card.setStyleSheet("QFrame { background: #22233d; border: 1px solid #2a2b4a; border-radius: 12px; padding: 16px; }")
        wf_layout = QVBoxLayout(whatif_card)
        wf_title = QLabel("🔮 What-If Estimation")
        wf_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #a78bfa; background: transparent;")
        wf_layout.addWidget(wf_title)
        self.whatif_label = QLabel("")
        self.whatif_label.setStyleSheet("font-size: 13px; color: #a0a0c0; background: transparent; line-height: 1.8;")
        self.whatif_label.setWordWrap(True)
        wf_layout.addWidget(self.whatif_label)
        right_layout.addWidget(whatif_card)

        right_layout.addStretch()
        right_scroll.setWidget(right_content)
        layout.addWidget(right_scroll, stretch=2)

    def refresh(self):
        try:
            from src.engine.problem_detector import problem_detector
            self._problems = problem_detector.detect_all_problems()
            self.problem_list.clear()

            if not self._problems:
                item = QListWidgetItem("✅ No significant problems detected")
                self.problem_list.addItem(item)
                return

            for p in self._problems:
                icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}.get(p.severity, "⚪")
                text = f"{icon} [{p.severity.upper()}]  {p.title}\n    Priority: {p.priority_score:.0f}/100"
                item = QListWidgetItem(text)
                self.problem_list.addItem(item)

        except Exception as e:
            item = QListWidgetItem(f"Error: {e}")
            self.problem_list.addItem(item)

    def _on_select(self, row):
        if 0 <= row < len(self._problems):
            p = self._problems[row]
            
            self.detail_title.setText(p.title)
            
            sev_colors = {'critical': '#dc2626', 'high': '#ea580c', 'medium': '#ca8a04', 'low': '#2563eb'}
            self.severity_label.setText(f"  {p.severity.upper()}  |  Priority: {p.priority_score:.0f}/100  |  Confidence: {p.confidence:.0%}")
            self.severity_label.setStyleSheet(
                f"font-size: 12px; color: white; background: {sev_colors.get(p.severity, '#666')}; "
                f"padding: 6px 16px; border-radius: 6px; font-weight: bold;"
            )
            
            self.desc_label.setText(p.description)

            # Evidence
            ev_lines = []
            for ev in p.evidence:
                direction_icon = "📈" if ev.direction == "increased" else ("📉" if ev.direction == "decreased" else "➡️")
                ev_lines.append(f"  {direction_icon}  {ev.description}")
                if ev.baseline_value:
                    ev_lines.append(f"       Current: {ev.current_value:.1f}  |  Baseline: {ev.baseline_value:.1f}")
            self.evidence_label.setText("\n".join(ev_lines) if ev_lines else "No evidence details available.")

            # Recommendations
            rec_lines = []
            for i, r in enumerate(p.recommendations, 1):
                priority_icon = {"high": "🔴", "medium": "🟡", "low": "🔵"}.get(r.priority, "⚪")
                rec_lines.append(f"  {i}. {priority_icon} {r.action}")
                rec_lines.append(f"      ↳ {r.rationale}")
                rec_lines.append(f"      Category: {r.category}")
                rec_lines.append("")
            self.rec_label.setText("\n".join(rec_lines) if rec_lines else "No recommendations available.")

            # What-If
            try:
                from src.engine.problem_detector import recommendation_engine
                impact = recommendation_engine.estimate_impact(p, "default")
                if 'scenarios' in impact:
                    wf_lines = []
                    for name, scenario in impact['scenarios'].items():
                        wf_lines.append(f"  📊 {name.title()}:")
                        wf_lines.append(f"      Assumption: {scenario.get('assumption', 'N/A')}")
                        for k, v in scenario.items():
                            if k != 'assumption' and isinstance(v, (int, float)):
                                wf_lines.append(f"      Estimated: ₹{v:,.0f}")
                        wf_lines.append("")
                    if impact.get('disclaimer'):
                        wf_lines.append(f"  ⚠️ {impact['disclaimer']}")
                    self.whatif_label.setText("\n".join(wf_lines))
                else:
                    self.whatif_label.setText(impact.get('message', 'No estimation available.'))
            except Exception:
                self.whatif_label.setText("What-if estimation not available.")
