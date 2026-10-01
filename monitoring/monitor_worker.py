"""
Background monitoring worker thread for PowerGuard OS Monitor.
Gathers real-time telemetry asynchronously using QThread to keep the GUI fluid.
"""
import time
import logging
from PyQt6.QtCore import QThread, pyqtSignal
from database.db import DatabaseManager
from database.models import (
    CPUSnapshot,
    RAMSnapshot,
    DiskSnapshot,
    BatterySnapshot
)
from .cpu_monitor import CPUMonitor
from .memory_monitor import MemoryMonitor
from .disk_monitor import DiskMonitor
from .battery_monitor import BatteryMonitor
from .process_monitor import ProcessMonitor

logger = logging.getLogger("PowerGuard.MonitorWorker")


class MonitorWorker(QThread):
    # Signals for event-driven GUI updates
    metrics_updated = pyqtSignal(object, object, object, object)  # cpu, ram, disk, battery
    processes_updated = pyqtSignal(list)                          # full list of ProcessItem
    top_apps_updated = pyqtSignal(list)                           # top 5-7 apps
    battery_recorded = pyqtSignal(float, bool)                    # percent, charging
    history_saved = pyqtSignal()

    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self._is_running = True
        self.refresh_interval = 2  # default 2 seconds

        # Subsystem monitors
        self.cpu_mon = CPUMonitor()
        self.mem_mon = MemoryMonitor()
        self.disk_mon = DiskMonitor()
        self.battery_mon = BatteryMonitor()
        self.proc_mon = ProcessMonitor()

        # Database recording intervals
        self._last_db_record_time = 0.0
        self._db_record_interval = 15.0  # record history to SQLite every 15s

    def set_refresh_interval(self, seconds: int):
        """Update polling frequency dynamically."""
        self.refresh_interval = max(1, seconds)

    def stop(self):
        """Signal thread to gracefully terminate."""
        self._is_running = False

    def run(self):
        logger.info("PowerGuard monitoring worker thread started.")
        # Initial sleep to ensure CPU interval priming has completed
        self.msleep(200)

        while self._is_running:
            try:
                # 1. Fetch protected apps set from DB
                protected_apps = self.db.get_protected_apps()
                protected_names = {app.process_name for app in protected_apps}

                # 2. Collect hardware snapshots
                cpu_snap: CPUSnapshot = self.cpu_mon.get_snapshot()
                ram_snap: RAMSnapshot = self.mem_mon.get_snapshot()
                disk_snap: DiskSnapshot = self.disk_mon.get_snapshot()
                batt_snap: BatterySnapshot = self.battery_mon.get_snapshot()

                # 3. Emit metrics signal for GUI
                self.metrics_updated.emit(cpu_snap, ram_snap, disk_snap, batt_snap)

                # 4. Collect process telemetry
                procs = self.proc_mon.get_process_list(protected_names)
                top_apps = self.proc_mon.get_top_apps(limit=6, protected_names=protected_names)

                self.processes_updated.emit(procs)
                self.top_apps_updated.emit(top_apps)

                # 5. Periodic database recording
                now = time.time()
                if now - self._last_db_record_time >= self._db_record_interval:
                    if batt_snap.is_available:
                        self.db.record_battery_reading(batt_snap.percent, batt_snap.plugged)
                        self.battery_recorded.emit(batt_snap.percent, batt_snap.plugged)

                    self.db.record_system_reading(
                        cpu_snap.percent,
                        ram_snap.percent,
                        disk_snap.primary_percent
                    )
                    self.history_saved.emit()
                    self._last_db_record_time = now

            except Exception as e:
                logger.error(f"Error in monitor worker loop: {e}", exc_info=True)

            # Sleep in small increments to allow rapid responsive thread termination
            elapsed_ms = 0
            target_ms = self.refresh_interval * 1000
            while elapsed_ms < target_ms and self._is_running:
                self.msleep(100)
                elapsed_ms += 100

        logger.info("PowerGuard monitoring worker thread stopped.")
