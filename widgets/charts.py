"""
PyQtGraph based charts for PowerGuard OS Monitor.
Provides Battery Usage Trend and live Performance telemetry charts
styled for the Warm Beige / Soft Sand palette.
"""
from datetime import datetime
from typing import List, Tuple
import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QButtonGroup, QWidget
)
from PyQt6.QtGui import QColor, QPen, QBrush
from PyQt6.QtCore import Qt, pyqtSignal
from resources.styles import (
    COLOR_SURFACE, COLOR_BORDER, COLOR_BORDER_LIGHT, COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED, COLOR_PRIMARY,
    COLOR_SUCCESS, COLOR_WARNING
)

# Enable anti-aliasing globally for crisp vectors
pg.setConfigOptions(antialias=True)


class TimeAxisItem(pg.AxisItem):
    """Custom pyqtgraph AxisItem that renders timestamps into human-readable strings."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.time_labels = {}

    def set_time_labels(self, labels: dict):
        self.time_labels = labels

    def tickStrings(self, values, scale, spacing):
        strings = []
        for val in values:
            int_val = int(round(val))
            if int_val in self.time_labels:
                strings.append(self.time_labels[int_val])
            elif len(values) > 0 and 0 <= int_val < len(self.time_labels):
                # Fallback index lookup
                strings.append(list(self.time_labels.values())[int_val])
            else:
                strings.append("")
        return strings


class BatteryTrendChart(QFrame):
    """
    Polished Battery Usage Trend chart matching Design 2.
    Shows real battery percentage readings loaded from SQLite.
    """
    filter_changed = pyqtSignal(float)  # hours

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("BatteryTrendFrame")
        self.setStyleSheet(f"""
            QFrame#BatteryTrendFrame {{
                background-color: {COLOR_SURFACE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Header bar: Title and Time Range Filter Buttons
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel("Battery Usage Trend")
        title_label.setStyleSheet(f"""
            color: {COLOR_TEXT_PRIMARY};
            font-size: 14px;
            font-weight: 700;
        """)
        header_row.addWidget(title_label)
        header_row.addStretch()

        # Filter Pills: 1h, 24h, 7d
        self.filter_group = QButtonGroup(self)
        self.filter_group.setExclusive(True)

        filters = [("1h", 1.0), ("24h", 24.0), ("7d", 168.0)]
        self.filter_btns = {}
        for text, hours in filters:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setFixedSize(40, 24)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._apply_pill_style(btn, False)
            btn.clicked.connect(lambda checked, h=hours: self._on_filter_clicked(h))
            self.filter_group.addButton(btn)
            self.filter_btns[text] = btn
            header_row.addWidget(btn)

        # Select 24h by default
        self.filter_btns["24h"].setChecked(True)
        self._apply_pill_style(self.filter_btns["24h"], True)

        layout.addLayout(header_row)

        # Pyqtgraph PlotWidget
        self.time_axis = TimeAxisItem(orientation='bottom')
        self.plot_widget = pg.PlotWidget(axisItems={'bottom': self.time_axis})
        self.plot_widget.setBackground("#FFFFFF")
        self.plot_widget.setMouseEnabled(x=False, y=False)
        self.plot_widget.hideButtons()
        self.plot_widget.showGrid(x=True, y=True, alpha=0.15)

        # Style axes
        left_axis = self.plot_widget.getAxis('left')
        left_axis.setRange(0, 100)
        left_axis.setTicks([[(0, '0%'), (25, '25%'), (50, '50%'), (75, '75%'), (100, '100%')]])
        left_axis.setPen(pg.mkPen(color="#D9D2C6", width=1))
        left_axis.setTextPen(pg.mkPen(color=COLOR_TEXT_MUTED))

        self.time_axis.setPen(pg.mkPen(color="#D9D2C6", width=1))
        self.time_axis.setTextPen(pg.mkPen(color=COLOR_TEXT_MUTED))

        # Main curve: Fresh green line with translucent soft gradient area fill
        self.pen = pg.mkPen(color=COLOR_SUCCESS, width=2.5)
        self.brush = QBrush(QColor(16, 185, 129, 35))
        self.plot_curve = self.plot_widget.plot(
            [], [],
            pen=self.pen,
            fillLevel=0,
            fillBrush=self.brush
        )

        layout.addWidget(self.plot_widget)

    def _apply_pill_style(self, btn: QPushButton, checked: bool):
        if checked:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #2D2823;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 12px;
                    font-size: 11px;
                    font-weight: 700;
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #EDE7DD;
                    color: {COLOR_TEXT_SECONDARY};
                    border: none;
                    border-radius: 12px;
                    font-size: 11px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: #E2DACB;
                }}
            """)

    def _on_filter_clicked(self, hours: float):
        for btn in self.filter_btns.values():
            self._apply_pill_style(btn, btn.isChecked())
        self.filter_changed.emit(hours)

    def update_data(self, history: List[Tuple[str, float, int]]):
        """
        Populate the plot with real historical battery readings from SQLite.
        history: list of (timestamp_str, percentage, charging_flag)
        """
        if not history:
            self.plot_curve.setData([], [])
            return

        x_vals = []
        y_vals = []
        labels = {}

        # Limit points to max 120 for clean rendering
        step = max(1, len(history) // 120)
        sampled = history[::step]

        for i, (ts_str, pct, charging) in enumerate(sampled):
            x_vals.append(i)
            y_vals.append(pct)

            # Extract time string e.g. "14:30" or "2:30 PM"
            try:
                dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                # Every few ticks, assign label
                if i % max(1, len(sampled) // 5) == 0 or i == len(sampled) - 1:
                    labels[i] = dt.strftime("%I:%M %p").lstrip('0')
            except Exception:
                labels[i] = ""

        self.time_axis.set_time_labels(labels)
        self.plot_widget.setXRange(0, max(len(x_vals) - 1, 1), padding=0.02)
        self.plot_widget.setYRange(0, 105, padding=0.02)
        self.plot_curve.setData(x_vals, y_vals)


class LiveMetricChart(QFrame):
    """
    Live rolling metric chart for CPU / RAM / Disk on the Performance page.
    """
    def __init__(self, title: str, unit: str = "%", max_val: float = 100.0, line_color: str = COLOR_PRIMARY, parent=None):
        super().__init__(parent)
        self.max_val = max_val
        self.max_points = 60
        self.history_data: List[float] = []

        self.setObjectName("LiveMetricChart")
        self.setStyleSheet(f"""
            QFrame#LiveMetricChart {{
                background-color: {COLOR_SURFACE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        # Title row
        title_row = QHBoxLayout()
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet(f"""
            color: {COLOR_TEXT_PRIMARY};
            font-size: 13px;
            font-weight: 700;
        """)
        title_row.addWidget(self.title_lbl)
        title_row.addStretch()

        self.current_val_lbl = QLabel(f"0.0 {unit}")
        self.current_val_lbl.setStyleSheet(f"""
            color: {line_color};
            font-size: 14px;
            font-weight: 700;
        """)
        title_row.addWidget(self.current_val_lbl)
        layout.addLayout(title_row)

        # Pyqtgraph plot
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("#FFFFFF")
        self.plot_widget.setMouseEnabled(x=False, y=False)
        self.plot_widget.hideButtons()
        self.plot_widget.showGrid(x=True, y=True, alpha=0.12)

        # Style axes
        left_axis = self.plot_widget.getAxis('left')
        left_axis.setPen(pg.mkPen(color="#DDD6CA", width=1))
        left_axis.setTextPen(pg.mkPen(color=COLOR_TEXT_MUTED))

        bottom_axis = self.plot_widget.getAxis('bottom')
        bottom_axis.setPen(pg.mkPen(color="#DDD6CA", width=1))
        bottom_axis.setTextPen(pg.mkPen(color=COLOR_TEXT_MUTED))

        # Color fill
        qc = QColor(line_color)
        pen = pg.mkPen(color=line_color, width=2.2)
        brush = QBrush(QColor(qc.red(), qc.green(), qc.blue(), 30))

        self.curve = self.plot_widget.plot([], [], pen=pen, fillLevel=0, fillBrush=brush)
        self.plot_widget.setYRange(0, max_val, padding=0.05)
        layout.addWidget(self.plot_widget)

    def add_point(self, value: float, display_str: str = None):
        self.history_data.append(value)
        if len(self.history_data) > self.max_points:
            self.history_data.pop(0)

        x = list(range(len(self.history_data)))
        self.curve.setData(x, self.history_data)
        self.plot_widget.setXRange(0, self.max_points, padding=0.02)

        if display_str:
            self.current_val_lbl.setText(display_str)
        else:
            self.current_val_lbl.setText(f"{value:.1f}%")
