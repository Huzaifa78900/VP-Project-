"""
Supportive dashboard cards for PowerGuard OS Monitor:
- Quick Actions Panel
- Top Apps by Resource Usage Card
- Protected Apps Preview Card
- Recent Activity Log Card
"""
from typing import List
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from database.models import ProcessItem, ProtectedAppEntry, OptimizationLogEntry
from resources.styles import (
    COLOR_SURFACE, COLOR_BORDER, COLOR_BORDER_LIGHT, COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED, COLOR_PRIMARY,
    COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER
)
from resources.icons import get_icon, get_pixmap


class QuickActionsPanel(QFrame):
    """
    Quick Actions card on dashboard: View Logs, Export CSV, Manage Wishlist.
    """
    view_logs_clicked = pyqtSignal()
    export_csv_clicked = pyqtSignal()
    manage_wishlist_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("QuickActionsPanel")
        self.setStyleSheet(f"""
            QFrame#QuickActionsPanel {{
                background-color: {COLOR_SURFACE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header = QLabel("QUICK ACTIONS")
        header.setStyleSheet(f"""
            color: {COLOR_TEXT_SECONDARY};
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.6px;
        """)
        layout.addWidget(header)

        # 1. View Logs
        self.logs_btn = QPushButton("View Logs")
        self.logs_btn.setIcon(get_icon("logs", color=COLOR_TEXT_PRIMARY, size=15))
        self.logs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.logs_btn.clicked.connect(self.view_logs_clicked.emit)
        layout.addWidget(self.logs_btn)

        # 2. Export CSV
        self.export_btn = QPushButton("Export CSV")
        self.export_btn.setIcon(get_icon("export", color=COLOR_TEXT_PRIMARY, size=15))
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.clicked.connect(self.export_csv_clicked.emit)
        layout.addWidget(self.export_btn)

        # 3. Manage Wishlist
        self.wishlist_btn = QPushButton("Manage Wishlist")
        self.wishlist_btn.setIcon(get_icon("protected", color=COLOR_TEXT_PRIMARY, size=15))
        self.wishlist_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.wishlist_btn.clicked.connect(self.manage_wishlist_clicked.emit)
        layout.addWidget(self.wishlist_btn)


class TopAppsCard(QFrame):
    """
    Bottom card: Top Apps by Battery / Resource Usage.
    Displays real running applications sorted by CPU/Memory.
    """
    manage_processes_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TopAppsCard")
        self.setStyleSheet(f"""
            QFrame#TopAppsCard {{
                background-color: {COLOR_SURFACE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 12px;
            }}
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 16, 16, 16)
        self.layout.setSpacing(10)

        # Header row
        header_row = QHBoxLayout()
        title_label = QLabel("Top Apps by Resource Usage")
        title_label.setStyleSheet(f"""
            color: {COLOR_TEXT_PRIMARY};
            font-size: 13px;
            font-weight: 700;
        """)
        header_row.addWidget(title_label)
        header_row.addStretch()

        self.layout.addLayout(header_row)

        # Container for process rows
        self.rows_container = QVBoxLayout()
        self.rows_container.setSpacing(8)
        self.layout.addLayout(self.rows_container)
        self.layout.addStretch()

    def update_apps(self, apps: List[ProcessItem]):
        # Clear existing rows
        while self.rows_container.count():
            item = self.rows_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not apps:
            empty_lbl = QLabel("No active resource-heavy applications.")
            empty_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
            self.rows_container.addWidget(empty_lbl)
            return

        for p in apps[:5]:
            row = QWidget()
            r_layout = QHBoxLayout(row)
            r_layout.setContentsMargins(0, 2, 0, 2)
            r_layout.setSpacing(10)

            # Name and PID
            name_lbl = QLabel(p.name)
            name_lbl.setStyleSheet(f"""
                color: {COLOR_TEXT_PRIMARY};
                font-size: 12px;
                font-weight: 600;
            """)
            name_lbl.setFixedWidth(130)

            # Mini Progress bar for CPU %
            bar = QProgressBar()
            bar.setFixedHeight(5)
            bar.setTextVisible(False)
            bar.setRange(0, 100)
            bar.setValue(min(100, int(p.cpu_percent)))
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: #EFEBE3;
                    border: none;
                    border-radius: 2px;
                }}
                QProgressBar::chunk {{
                    background-color: {COLOR_PRIMARY};
                    border-radius: 2px;
                }}
            """)

            # Value text e.g. "14.2%" or "820 MB"
            val_lbl = QLabel(f"{p.cpu_percent:.1f}%")
            val_lbl.setStyleSheet(f"""
                color: {COLOR_TEXT_SECONDARY};
                font-size: 12px;
                font-weight: 700;
            """)
            val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            val_lbl.setFixedWidth(45)

            r_layout.addWidget(name_lbl)
            r_layout.addWidget(bar)
            r_layout.addWidget(val_lbl)

            self.rows_container.addWidget(row)


class ProtectedAppsCard(QFrame):
    """
    Bottom card: Protected Apps (Wishlist) preview.
    """
    manage_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ProtectedAppsCard")
        self.setStyleSheet(f"""
            QFrame#ProtectedAppsCard {{
                background-color: {COLOR_SURFACE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 12px;
            }}
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 16, 16, 16)
        self.layout.setSpacing(10)

        # Header
        header_row = QHBoxLayout()
        title_label = QLabel("Protected Apps (Wishlist)")
        title_label.setStyleSheet(f"""
            color: {COLOR_TEXT_PRIMARY};
            font-size: 13px;
            font-weight: 700;
        """)
        header_row.addWidget(title_label)
        header_row.addStretch()

        self.layout.addLayout(header_row)

        self.rows_container = QVBoxLayout()
        self.rows_container.setSpacing(8)
        self.layout.addLayout(self.rows_container)
        self.layout.addStretch()

    def update_apps(self, apps: List[ProtectedAppEntry]):
        while self.rows_container.count():
            item = self.rows_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not apps:
            empty_lbl = QLabel("No apps added to protected wishlist yet.")
            empty_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
            self.rows_container.addWidget(empty_lbl)
            return

        for app in apps[:5]:
            row = QWidget()
            r_layout = QHBoxLayout(row)
            r_layout.setContentsMargins(0, 2, 0, 2)
            r_layout.setSpacing(8)

            icon_lbl = QLabel()
            icon_lbl.setFixedSize(16, 16)
            icon_lbl.setPixmap(get_pixmap("shield-check", color=COLOR_SUCCESS, size=14))

            name_lbl = QLabel(app.process_name)
            name_lbl.setStyleSheet(f"""
                color: {COLOR_TEXT_PRIMARY};
                font-size: 12px;
                font-weight: 600;
            """)

            badge = QLabel("Protected")
            badge.setStyleSheet(f"""
                background-color: #ECFDF5;
                color: {COLOR_SUCCESS};
                font-size: 10px;
                font-weight: 700;
                padding: 2px 6px;
                border-radius: 4px;
                border: 1px solid #A7F3D0;
            """)

            r_layout.addWidget(icon_lbl)
            r_layout.addWidget(name_lbl)
            r_layout.addStretch()
            r_layout.addWidget(badge)

            self.rows_container.addWidget(row)


