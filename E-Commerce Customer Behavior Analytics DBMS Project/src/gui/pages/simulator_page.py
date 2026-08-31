"""Simulator Control Page — Start/stop event simulator, configure parameters."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QSpinBox, QDoubleSpinBox, QScrollArea, QPlainTextEdit, QGroupBox, QGridLayout
)
from PySide6.QtCore import Qt, QTimer


class SimulatorPage(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_stats)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("⚡ Event Simulator")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #ffffff;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Controls row
        controls = QHBoxLayout()
        controls.setSpacing(12)

        self.start_btn = QPushButton("▶ Start Simulator")
        self.start_btn.setProperty("class", "success")
        self.start_btn.setStyleSheet("background-color: #16a34a; font-weight: bold; padding: 12px 24px;")
        self.start_btn.clicked.connect(self._start)
        controls.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setStyleSheet("background-color: #dc2626; font-weight: bold; padding: 12px 24px;")
        self.stop_btn.clicked.connect(self._stop)
        self.stop_btn.setEnabled(False)
        controls.addWidget(self.stop_btn)

        controls.addStretch()

        self.status_label = QLabel("● Stopped")
        self.status_label.setStyleSheet("font-size: 14px; color: #f87171; font-weight: bold;")
        controls.addWidget(self.status_label)
        layout.addLayout(controls)

        # Config + Stats row
        config_stats = QHBoxLayout()
        config_stats.setSpacing(16)

        # Configuration
        config_group = QGroupBox("Configuration")
        config_grid = QGridLayout(config_group)

        config_grid.addWidget(QLabel("Sessions per batch:"), 0, 0)
        self.batch_spin = QSpinBox()
        self.batch_spin.setRange(5, 200)
        self.batch_spin.setValue(50)
        config_grid.addWidget(self.batch_spin, 0, 1)

        config_grid.addWidget(QLabel("Batch interval (sec):"), 1, 0)
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 60)
        self.interval_spin.setValue(5)
        config_grid.addWidget(self.interval_spin, 1, 1)

        config_grid.addWidget(QLabel("Cart add probability:"), 2, 0)
        self.cart_prob_spin = QDoubleSpinBox()
        self.cart_prob_spin.setRange(0.01, 1.0)
        self.cart_prob_spin.setSingleStep(0.05)
        self.cart_prob_spin.setValue(0.15)
        config_grid.addWidget(self.cart_prob_spin, 2, 1)

        config_grid.addWidget(QLabel("Cart abandon probability:"), 3, 0)
        self.abandon_prob_spin = QDoubleSpinBox()
        self.abandon_prob_spin.setRange(0.01, 1.0)
        self.abandon_prob_spin.setSingleStep(0.05)
        self.abandon_prob_spin.setValue(0.70)
        config_grid.addWidget(self.abandon_prob_spin, 3, 1)

        config_grid.addWidget(QLabel("Mobile ratio:"), 4, 0)
        self.mobile_spin = QDoubleSpinBox()
        self.mobile_spin.setRange(0.1, 0.9)
        self.mobile_spin.setSingleStep(0.05)
        self.mobile_spin.setValue(0.55)
        config_grid.addWidget(self.mobile_spin, 4, 1)

        config_stats.addWidget(config_group)

        # Scenario presets
        scenario_group = QGroupBox("Scenario Presets")
        scenario_layout = QVBoxLayout(scenario_group)

        normal_btn = QPushButton("📊 Normal Traffic")
        normal_btn.clicked.connect(lambda: self._apply_preset(0.15, 0.70, 0.55))
        scenario_layout.addWidget(normal_btn)

        mobile_friction = QPushButton("📱 Mobile Friction")
        mobile_friction.setStyleSheet("background-color: #ea580c;")
        mobile_friction.clicked.connect(lambda: self._apply_preset(0.15, 0.92, 0.80))
        scenario_layout.addWidget(mobile_friction)

        high_intent = QPushButton("🎯 High Purchase Intent")
        high_intent.setStyleSheet("background-color: #16a34a;")
        high_intent.clicked.connect(lambda: self._apply_preset(0.35, 0.40, 0.55))
        scenario_layout.addWidget(high_intent)

        low_engage = QPushButton("😴 Low Engagement")
        low_engage.setStyleSheet("background-color: #ca8a04;")
        low_engage.clicked.connect(lambda: self._apply_preset(0.05, 0.85, 0.55))
        scenario_layout.addWidget(low_engage)

        scenario_layout.addStretch()
        config_stats.addWidget(scenario_group)

        # Live stats
        stats_group = QGroupBox("Live Statistics")
        stats_layout = QVBoxLayout(stats_group)
        self.stats_label = QLabel("No data yet. Start the simulator.")
        self.stats_label.setStyleSheet("font-size: 14px; color: #a0a0c0; line-height: 2.0; font-family: 'Consolas', monospace;")
        stats_layout.addWidget(self.stats_label)
        config_stats.addWidget(stats_group)

        layout.addLayout(config_stats)

        # Event log
        log_label = QLabel("Event Log")
        log_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #c0c0e0;")
        layout.addWidget(log_label)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(200)
        self.log.setStyleSheet("""
            QPlainTextEdit { 
                background: #12132a; border: 1px solid #2a2b4a; border-radius: 8px; 
                color: #4ade80; font-family: 'Consolas', monospace; font-size: 12px; padding: 8px;
            }
        """)
        layout.addWidget(self.log)

    def _apply_preset(self, cart_prob, abandon_prob, mobile_ratio):
        self.cart_prob_spin.setValue(cart_prob)
        self.abandon_prob_spin.setValue(abandon_prob)
        self.mobile_spin.setValue(mobile_ratio)
        self.log.appendPlainText(f"[Preset] Cart: {cart_prob}, Abandon: {abandon_prob}, Mobile: {mobile_ratio}")

        # Update simulator if running
        try:
            from src.simulator.event_simulator import simulator
            if simulator.running:
                simulator.update_config(
                    cart_add_prob=cart_prob,
                    cart_abandon_prob=abandon_prob,
                    mobile_ratio=mobile_ratio,
                )
                self.log.appendPlainText("[Config updated on running simulator]")
        except Exception:
            pass

    def _start(self):
        try:
            from src.simulator.event_simulator import simulator

            simulator.events_per_batch = self.batch_spin.value()
            simulator.batch_interval = self.interval_spin.value()
            simulator.cart_add_prob = self.cart_prob_spin.value()
            simulator.cart_abandon_prob = self.abandon_prob_spin.value()
            simulator.mobile_ratio = self.mobile_spin.value()

            simulator.add_callback(self._on_simulator_update)
            simulator.start()

            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_label.setText("● Running")
            self.status_label.setStyleSheet("font-size: 14px; color: #4ade80; font-weight: bold;")
            self.log.appendPlainText("[Simulator started]")

            self._timer.start(2000)  # Update stats every 2 sec
        except Exception as e:
            self.log.appendPlainText(f"[Error] {e}")

    def _stop(self):
        try:
            from src.simulator.event_simulator import simulator
            simulator.stop()
        except Exception:
            pass

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("● Stopped")
        self.status_label.setStyleSheet("font-size: 14px; color: #f87171; font-weight: bold;")
        self.log.appendPlainText("[Simulator stopped]")
        self._timer.stop()

    def _on_simulator_update(self, message, stats):
        self.log.appendPlainText(f"  {message}")

    def _update_stats(self):
        try:
            from src.simulator.event_simulator import simulator
            stats = simulator.get_stats()
            self.stats_label.setText(
                f"  Batches:   {stats.get('batches', 0)}\n"
                f"  Sessions:  {stats.get('sessions', 0):,}\n"
                f"  Events:    {stats.get('events', 0):,}\n"
                f"  Carts:     {stats.get('carts', 0):,}\n"
                f"  Orders:    {stats.get('orders', 0):,}\n"
            )
        except Exception:
            pass

    def refresh(self):
        pass
