"""
Reviews & Sentiment Page — Live Amazon Review Explorer, Topic Insights, and Interactive NLP Testing Studio.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QScrollArea, QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QTextEdit, QProgressBar, QGridLayout, QSplitter
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont
from src.ml.models import ml_manager
from src.ml.review_loader import review_loader


class SentimentBadge(QLabel):
    """Badge displaying sentiment label with appropriate modern colors."""
    def __init__(self, label: str, score: float = 0.0):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(24)
        self.update_sentiment(label, score)

    def update_sentiment(self, label: str, score: float = 0.0):
        if label == "Positive":
            bg = "#103d2b"
            border = "#10b981"
            color = "#6ee7b7"
            icon = "🟢"
        elif label == "Negative":
            bg = "#3d141d"
            border = "#ef4444"
            color = "#fca5a5"
            icon = "🔴"
        else:
            bg = "#382d13"
            border = "#f59e0b"
            color = "#fde68a"
            icon = "🟡"

        self.setText(f"{icon} {label.upper()} ({score:+.2f})")
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 6px;
                color: {color};
                font-size: 11px;
                font-weight: bold;
                padding: 2px 8px;
            }}
        """)


class ReviewsPage(QWidget):
    """Interactive Reviews Exploration and Real-Time NLP Studio."""

    def __init__(self):
        super().__init__()
        self._setup_ui()

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
        title = QLabel("💬 Customer Reviews & Sentiment Intelligence")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #ffffff;")
        subtitle = QLabel("Real-time voice of customer analytics, NLP sentiment inference & operational topic signals")
        subtitle.setStyleSheet("font-size: 12px; color: #8888aa;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch()

        self.refresh_btn = QPushButton("🔄 Refresh Data")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background: #3b3a6e; color: #ffffff; border-radius: 8px;
                padding: 8px 16px; font-weight: bold; font-size: 12px;
            }
            QPushButton:hover { background: #4b4a8e; }
        """)
        self.refresh_btn.clicked.connect(self.refresh)
        header.addWidget(self.refresh_btn)
        layout.addLayout(header)

        # ── Metrics Row ──
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(14)

        self.card_total = self._make_stat_card("TOTAL REVIEWS", "0", "#7c6ff7")
        self.card_avg_stars = self._make_stat_card("AVG STAR RATING", "0.0 ★", "#f59e0b")
        self.card_sentiment = self._make_stat_card("NET SENTIMENT INDEX", "+0.00", "#10b981")
        self.card_pos_ratio = self._make_stat_card("POSITIVE RATIO", "0%", "#38bdf8")

        metrics_grid.addWidget(self.card_total, 0, 0)
        metrics_grid.addWidget(self.card_avg_stars, 0, 1)
        metrics_grid.addWidget(self.card_sentiment, 0, 2)
        metrics_grid.addWidget(self.card_pos_ratio, 0, 3)
        layout.addLayout(metrics_grid)

        # ── Interactive NLP Studio Playground (ALIVE & DYNAMIC) ──
        studio_card = QFrame()
        studio_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1e1f3a, stop:1 #27284d);
                border: 1px solid #434475; border-radius: 12px; padding: 18px;
            }
        """)
        studio_layout = QVBoxLayout(studio_card)

        studio_header = QHBoxLayout()
        studio_title = QLabel("⚡ Live AI Review Sentiment & Aspect Analyzer")
        studio_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #a5b4fc; background: transparent;")
        studio_header.addWidget(studio_title)
        studio_header.addStretch()

        # Preset buttons for quick interactive testing
        preset_label = QLabel("Quick Presets:")
        preset_label.setStyleSheet("color: #94a3b8; font-size: 11px; background: transparent;")
        studio_header.addWidget(preset_label)

        btn_preset_pos = QPushButton("Positive")
        btn_preset_pos.setFixedHeight(22)
        btn_preset_pos.setStyleSheet("background: #065f46; color: #6ee7b7; border-radius: 4px; padding: 2px 8px; font-size: 10px;")
        btn_preset_pos.clicked.connect(lambda: self._set_preset(
            "Amazing product! The delivery arrived 2 days earlier than expected, build quality is super solid and customer support was very helpful."
        ))
        studio_header.addWidget(btn_preset_pos)

        btn_preset_neg = QPushButton("Negative")
        btn_preset_neg.setFixedHeight(22)
        btn_preset_neg.setStyleSheet("background: #881337; color: #fca5a5; border-radius: 4px; padding: 2px 8px; font-size: 10px;")
        btn_preset_neg.clicked.connect(lambda: self._set_preset(
            "Terrible experience. Driver never showed up, package marked delivered falsely and customer support refused to refund my money. Disgraceful!"
        ))
        studio_header.addWidget(btn_preset_neg)

        btn_preset_neu = QPushButton("Neutral")
        btn_preset_neu.setFixedHeight(22)
        btn_preset_neu.setStyleSheet("background: #78350f; color: #fde68a; border-radius: 4px; padding: 2px 8px; font-size: 10px;")
        btn_preset_neu.clicked.connect(lambda: self._set_preset(
            "Average quality item. Looks okay for the discounted price, works as described but packaging was slightly crushed."
        ))
        studio_header.addWidget(btn_preset_neu)

        studio_layout.addLayout(studio_header)

        # Input & Result Columns
        studio_content = QHBoxLayout()
        studio_content.setSpacing(16)

        # Input side
        input_col = QVBoxLayout()
        self.review_input = QTextEdit()
        self.review_input.setPlaceholderText("Type or paste any real customer feedback, product review, or complaint here to analyze sentiment live...")
        self.review_input.setFixedHeight(90)
        self.review_input.setStyleSheet("""
            QTextEdit {
                background: #131424; color: #ffffff; border: 1px solid #36375c;
                border-radius: 8px; padding: 10px; font-size: 13px; font-family: 'Segoe UI', sans-serif;
            }
            QTextEdit:focus { border: 1px solid #7c6ff7; }
        """)
        self.review_input.textChanged.connect(self._on_input_text_changed)
        input_col.addWidget(self.review_input)

        btn_row = QHBoxLayout()
        self.analyze_btn = QPushButton("🚀 Run NLP Inference")
        self.analyze_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #8b5cf6);
                color: #ffffff; border-radius: 6px; padding: 8px 16px; font-weight: bold; font-size: 12px;
            }
            QPushButton:hover { background: #7c6ff7; }
        """)
        self.analyze_btn.clicked.connect(self._run_live_analysis)
        btn_row.addWidget(self.analyze_btn)
        btn_row.addStretch()
        input_col.addLayout(btn_row)
        studio_content.addLayout(input_col, 3)

        # Output / Analysis side
        result_box = QFrame()
        result_box.setStyleSheet("background: #141529; border: 1px solid #2d2e4e; border-radius: 8px; padding: 12px;")
        result_layout = QVBoxLayout(result_box)
        result_layout.setSpacing(8)

        r_top = QHBoxLayout()
        self.res_badge = SentimentBadge("Neutral", 0.0)
        r_top.addWidget(self.res_badge)
        self.res_stars = QLabel("Predicted: ⭐⭐⭐")
        self.res_stars.setStyleSheet("font-size: 13px; font-weight: bold; color: #fbbf24; background: transparent;")
        r_top.addWidget(self.res_stars)
        r_top.addStretch()
        result_layout.addLayout(r_top)

        self.prob_bar = QProgressBar()
        self.prob_bar.setRange(0, 100)
        self.prob_bar.setValue(50)
        self.prob_bar.setTextVisible(True)
        self.prob_bar.setStyleSheet("""
            QProgressBar {
                background: #1f2038; border-radius: 4px; text-align: center; color: #ffffff; height: 14px; font-size: 10px;
            }
            QProgressBar::chunk { background: #6366f1; border-radius: 4px; }
        """)
        result_layout.addWidget(self.prob_bar)

        self.res_details = QLabel("Keywords: Type a review to detect positive / negative triggers")
        self.res_details.setStyleSheet("font-size: 11px; color: #94a3b8; background: transparent; line-height: 1.4;")
        self.res_details.setWordWrap(True)
        result_layout.addWidget(self.res_details)

        studio_content.addWidget(result_box, 2)
        studio_layout.addLayout(studio_content)
        layout.addWidget(studio_card)

        # ── Filters Row ──
        filter_box = QHBoxLayout()
        filter_box.setSpacing(12)

        search_label = QLabel("🔍 Search:")
        search_label.setStyleSheet("color: #c0c0e0; font-weight: bold; font-size: 12px;")
        filter_box.addWidget(search_label)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Filter by keyword (e.g. delivery, battery, sound, refund)...")
        self.search_edit.setStyleSheet("""
            QLineEdit {
                background: #22233d; color: #ffffff; border: 1px solid #323356;
                border-radius: 6px; padding: 6px 12px; font-size: 12px;
            }
        """)
        self.search_edit.textChanged.connect(self._apply_filters)
        filter_box.addWidget(self.search_edit, 2)

        star_label = QLabel("Rating:")
        star_label.setStyleSheet("color: #c0c0e0; font-size: 12px;")
        filter_box.addWidget(star_label)

        self.star_combo = QComboBox()
        self.star_combo.addItems(["All Stars", "5 Stars ★★★★★", "4 Stars ★★★★", "3 Stars ★★★", "2 Stars ★★", "1 Star ★"])
        self.star_combo.setStyleSheet("""
            QComboBox {
                background: #22233d; color: #ffffff; border: 1px solid #323356;
                border-radius: 6px; padding: 6px 10px; font-size: 12px;
            }
            QComboBox QAbstractItemView { background: #22233d; color: #ffffff; selection-background-color: #4338ca; }
        """)
        self.star_combo.currentIndexChanged.connect(self._apply_filters)
        filter_box.addWidget(self.star_combo)

        sent_label = QLabel("Sentiment:")
        sent_label.setStyleSheet("color: #c0c0e0; font-size: 12px;")
        filter_box.addWidget(sent_label)

        self.sent_combo = QComboBox()
        self.sent_combo.addItems(["All Sentiments", "Positive (4-5★)", "Neutral (3★)", "Negative (1-2★)"])
        self.sent_combo.setStyleSheet("""
            QComboBox {
                background: #22233d; color: #ffffff; border: 1px solid #323356;
                border-radius: 6px; padding: 6px 10px; font-size: 12px;
            }
            QComboBox QAbstractItemView { background: #22233d; color: #ffffff; selection-background-color: #4338ca; }
        """)
        self.sent_combo.currentIndexChanged.connect(self._apply_filters)
        filter_box.addWidget(self.sent_combo)

        layout.addLayout(filter_box)

        # ── Reviews Table ──
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Stars", "Sentiment", "Customer", "Product / Category", "Review Feedback Snippet", "Date"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.setColumnWidth(3, 180)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1a1b2e;
                alternate-background-color: #202138;
                border: 1px solid #2a2b4a;
                border-radius: 8px;
                color: #e0e0f0;
                gridline-color: #2a2b4a;
            }
            QHeaderView::section {
                background-color: #242542;
                color: #94a3b8;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #333458;
                font-weight: bold;
                font-size: 11px;
            }
            QTableWidget::item:selected { background-color: #3b3a6e; }
        """)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setFixedHeight(340)
        layout.addWidget(self.table)

        # ── Selected Review Detail Inspector ──
        self.detail_card = QFrame()
        self.detail_card.setStyleSheet("QFrame { background: #22233d; border: 1px solid #2a2b4a; border-radius: 10px; padding: 14px; }")
        detail_layout = QVBoxLayout(self.detail_card)
        detail_title = QLabel("📌 Selected Review Full Text & Deep Aspect Breakdown")
        detail_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #a5b4fc; background: transparent;")
        detail_layout.addWidget(detail_title)

        self.detail_text = QLabel("Click any row in the table above to inspect the complete voice of customer feedback.")
        self.detail_text.setStyleSheet("font-size: 12px; color: #cbd5e1; background: transparent; line-height: 1.6;")
        self.detail_text.setWordWrap(True)
        detail_layout.addWidget(self.detail_text)
        layout.addWidget(self.detail_card)

        self.table.itemSelectionChanged.connect(self._on_table_row_selected)

        layout.addStretch()
        scroll.setWidget(content)
        page_layout.addWidget(scroll)

        # Initial load
        self.refresh()

    def _make_stat_card(self, label_text: str, val_text: str, accent_color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #22233d, stop:1 #292a4e);
                border: 1px solid #323356; border-radius: 10px; padding: 14px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(4)

        t = QLabel(label_text)
        t.setStyleSheet("font-size: 10px; color: #94a3b8; font-weight: bold; letter-spacing: 1px; background: transparent;")
        card_layout.addWidget(t)

        v = QLabel(val_text)
        v.setObjectName("val")
        v.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {accent_color}; background: transparent;")
        card_layout.addWidget(v)

        return card

    def _set_preset(self, text: str):
        self.review_input.setText(text)
        self._run_live_analysis()

    def _on_input_text_changed(self):
        text = self.review_input.toPlainText().strip()
        if len(text) > 10:
            self._run_live_analysis()

    def _run_live_analysis(self):
        text = self.review_input.toPlainText().strip()
        if not text:
            return

        pred = ml_manager.predict_review_sentiment(text)
        label = pred['sentiment']
        score = pred['sentiment_score']
        stars = pred['predicted_stars']
        conf = int(pred['confidence'] * 100)

        self.res_badge.update_sentiment(label, score)
        star_str = "★" * stars + "☆" * (5 - stars)
        self.res_stars.setText(f"Predicted: {star_str} ({stars}/5)")

        self.prob_bar.setValue(conf)
        self.prob_bar.setFormat(f"Model Confidence: {conf}% ({label})")

        trigs = pred.get('trigger_words', {})
        pos_w = trigs.get('positive', [])
        neg_w = trigs.get('negative', [])
        parts = []
        if pos_w:
            parts.append(f"🟢 Positive Triggers: {', '.join(pos_w)}")
        if neg_w:
            parts.append(f"🔴 Negative Triggers: {', '.join(neg_w)}")
        if not parts:
            parts.append("Balanced neutral sentiment detected.")

        self.res_details.setText(" | ".join(parts))

    def _apply_filters(self):
        self.refresh_table_data()

    def _on_table_row_selected(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            return
        row = self.table.currentRow()
        text_item = self.table.item(row, 4)
        prod_item = self.table.item(row, 3)
        cust_item = self.table.item(row, 2)
        star_item = self.table.item(row, 0)
        sent_item = self.table.item(row, 1)

        if text_item:
            full_txt = text_item.toolTip() or text_item.text()
            topics = review_loader.detect_topics(full_txt)
            topic_str = ", ".join(topics)

            self.detail_text.setText(
                f"<b>Customer:</b> {cust_item.text() if cust_item else 'N/A'} | "
                f"<b>Product:</b> {prod_item.text() if prod_item else 'N/A'}<br>"
                f"<b>Rating:</b> {star_item.text() if star_item else ''} ({sent_item.text() if sent_item else ''}) | "
                f"<b>Detected Operational Topics:</b> <span style='color: #38bdf8;'>{topic_str}</span><br><br>"
                f"<b>Review Statement:</b><br><i style='color: #e2e8f0;'>\"{full_txt}\"</i>"
            )

    def refresh_table_data(self):
        """Fetch filtered reviews and populate table."""
        try:
            from src.analytics.sql_analytics import analytics

            star_idx = self.star_combo.currentIndex()
            star_filter = (6 - star_idx) if star_idx > 0 else None

            sent_idx = self.sent_combo.currentIndex()
            sent_filter = ["All", "Positive", "Neutral", "Negative"][sent_idx] if sent_idx > 0 else None

            search_term = self.search_edit.text().strip() or None

            reviews = analytics.get_recent_reviews(
                limit=60,
                star_filter=star_filter,
                sentiment_filter=sent_filter,
                search_term=search_term
            )

            self.table.setRowCount(len(reviews or []))
            for i, r in enumerate(reviews or []):
                stars = int(r.get('rating', 3))
                star_display = "★" * stars + "☆" * (5 - stars)
                star_item = QTableWidgetItem(star_display)
                star_item.setForeground(QColor("#f59e0b" if stars >= 4 else ("#ef4444" if stars <= 2 else "#eab308")))

                score = float(r.get('sentiment_score', 0))
                sent_label = "Positive" if stars >= 4 else ("Negative" if stars <= 2 else "Neutral")
                sent_item = QTableWidgetItem(f"{sent_label} ({score:+.2f})")
                sent_item.setForeground(QColor("#10b981" if stars >= 4 else ("#f87171" if stars <= 2 else "#fbbf24")))

                cust_item = QTableWidgetItem(f"{r.get('customer_code', 'CUST')} ({r.get('city', '')})")
                prod_item = QTableWidgetItem(f"{r.get('product_name', '')[:28]} | {r.get('category_name', '')}")
                
                raw_text = str(r.get('review_text', ''))
                snippet = raw_text.replace('\n', ' ')
                text_item = QTableWidgetItem(snippet[:80] + ("..." if len(snippet) > 80 else ""))
                text_item.setToolTip(raw_text)

                date_val = str(r.get('review_date', ''))[:10]
                date_item = QTableWidgetItem(date_val)

                self.table.setItem(i, 0, star_item)
                self.table.setItem(i, 1, sent_item)
                self.table.setItem(i, 2, cust_item)
                self.table.setItem(i, 3, prod_item)
                self.table.setItem(i, 4, text_item)
                self.table.setItem(i, 5, date_item)

        except Exception as e:
            print(f"Error loading reviews into table: {e}")

    def refresh(self):
        """Reload all metrics and table."""
        try:
            from src.analytics.sql_analytics import analytics

            summary = analytics.get_review_sentiment_summary()
            if summary and len(summary) > 0:
                s = summary[0]
                tot = int(s.get('total_reviews', 0))
                avg_r = float(s.get('avg_rating', 0.0))
                avg_s = float(s.get('avg_sentiment', 0.0))
                pos_c = int(s.get('positive_count', 0))
                ratio = (pos_c / tot * 100) if tot > 0 else 0

                self.card_total.findChild(QLabel, "val").setText(f"{tot:,}")
                self.card_avg_stars.findChild(QLabel, "val").setText(f"{avg_r:.2f} ★")
                self.card_sentiment.findChild(QLabel, "val").setText(f"{avg_s:+.2f}")
                self.card_pos_ratio.findChild(QLabel, "val").setText(f"{ratio:.1f}%")

            self.refresh_table_data()

        except Exception as e:
            print(f"Error refreshing review page: {e}")
