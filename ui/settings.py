"""
Settings page for PowerGuard OS Monitor.
Provides threshold configuration, background refresh frequency,
automatic optimization policies, notifications, and tray preferences.
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton,
    QFrame, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from database.db import DatabaseManager
from database.models import SystemSettings
from resources.styles import (
    COLOR_BG, COLOR_SURFACE, COLOR_BORDER, COLOR_BORDER_LIGHT,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    COLOR_PRIMARY, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER
)
from resources.icons import get_icon, get_pixmap


class SettingsPage(QWidget):
    settings_saved = pyqtSignal(object)  # SystemSettings

    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.current_settings = self.db.get_all_settings()

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
        header.setSpacing(2)
        title_lbl = QLabel("Application Settings & Polling Parameters")
        title_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 24px; font-weight: 700;")
        sub_lbl = QLabel("Customize hardware telemetry rate, battery thresholds, autonomous power policies, and tray behavior.")
        sub_lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 13px;")
        header.addWidget(title_lbl)
        header.addWidget(sub_lbl)
        self.main_layout.addLayout(header)

        # 2. Settings Sections
        self.main_layout.addWidget(self._build_monitoring_section())
        self.main_layout.addWidget(self._build_battery_thresholds_section())
        self.main_layout.addWidget(self._build_optimization_section())
        self.main_layout.addWidget(self._build_tray_notifications_section())
        self.main_layout.addWidget(self._build_appearance_section())

        # 3. Save / Reset Button Row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_row.addStretch()

        self.btn_reset = QPushButton("Reset to Defaults")
        self.btn_reset.clicked.connect(self._reset_defaults)
        btn_row.addWidget(self.btn_reset)

        self.btn_save = QPushButton("Save Settings")
        self.btn_save.setProperty("role", "primary")
        self.btn_save.setIcon(get_icon("shield-check", color="#FFFFFF", size=15))
        self.btn_save.clicked.connect(self._save_settings)
        btn_row.addWidget(self.btn_save)

        self.main_layout.addLayout(btn_row)

        self._populate_fields(self.current_settings)

    def _create_section_card(self, title: str, subtitle: str) -> QFrame:
        card = QFrame()
        card.setObjectName("SettingsCard")
        card.setStyleSheet(f"""
            QFrame#SettingsCard {{
                background-color: {COLOR_SURFACE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        header_col = QVBoxLayout()
        header_col.setSpacing(2)
        t = QLabel(title)
        t.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 14px; font-weight: 700;")
        s = QLabel(subtitle)
        s.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
        header_col.addWidget(t)
        header_col.addWidget(s)
        layout.addLayout(header_col)

        return card

    def _build_monitoring_section(self) -> QFrame:
        card = self._create_section_card(
            "Hardware Telemetry & Polling Interval",
            "Adjust background QThread query frequency to balance responsiveness with CPU overhead."
        )
        layout = card.layout()

        row = QHBoxLayout()
        lbl = QLabel("Monitoring Refresh Interval:")
        lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px; font-weight: 500;")
        row.addWidget(lbl)
        row.addStretch()

        self.combo_interval = QComboBox()
        self.combo_interval.addItems(["1 second (High Precision)", "2 seconds (Recommended)", "5 seconds (Low Overhead)", "10 seconds (Power Saver)"])
        self.combo_interval.setFixedWidth(240)
        row.addWidget(self.combo_interval)
        layout.addLayout(row)

        return card

    def _build_battery_thresholds_section(self) -> QFrame:
        card = self._create_section_card(
            "Battery Optimization Thresholds",
            "Define the battery percentage cutoffs that trigger Power Saver and Emergency operating modes."
        )
        layout = card.layout()

        # Warning threshold
        row1 = QHBoxLayout()
        lbl1 = QLabel("Warning Threshold (Activates Power Saver Mode):")
        lbl1.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px; font-weight: 500;")
        row1.addWidget(lbl1)
        row1.addStretch()

        self.spin_warning = QSpinBox()
        self.spin_warning.setRange(16, 50)
        self.spin_warning.setSuffix(" %")
        self.spin_warning.setFixedWidth(100)
        row1.addWidget(self.spin_warning)
        layout.addLayout(row1)

        # Critical threshold
        row2 = QHBoxLayout()
        lbl2 = QLabel("Critical Threshold (Activates Emergency Mode):")
        lbl2.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px; font-weight: 500;")
        row2.addWidget(lbl2)
        row2.addStretch()

        self.spin_critical = QSpinBox()
        self.spin_critical.setRange(5, 25)
        self.spin_critical.setSuffix(" %")
        self.spin_critical.setFixedWidth(100)
        row2.addWidget(self.spin_critical)
        layout.addLayout(row2)

        return card

    def _build_optimization_section(self) -> QFrame:
        card = self._create_section_card(
            "Smart Battery Autonomous Policy",
            "Configure proactive background throttling of resource-heavy applications."
        )
        layout = card.layout()

        self.chk_auto_optimize = QCheckBox("Enable Automatic Power Optimization")
        self.chk_auto_optimize.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight: 600;")
        layout.addWidget(self.chk_auto_optimize)

        row = QHBoxLayout()
        lbl = QLabel("High CPU Throttling Trigger:")
        lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px; font-weight: 500;")
        row.addWidget(lbl)
        row.addStretch()

        self.spin_high_cpu = QDoubleSpinBox()
        self.spin_high_cpu.setRange(5.0, 80.0)
        self.spin_high_cpu.setSingleStep(5.0)
        self.spin_high_cpu.setSuffix(" %")
        self.spin_high_cpu.setFixedWidth(100)
        row.addWidget(self.spin_high_cpu)
        layout.addLayout(row)

        return card

    def _build_tray_notifications_section(self) -> QFrame:
        card = self._create_section_card(
            "Notifications & System Tray",
            "Configure desktop alert banners and background tray minimization behavior."
        )
        layout = card.layout()

        self.chk_notifications = QCheckBox("Show desktop notifications for mode transitions and process throttling")
        layout.addWidget(self.chk_notifications)

        self.chk_minimize_tray = QCheckBox("Minimize to Windows System Tray when closing the main window")
        layout.addWidget(self.chk_minimize_tray)

        return card

    def _build_appearance_section(self) -> QFrame:
        card = self._create_section_card(
            "Visual Theme & Application Info",
            "Design system configuration for Visual Programming university project."
        )
        layout = card.layout()

        theme_lbl = QLabel("Active Visual Theme: Warm Beige / Soft Sand (Design 2)")
        theme_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight: 600;")
        layout.addWidget(theme_lbl)

        info_lbl = QLabel(
            "PowerGuard OS Monitor • Smart Desktop Assistant for Battery & System Performance\n"
            "Visual Programming University Project • Built with Python, PyQt6, psutil, SQLite & pyqtgraph."
        )
        info_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11.5px; line-height: 1.4;")
        layout.addWidget(info_lbl)

        return card

    def _populate_fields(self, s: SystemSettings):
        # Refresh interval index mapping
        mapping = {1: 0, 2: 1, 5: 2, 10: 3}
        self.combo_interval.setCurrentIndex(mapping.get(s.refresh_interval, 1))

        self.spin_warning.setValue(s.warning_threshold)
        self.spin_critical.setValue(s.critical_threshold)
        self.chk_auto_optimize.setChecked(s.auto_optimize)
        self.spin_high_cpu.setValue(s.high_cpu_threshold)
        self.chk_notifications.setChecked(s.notifications_enabled)
        self.chk_minimize_tray.setChecked(s.minimize_to_tray)

    def _save_settings(self):
        # Read interval
        intervals = [1, 2, 5, 10]
        chosen_interval = intervals[self.combo_interval.currentIndex()]

        warn = self.spin_warning.value()
        crit = self.spin_critical.value()

        if crit >= warn:
            QMessageBox.warning(
                self,
                "Invalid Thresholds",
                "Critical battery threshold must be lower than the warning threshold."
            )
            return

        new_settings = SystemSettings(
            refresh_interval=chosen_interval,
            warning_threshold=warn,
            critical_threshold=crit,
            auto_optimize=self.chk_auto_optimize.isChecked(),
            high_cpu_threshold=self.spin_high_cpu.value(),
            notifications_enabled=self.chk_notifications.isChecked(),
            minimize_to_tray=self.chk_minimize_tray.isChecked(),
            theme="Warm Beige / Soft Sand"
        )

        self.db.save_all_settings(new_settings)
        self.current_settings = new_settings
        self.settings_saved.emit(new_settings)

        QMessageBox.information(
            self,
            "Settings Saved",
            "Configuration successfully updated and saved to SQLite."
        )

    def _reset_defaults(self):
        defaults = SystemSettings()
        self._populate_fields(defaults)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("PowerGuard Settings")
    db = DatabaseManager()

    window = SettingsPage(db)
    window.resize(980, 760)
    window.show()

    sys.exit(app.exec())
