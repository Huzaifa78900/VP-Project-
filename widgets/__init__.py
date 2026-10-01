"""
Widgets package for PowerGuard OS Monitor.
"""
from .metric_card import MetricCard
from .toggle_switch import ToggleSwitch
from .mode_card import SingleModeCard, BatteryOptimizationModesPanel, CurrentModeCard
from .sidebar import Sidebar
from .charts import BatteryTrendChart, LiveMetricChart
from .status_card import QuickActionsPanel, TopAppsCard, ProtectedAppsCard, RecentActivityCard

__all__ = [
    "MetricCard",
    "ToggleSwitch",
    "SingleModeCard",
    "BatteryOptimizationModesPanel",
    "CurrentModeCard",
    "Sidebar",
    "BatteryTrendChart",
    "LiveMetricChart",
    "QuickActionsPanel",
    "TopAppsCard",
    "ProtectedAppsCard",
    "RecentActivityCard"
]
