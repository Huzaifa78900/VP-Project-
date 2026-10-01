"""
Dashboard view for PowerGuard OS Monitor.
Faithfully implements Design 2: Warm Beige / Soft Sand.
Displays real-time telemetry cards, battery trend chart, optimization modes,
quick actions, top apps, protected apps, and recent activity.
"""
from datetime import datetime
from typing import List, Tuple
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from database.models import (
    CPUSnapshot, RAMSnapshot, DiskSnapshot, BatterySnapshot,
    ProcessItem, ProtectedAppEntry, OptimizationLogEntry
)
from widgets.metric_card import MetricCard
from widgets.charts import BatteryTrendChart
from widgets.mode_card import CurrentModeCard, BatteryOptimizationModesPanel
from widgets.status_card import QuickActionsPanel, TopAppsCard, ProtectedAppsCard, RecentActivityCard
from resources.styles import (
    COLOR_BG, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    COLOR_SUCCESS, COLOR_PRIMARY, COLOR_WARNING, COLOR_DANGER
)


class DashboardPage(QWidget):
    navigate_requested = pyqtSignal(str)
    export_csv_requested = pyqtSignal()
    optimization_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Main scroll container for smooth responsiveness
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

        # 1. Header Area: Greeting and Subtitle
        self._build_header()

        # 2. Four Real-time Metric Cards (Battery, CPU, RAM, Disk)
        self._build_metric_cards()

        # 3. Middle Section: Battery Trend Chart (Left) + Mode & Actions (Right)
        self._build_middle_section()

        # 4. Bottom Section: Top Apps, Protected Apps, Recent Activity
        self._build_bottom_section()

    def _build_header(self):
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 4)
        header_layout.setSpacing(2)

        # Dynamic greeting based on time of day
        hour = datetime.now().hour
        if hour < 12:
            greeting = "Good Morning!"
        elif hour < 18:
            greeting = "Good Afternoon!"
        else:
            greeting = "Good Evening!"

        self.greeting_lbl = QLabel(greeting)
        self.greeting_lbl.setStyleSheet(f"""
            color: {COLOR_TEXT_PRIMARY};
            font-size: 24px;
            font-weight: 700;
        """)

        self.sub_lbl = QLabel("Here's how your system is doing today.")
        self.sub_lbl.setStyleSheet(f"""
            color: {COLOR_TEXT_SECONDARY};
            font-size: 13px;
        """)

        header_layout.addWidget(self.greeting_lbl)
        header_layout.addWidget(self.sub_lbl)
        self.main_layout.addLayout(header_layout)

    def _build_metric_cards(self):
        cards_layout = QHBoxLayout()
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(16)

        # 1. Battery Card
        self.card_battery = MetricCard(title="Battery", icon_name="battery", parent=self)
        cards_layout.addWidget(self.card_battery)

        # 2. CPU Card
        self.card_cpu = MetricCard(title="CPU Usage", icon_name="cpu", parent=self)
        cards_layout.addWidget(self.card_cpu)

        # 3. RAM Card
        self.card_ram = MetricCard(title="RAM Usage", icon_name="ram", parent=self)
        cards_layout.addWidget(self.card_ram)

        # 4. Disk Card
        self.card_disk = MetricCard(title="Disk Usage", icon_name="disk", parent=self)
        cards_layout.addWidget(self.card_disk)

        self.main_layout.addLayout(cards_layout)

    def _build_middle_section(self):
        middle_layout = QHBoxLayout()
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(16)

        # Left: Battery Usage Trend Chart (takes ~65% width)
        self.chart_battery_trend = BatteryTrendChart(parent=self)
        middle_layout.addWidget(self.chart_battery_trend, stretch=65)

        # Right: Modes & Actions Stack (takes ~35% width)
        right_col = QVBoxLayout()
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(16)

        # Current Mode Card with Toggle
        self.card_current_mode = CurrentModeCard(parent=self)
        self.card_current_mode.optimization_toggled.connect(self.optimization_toggled.emit)
        right_col.addWidget(self.card_current_mode)

        # Battery Optimization Modes Panel
        self.panel_opt_modes = BatteryOptimizationModesPanel(parent=self)
        right_col.addWidget(self.panel_opt_modes)

        # Quick Actions Panel
        self.panel_quick_actions = QuickActionsPanel(parent=self)
        self.panel_quick_actions.view_logs_clicked.connect(lambda: self.navigate_requested.emit("logs"))
        self.panel_quick_actions.export_csv_clicked.connect(self.export_csv_requested.emit)
        self.panel_quick_actions.manage_wishlist_clicked.connect(lambda: self.navigate_requested.emit("protected_apps"))
        right_col.addWidget(self.panel_quick_actions)

        middle_layout.addLayout(right_col, stretch=35)
        self.main_layout.addLayout(middle_layout)

    def _build_bottom_section(self):
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(16)

        # 1. Top Apps by Resource Usage
        self.card_top_apps = TopAppsCard(parent=self)
        bottom_layout.addWidget(self.card_top_apps, stretch=1)

        # 2. Protected Apps (Wishlist) Preview
        self.card_protected = ProtectedAppsCard(parent=self)
        bottom_layout.addWidget(self.card_protected, stretch=1)

        # 3. Recent Activity Log Preview
        self.card_activity = RecentActivityCard(parent=self)
        bottom_layout.addWidget(self.card_activity, stretch=1)

        self.main_layout.addLayout(bottom_layout)

    # ----------------- Update Handlers -----------------
    def update_metrics(
        self,
        cpu: CPUSnapshot,
        ram: RAMSnapshot,
        disk: DiskSnapshot,
        battery: BatterySnapshot
    ):
        """Update the 4 metric cards with live system data."""
        # 1. Battery Card
        if battery.is_available:
            batt_main = f"{int(battery.percent)}%"
            batt_sub = f"{battery.status_str} • {battery.time_str}"
            batt_color = "success" if battery.percent > 30 else ("warning" if battery.percent > 15 else "danger")
            self.card_battery.update_data(batt_main, batt_sub, battery.percent, batt_color)
        else:
            self.card_battery.update_data("AC Power", "Desktop / No Battery", 100, "success")

        # 2. CPU Card
        cpu_main = f"{int(cpu.percent)}%"
        cpu_sub = f"{cpu.current_freq:.2f} GHz • {cpu.core_count} Cores" if cpu.current_freq > 0 else f"{cpu.core_count} Cores"
        cpu_color = "danger" if cpu.percent > 85 else ("warning" if cpu.percent > 60 else "primary")
        self.card_cpu.update_data(cpu_main, cpu_sub, cpu.percent, cpu_color)

        # 3. RAM Card
        ram_main = f"{int(ram.percent)}%"
        ram_sub = f"{ram.used_gb:.1f} GB / {ram.total_gb:.1f} GB"
        ram_color = "danger" if ram.percent > 85 else ("warning" if ram.percent > 70 else "primary")
        self.card_ram.update_data(ram_main, ram_sub, ram.percent, ram_color)

        # 4. Disk Card
        disk_main = f"{int(disk.primary_percent)}%"
        disk_sub = f"{disk.primary_used_gb:.0f} GB / {disk.primary_total_gb:.0f} GB ({disk.primary_mount})"
        disk_color = "danger" if disk.primary_percent > 90 else ("warning" if disk.primary_percent > 75 else "primary")
        self.card_disk.update_data(disk_main, disk_sub, disk.primary_percent, disk_color)

    def update_battery_trend(self, history: List[Tuple[str, float, int]]):
        self.chart_battery_trend.update_data(history)

    def update_mode(self, mode: str):
        self.card_current_mode.set_mode(mode)
        self.panel_opt_modes.set_active_mode(mode)

    def set_optimization_toggle(self, enabled: bool):
        self.card_current_mode.toggle.setChecked(enabled)

    def update_top_apps(self, apps: List[ProcessItem]):
        self.card_top_apps.update_apps(apps)

    def update_protected_apps(self, apps: List[ProtectedAppEntry]):
        self.card_protected.update_apps(apps)

    def update_recent_activity(self, logs: List[OptimizationLogEntry]):
        self.card_activity.update_activity(logs)
