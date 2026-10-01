"""
Battery Optimization Mode cards and panels for PowerGuard.
Accurately implements Design 2: Warm Beige / Soft Sand layout.
"""
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from resources.styles import (
    COLOR_SURFACE, COLOR_BORDER, COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED, COLOR_PRIMARY,
    COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER,
    COLOR_SUCCESS_LIGHT, COLOR_WARNING_LIGHT, COLOR_DANGER_LIGHT
)
from resources.icons import get_pixmap
from .toggle_switch import ToggleSwitch


class SingleModeCard(QFrame):
    def __init__(
        self,
        mode_id: str,
        title: str,
        description: str,
        icon_name: str,
        theme_color: str,
        tint_bg: str,
        parent=None
    ):
        super().__init__(parent)
        self.mode_id = mode_id
        self.title_str = title
        self.description_str = description
        self.theme_color = theme_color
        self.tint_bg = tint_bg
        self.is_active = False

        self.setObjectName("SingleModeCard")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(14, 12, 14, 12)
        self.layout.setSpacing(6)

        # Header row: Icon, Title, Active Badge
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(10)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(26, 26)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet(f"""
            background-color: {self.tint_bg};
            border-radius: 6px;
        """)
        self.icon_label.setPixmap(get_pixmap(icon_name, color=self.theme_color, size=15))
        header_row.addWidget(self.icon_label)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"""
            color: {COLOR_TEXT_PRIMARY};
            font-size: 13px;
            font-weight: 700;
        """)
        header_row.addWidget(self.title_label)
        header_row.addStretch()

        self.badge_label = QLabel("Active")
        self.badge_label.setStyleSheet(f"""
            background-color: {self.tint_bg};
            color: {self.theme_color};
            font-size: 10px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 4px;
            border: 1px solid {self.theme_color};
        """)
        self.badge_label.setVisible(False)
        header_row.addWidget(self.badge_label)

        self.layout.addLayout(header_row)

        # Description
        self.desc_label = QLabel(description)
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet(f"""
            color: {COLOR_TEXT_SECONDARY};
            font-size: 11.5px;
            line-height: 1.3;
        """)
        self.layout.addWidget(self.desc_label)

        self.set_active(False)

    def set_active(self, active: bool):
        self.is_active = active
        self.badge_label.setVisible(active)

        if active:
            self.setStyleSheet(f"""
                QFrame#SingleModeCard {{
                    background-color: #FFFFFF;
                    border: 1.5px solid {self.theme_color};
                    border-radius: 10px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame#SingleModeCard {{
                    background-color: #FFFFFF;
                    border: 1px solid {COLOR_BORDER};
                    border-radius: 10px;
                }}
            """)


class BatteryOptimizationModesPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("BatteryModesPanel")
        self.setStyleSheet(f"""
            QFrame#BatteryModesPanel {{
                background-color: {COLOR_SURFACE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Panel Title
        title_label = QLabel("Battery Optimization Modes")
        title_label.setStyleSheet(f"""
            color: {COLOR_TEXT_PRIMARY};
            font-size: 13px;
            font-weight: 700;
        """)
        layout.addWidget(title_label)

        # 1. Normal Mode
        self.normal_card = SingleModeCard(
            mode_id="Normal",
            title="Normal Mode",
            description="Balanced performance and battery life.",
            icon_name="leaf",
            theme_color=COLOR_SUCCESS,
            tint_bg=COLOR_SUCCESS_LIGHT,
            parent=self
        )
        layout.addWidget(self.normal_card)

        # 2. Power Saver Mode
        self.saver_card = SingleModeCard(
            mode_id="Power Saver",
            title="Power Saver Mode",
            description="Limits background activity to extend battery life.",
            icon_name="battery",
            theme_color=COLOR_PRIMARY,
            tint_bg="#F5F3FF",
            parent=self
        )
        layout.addWidget(self.saver_card)

        # 3. Emergency Mode
        self.emergency_card = SingleModeCard(
            mode_id="Emergency",
            title="Emergency Mode",
            description="Max battery saving. Only essential apps.",
            icon_name="alert-triangle",
            theme_color=COLOR_DANGER,
            tint_bg=COLOR_DANGER_LIGHT,
            parent=self
        )
        layout.addWidget(self.emergency_card)

        self.set_active_mode("Normal")

    def set_active_mode(self, mode: str):
        clean = mode.strip().lower()
        self.normal_card.set_active("normal" in clean)
        self.saver_card.set_active("saver" in clean or "power" in clean)
        self.emergency_card.set_active("emergency" in clean)


class CurrentModeCard(QFrame):
    """
    Current Mode widget on the dashboard with status and quick toggle.
    """
    optimization_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CurrentModeCard")
        self.setStyleSheet(f"""
            QFrame#CurrentModeCard {{
                background-color: {COLOR_SURFACE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Title
        header = QLabel("CURRENT MODE")
        header.setStyleSheet(f"""
            color: {COLOR_TEXT_SECONDARY};
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.6px;
        """)
        layout.addWidget(header)

        # Mode Indicator Pill Row
        self.mode_row = QHBoxLayout()
        self.mode_row.setContentsMargins(0, 0, 0, 0)
        self.mode_row.setSpacing(8)

        self.mode_icon = QLabel()
        self.mode_icon.setFixedSize(20, 20)
        self.mode_icon.setPixmap(get_pixmap("leaf", color=COLOR_SUCCESS, size=16))
        self.mode_row.addWidget(self.mode_icon)

        self.mode_name = QLabel("Normal Mode")
        self.mode_name.setStyleSheet(f"""
            color: {COLOR_TEXT_PRIMARY};
            font-size: 16px;
            font-weight: 700;
        """)
        self.mode_row.addWidget(self.mode_name)
        self.mode_row.addStretch()
        layout.addLayout(self.mode_row)

        self.mode_desc = QLabel("Balanced performance and battery life.")
        self.mode_desc.setWordWrap(True)
        self.mode_desc.setStyleSheet(f"""
            color: {COLOR_TEXT_MUTED};
            font-size: 12px;
        """)
        layout.addWidget(self.mode_desc)

        layout.addSpacing(4)

        # Toggle Switch
        self.toggle = ToggleSwitch(
            text_on="Optimization: On",
            text_off="Optimization: Off",
            initial=True,
            parent=self
        )
        self.toggle.toggled.connect(self.optimization_toggled.emit)
        layout.addWidget(self.toggle)

    def set_mode(self, mode: str):
        clean = mode.strip().lower()
        if "emergency" in clean:
            self.mode_name.setText("Emergency Mode")
            self.mode_name.setStyleSheet(f"color: {COLOR_DANGER}; font-size: 16px; font-weight: 700;")
            self.mode_icon.setPixmap(get_pixmap("alert-triangle", color=COLOR_DANGER, size=16))
            self.mode_desc.setText("Strict resource limiting active to keep system alive.")
        elif "saver" in clean or "power" in clean:
            self.mode_name.setText("Power Saver Mode")
            self.mode_name.setStyleSheet(f"color: {COLOR_PRIMARY}; font-size: 16px; font-weight: 700;")
            self.mode_icon.setPixmap(get_pixmap("battery", color=COLOR_PRIMARY, size=16))
            self.mode_desc.setText("Lowering background priority for extended battery life.")
        else:
            self.mode_name.setText("Normal Mode")
            self.mode_name.setStyleSheet(f"color: {COLOR_SUCCESS}; font-size: 16px; font-weight: 700;")
            self.mode_icon.setPixmap(get_pixmap("leaf", color=COLOR_SUCCESS, size=16))
            self.mode_desc.setText("Balanced performance and battery life.")
