"""
Sidebar navigation widget for PowerGuard OS Monitor.
Faithfully reproduces Design 2: Warm Beige / Soft Sand.
Includes PowerGuard branding, active nav indicators, and a live health card at the bottom.
"""
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QButtonGroup, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from resources.styles import (
    COLOR_SIDEBAR, COLOR_BORDER, COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED, COLOR_PRIMARY,
    COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER
)
from resources.icons import get_icon, get_pixmap


class NavButton(QPushButton):
    def __init__(self, text: str, icon_name: str, page_id: str, parent=None):
        super().__init__(text, parent)
        self.page_id = page_id
        self.icon_name = icon_name
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(40)

        self._update_style(False)

    def _update_style(self, checked: bool):
        if checked:
            self.setIcon(get_icon(self.icon_name, color=COLOR_TEXT_PRIMARY, size=16))
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: #E2D7C7;
                    color: {COLOR_TEXT_PRIMARY};
                    border: none;
                    border-radius: 8px;
                    padding-left: 14px;
                    text-align: left;
                    font-size: 13px;
                    font-weight: 600;
                }}
            """)
        else:
            self.setIcon(get_icon(self.icon_name, color=COLOR_TEXT_SECONDARY, size=16))
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {COLOR_TEXT_SECONDARY};
                    border: none;
                    border-radius: 8px;
                    padding-left: 14px;
                    text-align: left;
                    font-size: 13px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: #EAE2D5;
                    color: {COLOR_TEXT_PRIMARY};
                }}
            """)


class SystemHealthSidebarCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HealthCard")
        self.setStyleSheet(f"""
            QFrame#HealthCard {{
                background-color: #FCFAF7;
                border: 1px solid {COLOR_BORDER};
                border-radius: 10px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        # Top row: Green leaf/battery icon and Title
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(8)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(20, 20)
        self.icon_label.setPixmap(get_pixmap("leaf", color=COLOR_SUCCESS, size=16))
        top_row.addWidget(self.icon_label)

        self.title_label = QLabel("Battery healthy")
        self.title_label.setStyleSheet(f"""
            color: {COLOR_TEXT_PRIMARY};
            font-size: 12px;
            font-weight: 700;
        """)
        top_row.addWidget(self.title_label)
        top_row.addStretch()
        layout.addLayout(top_row)

        self.desc_label = QLabel("Your battery is running well.")
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet(f"""
            color: {COLOR_TEXT_MUTED};
            font-size: 11px;
            line-height: 1.2;
        """)
        layout.addWidget(self.desc_label)

    def update_health(self, percent: float, plugged: bool, is_available: bool):
        if not is_available:
            self.title_label.setText("System on AC")
            self.desc_label.setText("Desktop system running normally.")
            self.icon_label.setPixmap(get_pixmap("shield-check", color=COLOR_SUCCESS, size=16))
            return

        if plugged:
            self.title_label.setText("AC Connected")
            self.desc_label.setText("Battery is charging or fully charged.")
            self.icon_label.setPixmap(get_pixmap("battery-charging", color=COLOR_SUCCESS, size=16))
        elif percent <= 15:
            self.title_label.setText("Battery Critical")
            self.desc_label.setText("Connect charger immediately.")
            self.icon_label.setPixmap(get_pixmap("alert-triangle", color=COLOR_DANGER, size=16))
        elif percent <= 30:
            self.title_label.setText("Battery Low")
            self.desc_label.setText("Power Saver activated to save power.")
            self.icon_label.setPixmap(get_pixmap("battery", color=COLOR_WARNING, size=16))
        else:
            self.title_label.setText("Battery healthy")
            self.desc_label.setText("Your battery is running well.")
            self.icon_label.setPixmap(get_pixmap("leaf", color=COLOR_SUCCESS, size=16))


class Sidebar(QFrame):
    page_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(220)
        self.setObjectName("SidebarFrame")
        self.setStyleSheet(f"""
            QFrame#SidebarFrame {{
                background-color: {COLOR_SIDEBAR};
                border-right: 1px solid {COLOR_BORDER};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(6)

        # 1. PowerGuard Logo & Branding
        brand_row = QHBoxLayout()
        brand_row.setContentsMargins(4, 0, 4, 16)
        brand_row.setSpacing(10)

        logo_label = QLabel()
        logo_label.setFixedSize(32, 32)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet(f"""
            background-color: #8B5CF6;
            border-radius: 8px;
        """)
        logo_label.setPixmap(get_pixmap("shield", color="#FFFFFF", size=20))
        brand_row.addWidget(logo_label)

        brand_text_col = QVBoxLayout()
        brand_text_col.setContentsMargins(0, 0, 0, 0)
        brand_text_col.setSpacing(1)

        title_lbl = QLabel("PowerGuard")
        title_lbl.setStyleSheet(f"""
            color: {COLOR_TEXT_PRIMARY};
            font-size: 15px;
            font-weight: 700;
        """)
        brand_text_col.addWidget(title_lbl)

        sub_lbl = QLabel("OS Monitor")
        sub_lbl.setStyleSheet(f"""
            color: {COLOR_TEXT_MUTED};
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        """)
        brand_text_col.addWidget(sub_lbl)

        brand_row.addLayout(brand_text_col)
        brand_row.addStretch()
        layout.addLayout(brand_row)

        # 2. Navigation items
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        nav_items = [
            ("Dashboard", "dashboard", "dashboard"),
            ("Performance", "performance", "performance"),
            ("Apps & Widgets", "apps", "apps"),
            ("Battery", "battery", "battery"),
            ("Processes", "processes", "processes"),
            ("Protected Apps", "protected", "protected_apps"),
            ("Logs", "logs", "logs"),
            ("Settings", "settings", "settings")
        ]

        self.buttons = {}
        for index, (text, icon_name, page_id) in enumerate(nav_items):
            btn = NavButton(text, icon_name, page_id, self)
            self.buttons[page_id] = btn
            self.button_group.addButton(btn, index)
            layout.addWidget(btn)

            # Connect clicked handler
            btn.clicked.connect(lambda checked, pid=page_id: self._on_btn_clicked(pid))

        # Select Dashboard by default
        self.buttons["dashboard"].setChecked(True)
        self.buttons["dashboard"]._update_style(True)

        layout.addStretch()

        # 3. System Health Card at the bottom of the sidebar
        self.health_card = SystemHealthSidebarCard(self)
        layout.addWidget(self.health_card)

    def _on_btn_clicked(self, page_id: str):
        # Update styles for all buttons
        for pid, btn in self.buttons.items():
            btn._update_style(btn.isChecked())
        self.page_changed.emit(page_id)

    def select_page(self, page_id: str, emit_signal: bool = False):
        if page_id in self.buttons:
            self.buttons[page_id].setChecked(True)
            for pid, btn in self.buttons.items():
                btn._update_style(btn.isChecked())
            if emit_signal:
                self.page_changed.emit(page_id)

    def update_health(self, percent: float, plugged: bool, is_available: bool):
        self.health_card.update_health(percent, plugged, is_available)
