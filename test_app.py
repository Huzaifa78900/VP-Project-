"""
Automated Verification Suite for PowerGuard OS Monitor.
Tests all subsystems, real sensors, SQLite CRUD, process safety,
CSV export, and UI signal-slot functionality.
"""
import os
import sys
import tempfile
import psutil

# Ensure offscreen Qt platform for headless CI / testing
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication
from database.db import DatabaseManager
from database.models import SystemSettings, OptimizationLogEntry
from monitoring.cpu_monitor import CPUMonitor
from monitoring.memory_monitor import MemoryMonitor
from monitoring.disk_monitor import DiskMonitor
from monitoring.battery_monitor import BatteryMonitor
from monitoring.process_monitor import ProcessMonitor
from optimization.safety import SafetyChecker, CRITICAL_WINDOWS_PROCESSES
from optimization.process_manager import ProcessManager
from optimization.optimizer import SmartOptimizer
from ui.main_window import MainWindow


def test_suite():
    print("=" * 60)
    print("RUNNING POWERGUARD OS MONITOR VERIFICATION SUITE")
    print("=" * 60)

    # 1. Test Database Operations
    print("\n[1/10] Testing SQLite Database Initialization & CRUD...")
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        test_db_path = tmp.name

    try:
        db = DatabaseManager(test_db_path)
        # Test settings
        settings = db.get_all_settings()
        assert settings.warning_threshold == 30, f"Expected 30, got {settings.warning_threshold}"
        settings.warning_threshold = 35
        db.save_all_settings(settings)
        reloaded = db.get_all_settings()
        assert reloaded.warning_threshold == 35, "Failed to persist setting"

        # Test protected apps
        initial_prot = len(db.get_protected_apps())
        assert initial_prot > 0, "Default protected apps not seeded"
        added = db.add_protected_app("notepad.exe", "Windows Notepad")
        assert added, "Failed to add protected app"
        assert db.is_app_protected("notepad.exe"), "App should be protected"

        # Test battery & system history
        db.record_battery_reading(85.0, False)
        hist = db.get_battery_history(24)
        assert len(hist) > 0, "Failed to record battery history"

        db.record_system_reading(12.5, 45.0, 30.0)
        sys_hist = db.get_system_history(10)
        assert len(sys_hist) > 0, "Failed to record system history"

        # Test logs & CSV export
        log_id = db.add_optimization_log(OptimizationLogEntry(
            process_name="test.exe",
            pid=9999,
            action="Lower Priority",
            reason="High CPU test",
            battery_percentage=28.0,
            mode="Power Saver",
            result="Success"
        ))
        assert log_id > 0, "Failed to insert log entry"
        logs = db.get_optimization_logs()
        assert len(logs) > 0, "Failed to query logs"

        csv_path = test_db_path + ".csv"
        csv_ok = db.export_logs_to_csv(csv_path)
        assert csv_ok and os.path.exists(csv_path), "Failed to export logs to CSV"
        os.remove(csv_path)

        print("  -> Database CRUD & CSV Export: PASSED")
    finally:
        try:
            if os.path.exists(test_db_path):
                os.remove(test_db_path)
        except Exception:
            pass

    # 2. Test Real CPU Telemetry
    print("\n[2/10] Testing Real CPU Telemetry...")
    cpu_mon = CPUMonitor()
    cpu_snap = cpu_mon.get_snapshot()
    print(f"  -> CPU Usage: {cpu_snap.percent}% | Cores: {cpu_snap.core_count} | Freq: {cpu_snap.current_freq} GHz")
    assert isinstance(cpu_snap.percent, float) and 0.0 <= cpu_snap.percent <= 100.0
    assert len(cpu_snap.per_core) > 0
    print("  -> Real CPU Telemetry: PASSED")

    # 3. Test Real RAM Telemetry
    print("\n[3/10] Testing Real RAM Telemetry...")
    mem_mon = MemoryMonitor()
    ram_snap = mem_mon.get_snapshot()
    print(f"  -> RAM Usage: {ram_snap.percent}% | Used: {ram_snap.used_gb:.2f} GB / {ram_snap.total_gb:.2f} GB")
    assert ram_snap.total_gb > 1.0
    assert 0.0 <= ram_snap.percent <= 100.0
    print("  -> Real RAM Telemetry: PASSED")

    # 4. Test Real Disk Telemetry & Partitions
    print("\n[4/10] Testing Real Disk Telemetry...")
    disk_mon = DiskMonitor()
    disk_snap = disk_mon.get_snapshot()
    print(f"  -> Primary Disk: {disk_snap.primary_mount} | {disk_snap.primary_used_gb:.1f} GB / {disk_snap.primary_total_gb:.1f} GB ({disk_snap.primary_percent}%)")
    print(f"  -> Partitions detected: {len(disk_snap.partitions)} | Read: {disk_snap.read_speed_mb} MB/s | Write: {disk_snap.write_speed_mb} MB/s")
    assert len(disk_snap.partitions) > 0
    assert disk_snap.primary_total_gb > 0
    print("  -> Real Disk Telemetry: PASSED")

    # 5. Test Real Battery Telemetry
    print("\n[5/10] Testing Real Battery Telemetry...")
    batt_mon = BatteryMonitor()
    batt_snap = batt_mon.get_snapshot()
    print(f"  -> Battery Available: {batt_snap.is_available} | Level: {batt_snap.percent}% | State: {batt_snap.status_str} | Remaining: {batt_snap.time_str}")
    assert isinstance(batt_snap.percent, float)
    print("  -> Real Battery Telemetry: PASSED")

    # 6. Test Real Process Telemetry
    print("\n[6/10] Testing Real Windows Process Telemetry...")
    proc_mon = ProcessMonitor()
    procs = proc_mon.get_process_list()
    top_apps = proc_mon.get_top_apps(5)
    print(f"  -> Total Active Windows Processes: {len(procs)}")
    print(f"  -> Top Resource Consumer: {top_apps[0].name} (PID {top_apps[0].pid}) CPU: {top_apps[0].cpu_percent}% RAM: {top_apps[0].memory_mb} MB")
    assert len(procs) > 10, "Should detect multiple running processes on Windows"
    assert len(top_apps) > 0
    print("  -> Real Process Telemetry: PASSED")

    # 7. Test Process Safety System
    print("\n[7/10] Testing Process Safety Enforcement...")
    own_pid = os.getpid()
    assert SafetyChecker.is_critical(own_pid, "python.exe"), "Self-protection check failed"
    assert SafetyChecker.is_critical(0, "System Idle Process"), "PID 0 should be critical"
    assert SafetyChecker.is_critical(4, "System"), "PID 4 should be critical"
    assert SafetyChecker.is_critical(1234, "smss.exe"), "smss.exe should be critical"
    assert SafetyChecker.is_critical(5678, "csrss.exe"), "csrss.exe should be critical"
    assert SafetyChecker.is_critical(9101, "explorer.exe"), "explorer.exe should be critical"

    can_mod, reason = SafetyChecker.can_modify(own_pid, "PowerGuard", None, set())
    assert not can_mod, "Should not be able to modify PowerGuard"
    print(f"  -> Safety Enforcement Verified: blocked action reason '{reason}'")
    print("  -> Process Safety Enforcement: PASSED")

    # 8. Test Smart Optimizer Decision Logic
    print("\n[8/10] Testing Smart Optimizer Decision Logic...")
    default_db = DatabaseManager()
    optimizer = SmartOptimizer(default_db, default_db.get_all_settings())

    # Simulated battery states
    sim_normal = batt_mon.get_snapshot()
    sim_normal.plugged = False
    sim_normal.percent = 80.0
    sim_normal.is_available = True
    assert optimizer.determine_mode(sim_normal) == "Normal", "80% battery should be Normal"

    sim_saver = batt_mon.get_snapshot()
    sim_saver.plugged = False
    sim_saver.percent = 25.0
    sim_saver.is_available = True
    assert optimizer.determine_mode(sim_saver) == "Power Saver", "25% battery should be Power Saver"

    sim_emergency = batt_mon.get_snapshot()
    sim_emergency.plugged = False
    sim_emergency.percent = 10.0
    sim_emergency.is_available = True
    assert optimizer.determine_mode(sim_emergency) == "Emergency", "10% battery should be Emergency"

    sim_plugged = batt_mon.get_snapshot()
    sim_plugged.plugged = True
    sim_plugged.percent = 10.0
    sim_plugged.is_available = True
    assert optimizer.determine_mode(sim_plugged) == "Normal", "Plugged in battery should always be Normal mode"
    print("  -> Smart Optimizer Decision Logic: PASSED")

    # 9. Test PyQt6 GUI Architecture & Pages
    print("\n[9/10] Testing PyQt6 GUI Navigation & Stacked Pages...")
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow(default_db)
    assert window.stack.count() == 8, f"Expected 8 pages, got {window.stack.count()}"

    # Test navigating each page
    pages = ["dashboard", "performance", "apps", "battery", "processes", "protected_apps", "logs", "settings"]
    for pid in pages:
        window.navigate_to_page(pid)
        assert window.stack.currentWidget() == window.pages[pid] or window.stack.currentIndex() == window.pages[pid]

    # Process events to test rendering pipeline
    app.processEvents()
    print("  -> All 8 Pages Instantiated & Navigated: PASSED")

    # 10. Test Clean Shutdown
    print("\n[10/10] Testing Clean Background Thread Shutdown...")
    window.worker.stop()
    window.worker.wait(3000)
    assert not window.worker.isRunning(), "Worker thread should terminate cleanly"
    print("  -> Clean Shutdown: PASSED")

    print("\n" + "=" * 60)
    print("ALL 10 VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    test_suite()
