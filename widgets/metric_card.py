"""
Metric card widget for PowerGuard OS Monitor.
Displays real-time system metrics (Battery, CPU, RAM, Disk)
with clean typography, modern progress indicators, and status badges.
"""
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
)
from PyQt6.QtCore import Qt
from resources.styles import (
    COLOR_SURFACE, COLOR_BORDER, COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED, COLOR_PRIMARY,
    COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER
)
from resources.icons import get_pixmap


class MetricCard(QFrame):
    def __init__(self, title: str, icon_name: str, parent=None):
        super().__init__(parent)
        self.title_str = title
        self.icon_name = icon_name

        self.setObjectName("MetricCard")
        self.setStyleSheet(f"""
            QFrame#MetricCard {{
                background-color: {COLOR_SURFACE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 12px;
            }}
            QFrame#MetricCard:hover {{
                border-color: #D3C9B8;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Top row: Title and Icon
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel(title.upper())
        self.title_label.setStyleSheet(f"""
            color: {COLOR_TEXT_SECONDARY};
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.6px;
        """)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(28, 28)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet(f"""
            background-color: #F8F5EE;
            border-radius: 6px;
            border: 1px solid {COLOR_BORDER};
        """)
        self._update_icon(COLOR_TEXT_SECONDARY)

        top_row.addWidget(self.title_label)
        top_row.addStretch()
        top_row.addWidget(self.icon_label)
        layout.addLayout(top_row)

        # Main Value (e.g. 68%, 12%, 42%, 31%)
        self.value_label = QLabel("0%")
        self.value_label.setStyleSheet(f"""
            color: {COLOR_TEXT_PRIMARY};
            font-size: 28px;
            font-weight: 700;
            margin-top: 2px;
        """)
        layout.addWidget(self.value_label)

        # Subtitle (e.g. "5h 42m remaining", "2.30 GHz", "6.7 GB / 16 GB")
        self.subtitle_label = QLabel("Loading system telemetry...")
        self.subtitle_label.setStyleSheet(f"""
            color: {COLOR_TEXT_MUTED};
            font-size: 12px;
            font-weight: 500;
        """)
        layout.addWidget(self.subtitle_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(5)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.set_progress_color(COLOR_PRIMARY)
        layout.addWidget(self.progress_bar)

    def _update_icon(self, color_hex: str):
        pixmap = get_pixmap(self.icon_name, color=color_hex, size=16)
        self.icon_label.setPixmap(pixmap)

    def set_progress_color(self, color_hex: str):
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #EFEBE3;
                border: none;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {color_hex};
                border-radius: 2px;
            }}
        """)

    def update_data(self, main_val: str, subtitle: str, progress_pct: float = None, color_type: str = "primary"):
        self.value_label.setText(main_val)
        self.subtitle_label.setText(subtitle)

        if progress_pct is not None:
            clamped = max(0, min(100, int(progress_pct)))
            self.progress_bar.setValue(clamped)

        # Select color based on status or type
        if color_type == "success":
            color = COLOR_SUCCESS
        elif color_type == "warning":
            color = COLOR_WARNING
        elif color_type == "danger":
            color = COLOR_DANGER
        else:
            color = COLOR_PRIMARY

        self.set_progress_color(color)
        self._update_icon(color)
