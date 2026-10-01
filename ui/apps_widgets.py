"""
Apps & Widgets page for PowerGuard OS Monitor.
Provides an overview of application footprint, top memory/CPU hogs,
and modular widget summaries.
"""
from typing import List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QProgressBar, QScrollArea, QPushButton, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from database.models import ProcessItem
from resources.styles import (
    COLOR_BG, COLOR_SURFACE, COLOR_BORDER, COLOR_BORDER_LIGHT,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    COLOR_PRIMARY, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER
)
from resources.icons import get_icon, get_pixmap


class AppsWidgetsPage(QWidget):
    navigate_requested = pyqtSignal(str)

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
        title_lbl = QLabel("Apps & Resource Footprint")
        title_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 24px; font-weight: 700;")
        sub_lbl = QLabel("Identify heavy background processes, active window consumption, and resource footprint.")
        sub_lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 13px;")
        header.addWidget(title_lbl)
        header.addWidget(sub_lbl)
        self.main_layout.addLayout(header)

        # 2. Action Banner
        banner = self._build_banner()
        self.main_layout.addWidget(banner)

        # 3. Two Columns: Top CPU Consumers & Top RAM Consumers
        lists_layout = QHBoxLayout()
        lists_layout.setSpacing(16)

        self.cpu_apps_card = self._build_category_card("Top CPU Consuming Apps", "cpu", COLOR_PRIMARY)
        lists_layout.addWidget(self.cpu_apps_card)

        self.ram_apps_card = self._build_category_card("Top Memory (RAM) Consuming Apps", "ram", COLOR_SUCCESS)
        lists_layout.addWidget(self.ram_apps_card)

        self.main_layout.addLayout(lists_layout)

    def _build_banner(self) -> QFrame:
        banner = QFrame()
        banner.setObjectName("AppsBanner")
        banner.setStyleSheet(f"""
            QFrame#AppsBanner {{
                background-color: {COLOR_SURFACE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 12px;
            }}
        """)
        layout = QHBoxLayout(banner)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        icon_lbl = QLabel()
        icon_lbl.setFixedSize(36, 36)
        icon_lbl.setStyleSheet("background-color: #F5F3FF; border-radius: 8px;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setPixmap(get_pixmap("apps", color=COLOR_PRIMARY, size=20))
        layout.addWidget(icon_lbl)

        text_col = QVBoxLayout()
        t1 = QLabel("Manage Running Processes & Safety Wishlist")
        t1.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 14px; font-weight: 700;")
        t2 = QLabel("Configure priority throttling, suspend rogue processes, or add essential apps to the protected wishlist.")
        t2.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 12px;")
        text_col.addWidget(t1)
        text_col.addWidget(t2)
        layout.addLayout(text_col)

        layout.addStretch()

        btn_proc = QPushButton("Open Process Manager")
        btn_proc.setIcon(get_icon("processes", color=COLOR_TEXT_PRIMARY, size=15))
        btn_proc.clicked.connect(lambda: self.navigate_requested.emit("processes"))
        layout.addWidget(btn_proc)

        btn_wish = QPushButton("Manage Wishlist")
        btn_wish.setIcon(get_icon("protected", color=COLOR_TEXT_PRIMARY, size=15))
        btn_wish.clicked.connect(lambda: self.navigate_requested.emit("protected_apps"))
        layout.addWidget(btn_wish)

        return banner

    def _build_category_card(self, title: str, icon_name: str, color_hex: str) -> QFrame:
        card = QFrame()
        card.setObjectName("AppCategoryCard")
        card.setStyleSheet(f"""
            QFrame#AppCategoryCard {{
                background-color: {COLOR_SURFACE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        top_row = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(22, 22)
        icon_lbl.setPixmap(get_pixmap(icon_name, color=color_hex, size=18))
        top_row.addWidget(icon_lbl)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px; font-weight: 700;")
        top_row.addWidget(title_lbl)
        top_row.addStretch()
        layout.addLayout(top_row)

        rows_container = QVBoxLayout()
        rows_container.setSpacing(10)
        layout.addLayout(rows_container)
        layout.addStretch()

        card.rows_container = rows_container
        return card

    def update_processes(self, procs: List[ProcessItem]):
        # Top CPU
        filtered_cpu = [p for p in procs if p.pid != 0 and "idle" not in p.name.lower()]
        filtered_cpu.sort(key=lambda x: x.cpu_percent, reverse=True)
        self._populate_category(self.cpu_apps_card, filtered_cpu[:6], "cpu")

        # Top RAM
        filtered_ram = [p for p in procs if p.pid != 0]
        filtered_ram.sort(key=lambda x: x.memory_mb, reverse=True)
        self._populate_category(self.ram_apps_card, filtered_ram[:6], "ram")

    def _populate_category(self, card: QFrame, items: List[ProcessItem], metric_type: str):
        c = card.rows_container
        while c.count():
            item = c.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for p in items:
            row = QWidget()
            r_layout = QHBoxLayout(row)
            r_layout.setContentsMargins(0, 0, 0, 0)
            r_layout.setSpacing(10)

            name_lbl = QLabel(p.name)
            name_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 12px; font-weight: 600;")
            name_lbl.setFixedWidth(130)

            bar = QProgressBar()
            bar.setFixedHeight(6)
            bar.setTextVisible(False)
            bar.setRange(0, 100)

            if metric_type == "cpu":
                bar.setValue(min(100, int(p.cpu_percent)))
                bar.setStyleSheet(f"""
                    QProgressBar {{ background-color: #EFEBE3; border: none; border-radius: 3px; }}
                    QProgressBar::chunk {{ background-color: {COLOR_PRIMARY}; border-radius: 3px; }}
                """)
                val_lbl = QLabel(f"{p.cpu_percent:.1f}%")
            else:
                pct = min(100, int((p.memory_mb / 4096.0) * 100))
                bar.setValue(pct)
                bar.setStyleSheet(f"""
                    QProgressBar {{ background-color: #EFEBE3; border: none; border-radius: 3px; }}
                    QProgressBar::chunk {{ background-color: {COLOR_SUCCESS}; border-radius: 3px; }}
                """)
                val_lbl = QLabel(f"{p.memory_mb:.0f} MB")

            val_lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 12px; font-weight: 600;")
            val_lbl.setFixedWidth(65)
            val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            r_layout.addWidget(name_lbl)
            r_layout.addWidget(bar)
            r_layout.addWidget(val_lbl)

            c.addWidget(row)
