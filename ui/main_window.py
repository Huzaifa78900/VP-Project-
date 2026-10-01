"""
Main application window for PowerGuard OS Monitor.
Coordinates QThread background worker, SmartOptimizer, SQLite database,
system tray integration, and the 8 core user interface views.
"""
from datetime import datetime
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QLabel, QSystemTrayIcon, QMenu,
    QApplication, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QCloseEvent, QAction

from database.db import DatabaseManager
from database.models import (
    CPUSnapshot, RAMSnapshot, DiskSnapshot, BatterySnapshot,
    ProcessItem, SystemSettings, OptimizationLogEntry
)
from monitoring.monitor_worker import MonitorWorker
from optimization.optimizer import SmartOptimizer
from widgets.sidebar import Sidebar
from resources.styles import (
    COLOR_BG, COLOR_SURFACE, COLOR_BORDER, COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED, COLOR_SUCCESS,
    MAIN_STYLESHEET
)
from resources.icons import get_icon, get_pixmap

from .dashboard import DashboardPage
from .performance import PerformancePage
from .apps_widgets import AppsWidgetsPage
from .battery import BatteryPage
from .processes import ProcessesPage
from .protected_apps import ProtectedAppsPage
from .logs import LogsPage
from .settings import SettingsPage


class MainWindow(QMainWindow):
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        self.settings: SystemSettings = self.db.get_all_settings()

        self.setWindowTitle("PowerGuard OS Monitor • Smart Desktop Assistant")
        self.resize(1340, 840)
        self.setMinimumSize(1180, 700)
        self.setStyleSheet(MAIN_STYLESHEET)
        self.setWindowIcon(get_icon("shield", color="#8B5CF6", size=32))

        # Central Layout: Sidebar + (TopBar + StackedWidget)
        central_widget = QWidget()
        central_widget.setStyleSheet(f"background-color: {COLOR_BG};")
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Left Sidebar
        self.sidebar = Sidebar(self)
        root_layout.addWidget(self.sidebar)

        # 2. Right Content Area
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # 2a. Top Bar
        top_bar = self._build_top_bar()
        right_layout.addWidget(top_bar)

        # 2b. QStackedWidget for Views
        self.stack = QStackedWidget(self)
        self.pages = {}

        # Instantiate Pages
        self.dashboard_page = DashboardPage(self)
        self.performance_page = PerformancePage(self)
        self.apps_page = AppsWidgetsPage(self)
        self.battery_page = BatteryPage(self)
        self.processes_page = ProcessesPage(self.db, self)
        self.protected_page = ProtectedAppsPage(self.db, self)
        self.logs_page = LogsPage(self.db, self)
        self.settings_page = SettingsPage(self.db, self)

        # Register Pages into Stack
        page_list = [
            ("dashboard", self.dashboard_page),
            ("performance", self.performance_page),
            ("apps", self.apps_page),
            ("battery", self.battery_page),
            ("processes", self.processes_page),
            ("protected_apps", self.protected_page),
            ("logs", self.logs_page),
            ("settings", self.settings_page)
        ]

        for pid, widget in page_list:
            idx = self.stack.addWidget(widget)
            self.pages[pid] = idx

        right_layout.addWidget(self.stack)
        root_layout.addWidget(right_container)

        # 3. Initialize Smart Optimizer
        self.optimizer = SmartOptimizer(self.db, self.settings, self)

        # 4. Initialize Background Monitoring Thread (QThread)
        self.worker = MonitorWorker(self.db, self)
        self.worker.set_refresh_interval(self.settings.refresh_interval)

        # 5. Initialize System Tray
        self._setup_system_tray()

        # 6. Setup Signal-Slot Architecture
        self._connect_signals()

        # 7. Start Background Monitoring Thread
        self.worker.start()

        # 8. Prime initial data
        self._load_initial_db_state()

    def _build_top_bar(self) -> QWidget:
        top_bar = QWidget()
        top_bar.setFixedHeight(50)
        top_bar.setStyleSheet(f"""
            background-color: {COLOR_BG};
            border-bottom: 1px solid {COLOR_BORDER};
        """)

        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(28, 0, 28, 0)
        layout.setSpacing(16)

        # Status badge with pulsing/steady green dot
        status_box = QHBoxLayout()
        status_box.setSpacing(8)

        dot = QLabel()
        dot.setFixedSize(9, 9)
        dot.setStyleSheet(f"""
            background-color: {COLOR_SUCCESS};
            border-radius: 4.5px;
        """)

        status_text = QLabel("System Active")
        status_text.setStyleSheet(f"""
            color: {COLOR_TEXT_PRIMARY};
            font-size: 12px;
            font-weight: 600;
        """)

        status_box.addWidget(dot)
        status_box.addWidget(status_text)
        layout.addLayout(status_box)

        layout.addStretch()

        # Date & Time display
        self.time_label = QLabel()
        self.time_label.setStyleSheet(f"""
            color: {COLOR_TEXT_SECONDARY};
            font-size: 12.5px;
            font-weight: 500;
        """)
        self._update_clock()
        layout.addWidget(self.time_label)

        # Clock timer (updates every second)
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)

        return top_bar

    def _update_clock(self):
        now = datetime.now()
        date_str = now.strftime("%b %d, %Y")
        time_str = now.strftime("%I:%M:%S %p").lstrip('0')
        self.time_label.setText(f"{date_str}   {time_str}")

    def _setup_system_tray(self):
        self.tray_icon = QSystemTrayIcon(get_icon("shield", color="#8B5CF6", size=32), self)
        self.tray_icon.setToolTip("PowerGuard OS Monitor — Active")

        tray_menu = QMenu()
        tray_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLOR_SURFACE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
                padding: 6px;
                font-size: 12px;
            }}
            QMenu::item {{
                padding: 6px 18px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: #EFE8DC;
            }}
        """)

        # Header Info Items
        title_action = QAction("PowerGuard OS Monitor", self)
        title_action.setEnabled(False)
        tray_menu.addAction(title_action)

        self.tray_battery_action = QAction("Battery: Reading...", self)
        self.tray_battery_action.setEnabled(False)
        tray_menu.addAction(self.tray_battery_action)

        self.tray_mode_action = QAction("Mode: Normal", self)
        self.tray_mode_action.setEnabled(False)
        tray_menu.addAction(self.tray_mode_action)

        tray_menu.addSeparator()

        open_action = QAction("Open PowerGuard", self)
        open_action.triggered.connect(self._restore_from_tray)
        tray_menu.addAction(open_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self._exit_application)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self._restore_from_tray()

    def _restore_from_tray(self):
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        self.activateWindow()

    def _exit_application(self):
        self.worker.stop()
        self.worker.wait(2000)
        self.tray_icon.hide()
        QApplication.quit()

    def closeEvent(self, event: QCloseEvent):
        if self.settings.minimize_to_tray and self.tray_icon.isVisible():
            event.ignore()
            self.hide()
            if self.settings.notifications_enabled:
                self.tray_icon.showMessage(
                    "PowerGuard OS Monitor",
                    "PowerGuard is running in the background to monitor system health.",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )
        else:
            self._exit_application()
            event.accept()

    def _connect_signals(self):
        # 1. Navigation
        self.sidebar.page_changed.connect(self.navigate_to_page)
        self.dashboard_page.navigate_requested.connect(self.navigate_to_page)
        self.apps_page.navigate_requested.connect(self.navigate_to_page)
        self.dashboard_page.export_csv_requested.connect(self.logs_page.export_csv)

        # 2. Worker Telemetry Updates -> UI Components
        self.worker.metrics_updated.connect(self._on_metrics_updated)
        self.worker.processes_updated.connect(self._on_processes_updated)
        self.worker.top_apps_updated.connect(self._on_top_apps_updated)
        self.worker.history_saved.connect(self._refresh_history_charts)

        # 3. Smart Optimizer Signals
        self.optimizer.mode_changed.connect(self._on_mode_changed)
        self.optimizer.action_executed.connect(self._on_optimization_action)
        self.optimizer.notification_requested.connect(self._show_notification)

        # 4. Settings & Toggles
        self.dashboard_page.optimization_toggled.connect(self._on_optimization_toggle)
        self.settings_page.settings_saved.connect(self._on_settings_saved)

        # 5. Protected Apps / Wishlist updates
        self.protected_page.wishlist_changed.connect(self._on_wishlist_changed)
        self.processes_page.protected_apps_updated.connect(self._on_wishlist_changed)
        self.processes_page.action_logged.connect(self._on_process_action_logged)

        # 6. Chart timeframe filter clicks
        self.dashboard_page.chart_battery_trend.filter_changed.connect(self._on_chart_filter_changed)
        self.battery_page.chart.filter_changed.connect(self._on_chart_filter_changed)

    def navigate_to_page(self, page_id: str):
        if page_id in self.pages:
            self.stack.setCurrentIndex(self.pages[page_id])
            self.sidebar.select_page(page_id)

    def _load_initial_db_state(self):
        # Load protected apps
        protected = self.db.get_protected_apps()
        self.dashboard_page.update_protected_apps(protected)

        # Load recent activity
        activity = self.db.get_recent_activity(5)
        self.dashboard_page.update_recent_activity(activity)

        # Load battery history for trend chart
        hist = self.db.get_battery_history(hours=24)
        self.dashboard_page.update_battery_trend(hist)
        self.battery_page.update_trend(hist)

    # ----------------- Worker Telemetry Slot -----------------
    def _on_metrics_updated(
        self,
        cpu: CPUSnapshot,
        ram: RAMSnapshot,
        disk: DiskSnapshot,
        battery: BatterySnapshot
    ):
        # Update Dashboard
        self.dashboard_page.update_metrics(cpu, ram, disk, battery)

        # Update Performance View
        self.performance_page.update_metrics(cpu, ram, disk)

        # Update Battery View
        self.battery_page.update_battery(battery, self.optimizer.current_mode)

        # Update Sidebar Health Card
        self.sidebar.update_health(battery.percent, battery.plugged, battery.is_available)

        # Pass to Optimizer for threshold and mode evaluation
        self.optimizer.evaluate(battery, self.processes_page.all_processes)

        # Update Tray menu info
        if battery.is_available:
            self.tray_battery_action.setText(f"Battery: {int(battery.percent)}% ({battery.status_str})")
        else:
            self.tray_battery_action.setText("Power: Direct AC Connected")
        self.tray_mode_action.setText(f"Mode: {self.optimizer.current_mode}")

    def _on_processes_updated(self, procs):
        self.processes_page.update_processes(procs)
        self.apps_page.update_processes(procs)
        self.protected_page.set_running_processes(procs)

    def _on_top_apps_updated(self, top_apps):
        self.dashboard_page.update_top_apps(top_apps)

    def _refresh_history_charts(self):
        hist = self.db.get_battery_history(hours=24)
        self.dashboard_page.update_battery_trend(hist)
        self.battery_page.update_trend(hist)

    def _on_chart_filter_changed(self, hours: float):
        hist = self.db.get_battery_history(hours=hours)
        self.dashboard_page.update_battery_trend(hist)
        self.battery_page.update_trend(hist)

    # ----------------- Optimizer & Event Slots -----------------
    def _on_mode_changed(self, mode: str):
        self.dashboard_page.update_mode(mode)
        self.battery_page.update_battery(self.worker.battery_mon.get_snapshot(), mode)
        self.tray_mode_action.setText(f"Mode: {mode}")

    def _on_optimization_action(self, entry: OptimizationLogEntry):
        # Refresh recent activity on dashboard
        activity = self.db.get_recent_activity(5)
        self.dashboard_page.update_recent_activity(activity)
        # Refresh logs table if visible
        self.logs_page.refresh_logs()

    def _show_notification(self, title: str, message: str):
        if self.settings.notifications_enabled and self.tray_icon.isVisible():
            self.tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 3500)

    def _on_optimization_toggle(self, enabled: bool):
        self.settings.auto_optimize = enabled
        self.db.set_setting("auto_optimize", 1 if enabled else 0)
        self.optimizer.update_settings(self.settings)

    def _on_settings_saved(self, new_settings: SystemSettings):
        self.settings = new_settings
        self.worker.set_refresh_interval(new_settings.refresh_interval)
        self.optimizer.update_settings(new_settings)
        self.dashboard_page.set_optimization_toggle(new_settings.auto_optimize)

    def _on_wishlist_changed(self):
        protected = self.db.get_protected_apps()
        self.dashboard_page.update_protected_apps(protected)

    def _on_process_action_logged(self, process_name: str, action: str, result: str):
        entry = OptimizationLogEntry(
            process_name=process_name,
            pid=0,
            action=action,
            reason="Manual User Action in Process Manager",
            battery_percentage=self.worker.battery_mon.get_snapshot().percent,
            mode=self.optimizer.current_mode,
            result=result
        )
        self.db.add_optimization_log(entry)
        self.logs_page.refresh_logs()
        activity = self.db.get_recent_activity(5)
        self.dashboard_page.update_recent_activity(activity)
