"""
Predictions Page — ML Model Training Studio, Evaluation Metrics & Interactive Live What-If Simulator.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QScrollArea, QProgressBar, QSlider, QComboBox, QGridLayout, QTabWidget
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor


class TrainThread(QThread):
    """Background thread for model training."""
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, model_type):
        super().__init__()
        self.model_type = model_type

    def run(self):
        try:
            from src.ml.models import ml_manager
            if self.model_type == 'purchase':
                result = ml_manager.train_purchase_prediction()
            elif self.model_type == 'abandonment':
                result = ml_manager.train_cart_abandonment()
            elif self.model_type == 'sentiment':
                result = ml_manager.train_review_sentiment_model()
            else:
                result = {"error": f"Unknown model type {self.model_type}"}
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class PredictionsPage(QWidget):
    """Machine Learning Training Hub & Real-Time Interactive What-If Simulation Sandbox."""

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
        layout.setSpacing(20)

        # ── Header ──
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("🔮 Machine Learning Intelligence & What-If Studio")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #ffffff;")
        subtitle = QLabel("Train decision models, inspect precision/recall & run real-time behavioral simulations")
        subtitle.setStyleSheet("font-size: 12px; color: #8888aa;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch()
        layout.addLayout(header)

        # ── Interactive What-If Simulator Sandbox (ALIVE & DYNAMIC) ──
        sim_card = QFrame()
        sim_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1a1c38, stop:1 #24264d);
                border: 1px solid #3d3e6d; border-radius: 12px; padding: 18px;
            }
        """)
        sim_layout = QVBoxLayout(sim_card)

        sim_head = QHBoxLayout()
        sim_title = QLabel("⚡ Live What-If Behavioral Simulator (Instant Probability Dials)")
        sim_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #818cf8; background: transparent;")
        sim_head.addWidget(sim_title)
        sim_head.addStretch()
        sim_layout.addLayout(sim_head)

        sliders_row = QHBoxLayout()
        sliders_row.setSpacing(20)

        # Left Column: Slider Controls
        controls_col = QVBoxLayout()
        controls_col.setSpacing(10)

        # 1. Cart Value Slider
        self.slider_cart_val, self.lbl_cart_val = self._make_slider("Cart Value (₹):", 100, 25000, 3500, "₹{:,}")
        controls_col.addLayout(self.slider_cart_val)

        # 2. Session Duration Slider
        self.slider_dur, self.lbl_dur = self._make_slider("Session Duration (min):", 1, 60, 12, "{} mins")
        controls_col.addLayout(self.slider_dur)

        # 3. Products Viewed Slider
        self.slider_views, self.lbl_views = self._make_slider("Products Viewed:", 1, 20, 4, "{} items")
        controls_col.addLayout(self.slider_views)

        # 4. Items Removed Slider
        self.slider_rem, self.lbl_rem = self._make_slider("Items Removed from Cart:", 0, 5, 1, "{} removed")
        controls_col.addLayout(self.slider_rem)

        # Dropdowns for Device and Customer Status
        combo_row = QHBoxLayout()
        
        dev_label = QLabel("Device:")
        dev_label.setStyleSheet("color: #cbd5e1; font-size: 11px; background: transparent;")
        combo_row.addWidget(dev_label)
        self.combo_device = QComboBox()
        self.combo_device.addItems(["Mobile", "Desktop", "Tablet"])
        self.combo_device.setStyleSheet("background: #141528; color: #ffffff; border: 1px solid #36375c; border-radius: 4px; padding: 4px;")
        self.combo_device.currentIndexChanged.connect(self._recalculate_live_simulation)
        combo_row.addWidget(self.combo_device)

        cust_label = QLabel("Customer Type:")
        cust_label.setStyleSheet("color: #cbd5e1; font-size: 11px; background: transparent;")
        combo_row.addWidget(cust_label)
        self.combo_cust = QComboBox()
        self.combo_cust.addItems(["New Visitor", "Returning Customer (Past Orders)"])
        self.combo_cust.setStyleSheet("background: #141528; color: #ffffff; border: 1px solid #36375c; border-radius: 4px; padding: 4px;")
        self.combo_cust.currentIndexChanged.connect(self._recalculate_live_simulation)
        combo_row.addWidget(self.combo_cust)

        controls_col.addLayout(combo_row)
        sliders_row.addLayout(controls_col, 3)

        # Right Column: Instant Live Output Gauges
        gauge_box = QFrame()
        gauge_box.setStyleSheet("background: #111222; border: 1px solid #292a47; border-radius: 10px; padding: 14px;")
        gauge_layout = QVBoxLayout(gauge_box)
        gauge_layout.setSpacing(12)

        # Purchase Gauge
        p_head = QHBoxLayout()
        p_title = QLabel("🎯 Purchase Probability:")
        p_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #cbd5e1; background: transparent;")
        p_head.addWidget(p_title)
        p_head.addStretch()
        self.lbl_purchase_prob = QLabel("0.0%")
        self.lbl_purchase_prob.setStyleSheet("font-size: 16px; font-weight: bold; color: #10b981; background: transparent;")
        p_head.addWidget(self.lbl_purchase_prob)
        gauge_layout.addLayout(p_head)

        self.bar_purchase = QProgressBar()
        self.bar_purchase.setRange(0, 100)
        self.bar_purchase.setFixedHeight(12)
        self.bar_purchase.setTextVisible(False)
        self.bar_purchase.setStyleSheet("QProgressBar { background: #1e1f36; border-radius: 6px; } QProgressBar::chunk { background: #10b981; border-radius: 6px; }")
        gauge_layout.addWidget(self.bar_purchase)

        # Abandonment Gauge
        a_head = QHBoxLayout()
        a_title = QLabel("🛒 Cart Abandonment Risk:")
        a_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #cbd5e1; background: transparent;")
        a_head.addWidget(a_title)
        a_head.addStretch()
        self.lbl_abandon_prob = QLabel("0.0%")
        self.lbl_abandon_prob.setStyleSheet("font-size: 16px; font-weight: bold; color: #f87171; background: transparent;")
        a_head.addWidget(self.lbl_abandon_prob)
        gauge_layout.addLayout(a_head)

        self.bar_abandon = QProgressBar()
        self.bar_abandon.setRange(0, 100)
        self.bar_abandon.setFixedHeight(12)
        self.bar_abandon.setTextVisible(False)
        self.bar_abandon.setStyleSheet("QProgressBar { background: #1e1f36; border-radius: 6px; } QProgressBar::chunk { background: #ef4444; border-radius: 6px; }")
        gauge_layout.addWidget(self.bar_abandon)

        # Proactive Recommendation Action
        self.lbl_action = QLabel("Recommended Action: Calculating...")
        self.lbl_action.setStyleSheet("font-size: 11px; color: #38bdf8; background: transparent; font-weight: bold;")
        self.lbl_action.setWordWrap(True)
        gauge_layout.addWidget(self.lbl_action)

        sliders_row.addWidget(gauge_box, 2)
        sim_layout.addLayout(sliders_row)
        layout.addWidget(sim_card)

        # ── Model Training Control Deck ──
        train_deck = QFrame()
        train_deck.setStyleSheet("background: #22233d; border: 1px solid #2a2b4a; border-radius: 12px; padding: 16px;")
        train_layout = QVBoxLayout(train_deck)

        train_title = QLabel("🏋️ Machine Learning Model Training Deck")
        train_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #c0c0e0; background: transparent;")
        train_layout.addWidget(train_title)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.train_purchase_btn = QPushButton("🎯 Train Purchase Model")
        self.train_purchase_btn.setStyleSheet("""
            QPushButton { background: #4f46e5; color: #ffffff; border-radius: 6px; padding: 8px 14px; font-weight: bold; }
            QPushButton:hover { background: #6366f1; }
        """)
        self.train_purchase_btn.clicked.connect(lambda: self._train("purchase"))
        btn_row.addWidget(self.train_purchase_btn)

        self.train_abandon_btn = QPushButton("🛒 Train Abandonment Model")
        self.train_abandon_btn.setStyleSheet("""
            QPushButton { background: #9333ea; color: #ffffff; border-radius: 6px; padding: 8px 14px; font-weight: bold; }
            QPushButton:hover { background: #a855f7; }
        """)
        self.train_abandon_btn.clicked.connect(lambda: self._train("abandonment"))
        btn_row.addWidget(self.train_abandon_btn)

        self.train_sent_btn = QPushButton("💬 Train Review Sentiment NLP Model")
        self.train_sent_btn.setStyleSheet("""
            QPushButton { background: #059669; color: #ffffff; border-radius: 6px; padding: 8px 14px; font-weight: bold; }
            QPushButton:hover { background: #10b981; }
        """)
        self.train_sent_btn.clicked.connect(lambda: self._train("sentiment"))
        btn_row.addWidget(self.train_sent_btn)

        btn_row.addStretch()
        train_layout.addLayout(btn_row)

        self.status_label = QLabel("Models ready. Click any training button above to train or retrain.")
        self.status_label.setStyleSheet("font-size: 12px; color: #94a3b8; background: transparent; padding-top: 4px;")
        train_layout.addWidget(self.status_label)

        layout.addWidget(train_deck)

        # ── Model Results Cards ──
        # 1. Review Sentiment NLP Card
        self.sentiment_card = self._make_card("💬 Review Sentiment & Rating NLP Model (21,000+ Real Reviews)")
        self.sentiment_label = self.sentiment_card.findChild(QLabel, "content")
        layout.addWidget(self.sentiment_card)

        # 2. Purchase Model Card
        self.purchase_card = self._make_card("🎯 Purchase Prediction Model (Random Forest + Baseline)")
        self.purchase_label = self.purchase_card.findChild(QLabel, "content")
        layout.addWidget(self.purchase_card)

        # 3. Abandonment Model Card
        self.abandon_card = self._make_card("🛒 Cart Abandonment Model (Random Forest + Baseline)")
        self.abandon_label = self.abandon_card.findChild(QLabel, "content")
        layout.addWidget(self.abandon_card)

        # 4. Feature Importance Card
        self.importance_card = self._make_card("📊 Top Predictive Features & Keywords")
        self.importance_label = self.importance_card.findChild(QLabel, "content")
        layout.addWidget(self.importance_card)

        layout.addStretch()
        scroll.setWidget(content)
        page_layout.addWidget(scroll)

        # Trigger initial calculation
        self._recalculate_live_simulation()

    def _make_slider(self, label_text: str, min_val: int, max_val: int, default_val: int, fmt: str):
        row = QHBoxLayout()
        lbl = QLabel(label_text)
        lbl.setFixedWidth(160)
        lbl.setStyleSheet("color: #cbd5e1; font-size: 11px; background: transparent;")
        row.addWidget(lbl)

        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default_val)
        slider.setStyleSheet("""
            QSlider::groove:horizontal { background: #1e1f36; height: 6px; border-radius: 3px; }
            QSlider::sub-page:horizontal { background: #6366f1; border-radius: 3px; }
            QSlider::handle:horizontal { background: #ffffff; width: 14px; margin-top: -4px; margin-bottom: -4px; border-radius: 7px; }
        """)
        row.addWidget(slider, 2)

        val_lbl = QLabel(fmt.format(default_val))
        val_lbl.setFixedWidth(80)
        val_lbl.setStyleSheet("color: #a5b4fc; font-weight: bold; font-size: 11px; background: transparent;")
        row.addWidget(val_lbl)

        slider.valueChanged.connect(lambda v, l=val_lbl, f=fmt: (l.setText(f.format(v)), self._recalculate_live_simulation()))
        return row, slider

    def _recalculate_live_simulation(self):
        """Update live probabilities as user adjusts sliders."""
        from src.ml.models import ml_manager

        # Extract values
        c_val = self.slider_cart_val.itemAt(1).widget().value()
        dur = self.slider_dur.itemAt(1).widget().value()
        views = self.slider_views.itemAt(1).widget().value()
        rem = self.slider_rem.itemAt(1).widget().value()
        dev = self.combo_device.currentText().lower()
        is_ret = 1 if self.combo_cust.currentIndex() == 1 else 0

        # Purchase Pred
        pur_res = ml_manager.predict_live_purchase({
            'session_duration_min': dur,
            'products_viewed': views,
            'cart_adds': 2 if views > 2 else 1,
            'searches': 1,
            'is_returning_customer': is_ret,
            'device': dev
        })
        p_prob = int(pur_res['purchase_probability'] * 100)
        self.lbl_purchase_prob.setText(f"{p_prob}% ({pur_res['intent_level']})")
        self.bar_purchase.setValue(p_prob)

        # Abandonment Pred
        ab_res = ml_manager.predict_live_abandonment({
            'cart_value': c_val,
            'num_items': max(1, views // 2),
            'items_removed': rem,
            'session_duration_min': dur,
            'device': dev,
            'checkout_started': 1 if dur > 8 else 0
        })
        a_prob = int(ab_res['abandonment_probability'] * 100)
        self.lbl_abandon_prob.setText(f"{a_prob}% ({ab_res['risk_level']})")
        self.bar_abandon.setValue(a_prob)

        # Action
        self.lbl_action.setText(f"💡 Recommended Action: {ab_res['recommended_action']}")

    def _make_card(self, title_text):
        card = QFrame()
        card.setStyleSheet("QFrame { background: #22233d; border: 1px solid #2a2b4a; border-radius: 12px; padding: 16px; }")
        layout = QVBoxLayout(card)
        title = QLabel(title_text)
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #c0c0e0; background: transparent;")
        layout.addWidget(title)
        content = QLabel("Model ready for training / evaluation. Click a training button above.")
        content.setObjectName("content")
        content.setStyleSheet("font-size: 12px; color: #a0a0c0; background: transparent; line-height: 1.6; font-family: 'Consolas', monospace;")
        content.setWordWrap(True)
        layout.addWidget(content)
        return card

    def _train(self, model_type):
        type_names = {'purchase': 'Purchase', 'abandonment': 'Cart Abandonment', 'sentiment': 'Review Sentiment NLP'}
        name = type_names.get(model_type, model_type)
        self.status_label.setText(f"⏳ Training {name} model... Please wait a moment.")
        self.train_purchase_btn.setEnabled(False)
        self.train_abandon_btn.setEnabled(False)
        self.train_sent_btn.setEnabled(False)

        self._thread = TrainThread(model_type)
        self._thread.finished.connect(lambda r: self._on_trained(model_type, r))
        self._thread.error.connect(self._on_error)
        self._thread.start()

    def _on_trained(self, model_type, results):
        self.train_purchase_btn.setEnabled(True)
        self.train_abandon_btn.setEnabled(True)
        self.train_sent_btn.setEnabled(True)
        self.status_label.setText(f"✅ Training completed successfully for {model_type.title()} model!")

        if 'error' in results:
            self.status_label.setText(f"⚠️ {results['error']}")
            return

        if model_type == 'sentiment':
            lines = []
            lines.append(f"  Dataset: {results.get('dataset_size', 21000):,} Real Customer Reviews Analyzed\n")
            for m_key in ['baseline_nb', 'primary_lr']:
                if m_key in results:
                    m = results[m_key]
                    lines.append(f"  ── {m['model']} ──")
                    lines.append(f"    Overall Accuracy: {m['accuracy']:.4f}  |  Weighted F1-Score: {m['f1']:.4f}")
                    cm = m.get('confusion_matrix', [])
                    if len(cm) == 3:
                        lines.append(f"    Confusion Matrix [Neg, Neu, Pos]:")
                        lines.append(f"      Actual Neg: [{cm[0][0]:>5}, {cm[0][1]:>5}, {cm[0][2]:>5}]")
                        lines.append(f"      Actual Neu: [{cm[1][0]:>5}, {cm[1][1]:>5}, {cm[1][2]:>5}]")
                        lines.append(f"      Actual Pos: [{cm[2][0]:>5}, {cm[2][1]:>5}, {cm[2][2]:>5}]")
                    lines.append("")

            self.sentiment_label.setText("\n".join(lines))

            # Keywords
            if 'top_keywords' in results:
                kw = results['top_keywords']
                kw_lines = ["  Top Predictive Keywords Extracted by Model:\n"]
                kw_lines.append(f"  🟢 POSITIVE PRAISE:   {', '.join(kw.get('Positive', [])[:8])}")
                kw_lines.append(f"  🔴 NEGATIVE FRICTION: {', '.join(kw.get('Negative', [])[:8])}")
                kw_lines.append(f"  🟡 NEUTRAL / MODERATE: {', '.join(kw.get('Neutral', [])[:8])}")
                self.importance_label.setText("\n".join(kw_lines))

        else:
            target_label = self.purchase_label if model_type == 'purchase' else self.abandon_label
            lines = []
            for model_name in ['baseline_logistic', 'random_forest']:
                if model_name in results:
                    m = results[model_name]
                    lines.append(f"\n  ── {m['model']} ──")
                    lines.append(f"    Accuracy:  {m['accuracy']:.4f}  |  F1-Score:  {m['f1']:.4f}  |  ROC-AUC: {m['roc_auc']:.4f}")
                    cm = m['confusion_matrix']
                    if cm and len(cm) == 2:
                        lines.append(f"    Confusion Matrix:  [[{cm[0][0]:>5}, {cm[0][1]:>5}], [{cm[1][0]:>5}, {cm[1][1]:>5}]]")

            target_label.setText("\n".join(lines))

            if 'feature_importance' in results:
                imp = results['feature_importance']
                imp_lines = ["  Top Behavioral Features:\n"]
                for feat, val in imp.items():
                    bar = "█" * int(val * 150) + "░" * max(0, 15 - int(val * 150))
                    imp_lines.append(f"  {feat:28s}  {bar}  {val:.4f}")
                self.importance_label.setText("\n".join(imp_lines))

        self._recalculate_live_simulation()

    def _on_error(self, error):
        self.train_purchase_btn.setEnabled(True)
        self.train_abandon_btn.setEnabled(True)
        self.train_sent_btn.setEnabled(True)
        self.status_label.setText(f"❌ Error: {error}")

    def refresh(self):
        self._recalculate_live_simulation()
