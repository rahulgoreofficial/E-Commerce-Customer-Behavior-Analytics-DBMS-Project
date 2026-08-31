"""Predictions Page — ML model training, results, and live predictions."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QScrollArea, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal


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
            else:
                result = ml_manager.train_cart_abandonment()
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class PredictionsPage(QWidget):
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
        title = QLabel("🔮 ML Predictions")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #ffffff;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Training buttons
        btn_row = QHBoxLayout()
        self.train_purchase_btn = QPushButton("🎯 Train Purchase Model")
        self.train_purchase_btn.clicked.connect(lambda: self._train("purchase"))
        self.train_purchase_btn.setFixedWidth(220)
        btn_row.addWidget(self.train_purchase_btn)

        self.train_abandon_btn = QPushButton("🛒 Train Abandonment Model")
        self.train_abandon_btn.clicked.connect(lambda: self._train("abandonment"))
        self.train_abandon_btn.setFixedWidth(220)
        btn_row.addWidget(self.train_abandon_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.status_label = QLabel("Click a button above to train ML models.")
        self.status_label.setStyleSheet("font-size: 13px; color: #a0a0c0;")
        layout.addWidget(self.status_label)

        # Purchase model results
        self.purchase_card = self._make_card("Purchase Prediction Model")
        self.purchase_label = self.purchase_card.findChild(QLabel, "content")
        layout.addWidget(self.purchase_card)

        # Abandonment model results
        self.abandon_card = self._make_card("Cart Abandonment Prediction Model")
        self.abandon_label = self.abandon_card.findChild(QLabel, "content")
        layout.addWidget(self.abandon_card)

        # Feature importance
        self.importance_card = self._make_card("Feature Importance (Top 15)")
        self.importance_label = self.importance_card.findChild(QLabel, "content")
        layout.addWidget(self.importance_card)

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
        content = QLabel("Not trained yet. Click the train button above.")
        content.setObjectName("content")
        content.setStyleSheet("font-size: 13px; color: #a0a0c0; background: transparent; line-height: 1.6; font-family: 'Consolas', monospace;")
        content.setWordWrap(True)
        layout.addWidget(content)
        return card

    def _train(self, model_type):
        self.status_label.setText(f"⏳ Training {model_type} model... This may take a minute.")
        self.train_purchase_btn.setEnabled(False)
        self.train_abandon_btn.setEnabled(False)

        self._thread = TrainThread(model_type)
        self._thread.finished.connect(lambda r: self._on_trained(model_type, r))
        self._thread.error.connect(self._on_error)
        self._thread.start()

    def _on_trained(self, model_type, results):
        self.train_purchase_btn.setEnabled(True)
        self.train_abandon_btn.setEnabled(True)
        self.status_label.setText(f"✅ {model_type.title()} model training complete!")

        if 'error' in results:
            self.status_label.setText(f"⚠️ {results['error']}")
            return

        # Display results
        target_label = self.purchase_label if model_type == 'purchase' else self.abandon_label

        lines = []
        for model_name in ['baseline_logistic', 'random_forest']:
            if model_name in results:
                m = results[model_name]
                lines.append(f"\n  ── {m['model']} ──")
                lines.append(f"    Accuracy:  {m['accuracy']:.4f}")
                lines.append(f"    Precision: {m['precision']:.4f}")
                lines.append(f"    Recall:    {m['recall']:.4f}")
                lines.append(f"    F1-Score:  {m['f1']:.4f}")
                lines.append(f"    ROC-AUC:   {m['roc_auc']:.4f}")
                cm = m['confusion_matrix']
                if cm and len(cm) == 2:
                    lines.append(f"\n    Confusion Matrix:")
                    lines.append(f"                  Predicted")
                    lines.append(f"                  Neg    Pos")
                    lines.append(f"    Actual Neg  [{cm[0][0]:>5}  {cm[0][1]:>5}]")
                    lines.append(f"    Actual Pos  [{cm[1][0]:>5}  {cm[1][1]:>5}]")

        target_label.setText("\n".join(lines))

        # Feature importance
        if 'feature_importance' in results:
            imp = results['feature_importance']
            imp_lines = []
            for feat, val in imp.items():
                bar = "█" * int(val * 200) + "░" * max(0, 20 - int(val * 200))
                imp_lines.append(f"  {feat:30s}  {bar}  {val:.4f}")
            self.importance_label.setText("\n".join(imp_lines))

    def _on_error(self, error):
        self.train_purchase_btn.setEnabled(True)
        self.train_abandon_btn.setEnabled(True)
        self.status_label.setText(f"❌ Error: {error}")

    def refresh(self):
        pass  # Results persist until retrained