class RecentActivityCard(QFrame):
    """
    Bottom card: Recent Activity log events from SQLite.
    """
    view_all_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("RecentActivityCard")
        self.setStyleSheet(f"""
            QFrame#RecentActivityCard {{
                background-color: {COLOR_SURFACE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 12px;
            }}
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 16, 16, 16)
        self.layout.setSpacing(10)

        header_row = QHBoxLayout()
        title_label = QLabel("Recent Activity")
        title_label.setStyleSheet(f"""
            color: {COLOR_TEXT_PRIMARY};
            font-size: 13px;
            font-weight: 700;
        """)
        header_row.addWidget(title_label)
        header_row.addStretch()

        self.layout.addLayout(header_row)

        self.rows_container = QVBoxLayout()
        self.rows_container.setSpacing(8)
        self.layout.addLayout(self.rows_container)
        self.layout.addStretch()

    def update_activity(self, logs: List[OptimizationLogEntry]):
        while self.rows_container.count():
            item = self.rows_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not logs:
            empty_lbl = QLabel("No recent system activity recorded.")
            empty_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
            self.rows_container.addWidget(empty_lbl)
            return

        for log in logs[:5]:
            row = QWidget()
            r_layout = QHBoxLayout(row)
            r_layout.setContentsMargins(0, 2, 0, 2)
            r_layout.setSpacing(8)

            dot = QLabel()
            dot.setFixedSize(8, 8)
            dot_color = COLOR_SUCCESS if "Start" in log.action or "Normal" in log.mode else (
                COLOR_WARNING if "Power" in log.mode or "Lower" in log.action else COLOR_PRIMARY
            )
            dot.setStyleSheet(f"""
                background-color: {dot_color};
                border-radius: 4px;
            """)

            desc_lbl = QLabel(f"{log.action}: {log.process_name or 'System'}")
            desc_lbl.setStyleSheet(f"""
                color: {COLOR_TEXT_PRIMARY};
                font-size: 11.5px;
                font-weight: 500;
            """)

            # Short time extraction
            time_part = log.timestamp.split(" ")[-1] if " " in log.timestamp else log.timestamp
            time_lbl = QLabel(time_part)
            time_lbl.setStyleSheet(f"""
                color: {COLOR_TEXT_MUTED};
                font-size: 10.5px;
            """)

            r_layout.addWidget(dot)
            r_layout.addWidget(desc_lbl)
            r_layout.addStretch()
            r_layout.addWidget(time_lbl)

            self.rows_container.addWidget(row)
