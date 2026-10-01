"""
UI package for PowerGuard OS Monitor.
"""
from .main_window import MainWindow
from .dashboard import DashboardPage
from .performance import PerformancePage
from .apps_widgets import AppsWidgetsPage
from .battery import BatteryPage
from .processes import ProcessesPage
from .protected_apps import ProtectedAppsPage
from .logs import LogsPage
from .settings import SettingsPage

__all__ = [
    "MainWindow",
    "DashboardPage",
    "PerformancePage",
    "AppsWidgetsPage",
    "BatteryPage",
    "ProcessesPage",
    "ProtectedAppsPage",
    "LogsPage",
    "SettingsPage"
]
