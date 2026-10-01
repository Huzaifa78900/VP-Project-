"""
Battery details page for PowerGuard OS Monitor.
Provides a comprehensive battery health breakdown, visual battery gauge,
charging status, discharge time estimation, and pyqtgraph trend.
"""
from typing import List, Tuple
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QProgressBar, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt
from database.models import BatterySnapshot
from widgets.charts import BatteryTrendChart
from resources.styles import (
    COLOR_BG, COLOR_SURFACE, COLOR_BORDER, COLOR_BORDER_LIGHT,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    COLOR_PRIMARY, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER
)
from resources.icons import get_pixmap


class BatteryPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet(f"background-color: {COLOR_BG}; border: none;")

        content_widget = QWidget()
        content_widget.setStyleSheet(f"background-color: {COLOR_BG};")
        self.main_layout = QVBoxLayout(content_widget)
        self.main_layout.setContentsMargins(28, 24, 28, 28)
        self.main_layout.setSpacing(20)

        scroll_area.setWidget(content_widget)
        outer_layout.addWidget(scroll_area)

        # 1. Header
        header = QVBoxLayout()
        title_lbl = QLabel("Battery & Power Intelligence")
        title_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 24px; font-weight: 700;")
        sub_lbl = QLabel("Accurate hardware power telemetry, charging cycle state, discharge rates, and health.")
        sub_lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 13px;")
        header.addWidget(title_lbl)
        header.addWidget(sub_lbl)
        self.main_layout.addLayout(header)

        # 2. Main Battery Gauge Card & Stats Row
        top_row = QHBoxLayout()
        top_row.setSpacing(16)

        # Left: Large Battery Visualization Card
        self.gauge_card = self._build_gauge_card()
        top_row.addWidget(self.gauge_card, stretch=45)

        # Right: Battery Health & Threshold Card
        self.stats_card = self._build_stats_card()
        top_row.addWidget(self.stats_card, stretch=55)

        self.main_layout.addLayout(top_row)

        # 3. Battery Trend Chart
        self.chart = BatteryTrendChart(self)
        self.main_layout.addWidget(self.chart)

    def _build_gauge_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("BatteryGaugeCard")
        card.setStyleSheet(f"""
            QFrame#BatteryGaugeCard {{
                background-color: {COLOR_SURFACE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.status_icon = QLabel()
        self.status_icon.setFixedSize(48, 48)
        self.status_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_icon.setStyleSheet("background-color: #ECFDF5; border-radius: 24px;")
        self.status_icon.setPixmap(get_pixmap("leaf", color=COLOR_SUCCESS, size=28))
        layout.addWidget(self.status_icon, alignment=Qt.AlignmentFlag.AlignCenter)

        self.percent_label = QLabel("0%")
        self.percent_label.setStyleSheet(f"""
            color: {COLOR_TEXT_PRIMARY};
            font-size: 44px;
            font-weight: 800;
        """)
        layout.addWidget(self.percent_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.state_label = QLabel("Discharging")
        self.state_label.setStyleSheet(f"""
            color: {COLOR_TEXT_SECONDARY};
            font-size: 14px;
            font-weight: 600;
        """)
        layout.addWidget(self.state_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.time_label = QLabel("Calculating remaining...")
        self.time_label.setStyleSheet(f"""
            color: {COLOR_TEXT_MUTED};
            font-size: 13px;
        """)
        layout.addWidget(self.time_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Horizontal progress bar
        self.bar = QProgressBar()
        self.bar.setFixedHeight(8)
        self.bar.setTextVisible(False)
        self.bar.setRange(0, 100)
        self.bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #EFEBE3;
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {COLOR_SUCCESS};
                border-radius: 4px;
            }}
        """)
        layout.addWidget(self.bar)

        return card

    def _build_stats_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("BatteryStatsCard")
        card.setStyleSheet(f"""
            QFrame#BatteryStatsCard {{
                background-color: {COLOR_SURFACE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("Power Subsystem Properties")
        title.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 14px; font-weight: 700;")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(12)

        # 1. Power Source
        grid.addWidget(self._make_prop_label("Power Source"), 0, 0)
        self.prop_source = self._make_val_label("Battery Power")
        grid.addWidget(self.prop_source, 0, 1)

        # 2. Charging State
        grid.addWidget(self._make_prop_label("AC Connection"), 1, 0)
        self.prop_plugged = self._make_val_label("Unplugged")
        grid.addWidget(self.prop_plugged, 1, 1)

        # 3. Current Mode
        grid.addWidget(self._make_prop_label("Calculated Mode"), 2, 0)
        self.prop_mode = self._make_val_label("Normal Mode")
        grid.addWidget(self.prop_mode, 2, 1)

        # 4. Power Saver Threshold
        grid.addWidget(self._make_prop_label("Warning Threshold"), 3, 0)
        self.prop_warn = self._make_val_label("30% (Power Saver)")
        grid.addWidget(self.prop_warn, 3, 1)

        # 5. Emergency Threshold
        grid.addWidget(self._make_prop_label("Critical Threshold"), 4, 0)
        self.prop_crit = self._make_val_label("15% (Emergency)")
        grid.addWidget(self.prop_crit, 4, 1)

        layout.addLayout(grid)
        layout.addStretch()
        return card

    def _make_prop_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12.5px; font-weight: 500;")
        return lbl

    def _make_val_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 12.5px; font-weight: 600;")
        return lbl

    def update_battery(self, battery: BatterySnapshot, mode: str):
        if not battery.is_available:
            self.percent_label.setText("100%")
            self.state_label.setText("Connected to AC Power")
            self.time_label.setText("Desktop workstation (no battery sensor)")
            self.bar.setValue(100)
            self.prop_source.setText("Direct AC Wall Outlet")
            self.prop_plugged.setText("Plugged In")
            self.prop_mode.setText(f"{mode} Mode")
            return

        self.percent_label.setText(f"{int(battery.percent)}%")
        self.state_label.setText(battery.status_str)
        self.time_label.setText(battery.time_str)
        self.bar.setValue(int(battery.percent))

        color = COLOR_SUCCESS if battery.percent > 30 else (COLOR_WARNING if battery.percent > 15 else COLOR_DANGER)
        self.bar.setStyleSheet(f"""
            QProgressBar {{ background-color: #EFEBE3; border: none; border-radius: 4px; }}
            QProgressBar::chunk {{ background-color: {color}; border-radius: 4px; }}
        """)

        self.prop_source.setText(battery.power_source)
        self.prop_plugged.setText("Connected (Charging)" if battery.plugged else "Disconnected (On Battery)")
        self.prop_mode.setText(f"{mode} Mode")

    def update_trend(self, history: List[Tuple[str, float, int]]):
        self.chart.update_data(history)
