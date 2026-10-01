"""
Smart Battery Optimizer for PowerGuard OS Monitor.
Coordinates mode determination (Normal, Power Saver, Emergency)
and automated power optimization responses based on live battery status.
"""
import logging
from typing import Set, List, Optional
from PyQt6.QtCore import QObject, pyqtSignal
from database.db import DatabaseManager
from database.models import (
    BatterySnapshot,
    ProcessItem,
    OptimizationLogEntry,
    SystemSettings
)
from .process_manager import ProcessManager

logger = logging.getLogger("PowerGuard.Optimizer")


class SmartOptimizer(QObject):
    # Signals for visual programming event triggers
    mode_changed = pyqtSignal(str)                          # "Normal", "Power Saver", "Emergency"
    action_executed = pyqtSignal(object)                    # OptimizationLogEntry
    notification_requested = pyqtSignal(str, str)          # title, message

    def __init__(self, db: DatabaseManager, settings: SystemSettings, parent=None):
        super().__init__(parent)
        self.db = db
        self.settings = settings
        self.current_mode = "Normal"
        
        # Track processes we've already acted on to prevent duplicate churn
        self._throttled_pids: Set[int] = set()
        self._suspended_pids: Set[int] = set()

    def update_settings(self, settings: SystemSettings):
        self.settings = settings

    def determine_mode(self, battery: BatterySnapshot) -> str:
        """
        Calculate system operating mode based on battery status and thresholds.
        If plugged into AC, mode is always Normal.
        """
        if not battery.is_available or battery.plugged:
            return "Normal"

        if battery.percent <= self.settings.critical_threshold:
            return "Emergency"
        elif battery.percent <= self.settings.warning_threshold:
            return "Power Saver"
        else:
            return "Normal"

    def evaluate(self, battery: BatterySnapshot, processes: List[ProcessItem]):
        """
        Evaluates battery and triggers automatic optimization if enabled.
        """
        new_mode = self.determine_mode(battery)

        # Handle Mode Transitions
        if new_mode != self.current_mode:
            old_mode = self.current_mode
            self.current_mode = new_mode
            self.mode_changed.emit(new_mode)

            msg = f"System transitioned from {old_mode} to {new_mode} Mode (Battery: {battery.percent}%)."
            logger.info(msg)

            # Record mode change in optimization logs
            log_entry = OptimizationLogEntry(
                process_name="System",
                pid=0,
                action=f"Mode Changed to {new_mode}",
                reason=f"Battery level reached {battery.percent}%",
                battery_percentage=battery.percent,
                mode=new_mode,
                result="Active"
            )
            self.db.add_optimization_log(log_entry)
            self.action_executed.emit(log_entry)

            if self.settings.notifications_enabled:
                self.notification_requested.emit(
                    f"PowerGuard: {new_mode} Mode Activated",
                    f"Battery is at {battery.percent}%. Threshold applied."
                )

            # If returning to Normal mode, reset tracked throttled processes
            if new_mode == "Normal":
                self._throttled_pids.clear()
                self._suspended_pids.clear()

        # If automatic optimization is disabled, skip proactive throttling
        if not self.settings.auto_optimize:
            return

        if self.current_mode == "Normal":
            return

        # Fetch protected apps set
        protected_apps = self.db.get_protected_apps()
        protected_names = {app.process_name.lower() for app in protected_apps}

        # Power Saver Mode Action: Throttle high CPU processes
        if self.current_mode == "Power Saver":
            for proc in processes:
                if proc.pid in self._throttled_pids or proc.pid in self._suspended_pids:
                    continue

                # Check if process exceeds high CPU threshold
                if proc.cpu_percent >= self.settings.high_cpu_threshold:
                    clean_name = proc.name.lower()
                    if clean_name in protected_names:
                        # Log protection skip
                        log_entry = OptimizationLogEntry(
                            process_name=proc.name,
                            pid=proc.pid,
                            action="Skipped Optimization",
                            reason=f"Protected application wishlist (CPU: {proc.cpu_percent}%)",
                            battery_percentage=battery.percent,
                            mode=self.current_mode,
                            result="Protected"
                        )
                        self.db.add_optimization_log(log_entry)
                        self.action_executed.emit(log_entry)
                        self._throttled_pids.add(proc.pid)
                        continue

                    # Attempt to reduce priority
                    success, message = ProcessManager.lower_priority(proc.pid, protected_names)
                    log_entry = OptimizationLogEntry(
                        process_name=proc.name,
                        pid=proc.pid,
                        action="Lower Priority",
                        reason=f"High CPU ({proc.cpu_percent}%) in Power Saver mode",
                        battery_percentage=battery.percent,
                        mode=self.current_mode,
                        result="Success" if success else message
                    )
                    self.db.add_optimization_log(log_entry)
                    self.action_executed.emit(log_entry)

                    if success:
                        self._throttled_pids.add(proc.pid)
                        if self.settings.notifications_enabled:
                            self.notification_requested.emit(
                                "PowerGuard Optimization",
                                f"Reduced priority of {proc.name} (PID {proc.pid}) to conserve battery."
                            )
                    break  # Act on one high CPU process per cycle to prevent system freeze

        # Emergency Mode Action: Throttle or suspend aggressive background apps
        elif self.current_mode == "Emergency":
            for proc in processes:
                if proc.pid in self._suspended_pids:
                    continue

                if proc.cpu_percent >= self.settings.high_cpu_threshold:
                    clean_name = proc.name.lower()
                    if clean_name in protected_names:
                        continue

                    # In Emergency mode, suspend or drastically lower priority
                    success, message = ProcessManager.lower_priority(proc.pid, protected_names)
                    log_entry = OptimizationLogEntry(
                        process_name=proc.name,
                        pid=proc.pid,
                        action="Emergency Throttle",
                        reason=f"Emergency power preservation (CPU: {proc.cpu_percent}%)",
                        battery_percentage=battery.percent,
                        mode=self.current_mode,
                        result="Success" if success else message
                    )
                    self.db.add_optimization_log(log_entry)
                    self.action_executed.emit(log_entry)

                    if success:
                        self._suspended_pids.add(proc.pid)
                        if self.settings.notifications_enabled:
                            self.notification_requested.emit(
                                "PowerGuard Emergency Response",
                                f"Throttled {proc.name} for emergency battery preservation."
                            )
                    break
