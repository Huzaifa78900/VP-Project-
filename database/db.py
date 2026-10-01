"""
SQLite Database manager for PowerGuard OS Monitor.
Provides persistent storage for settings, protected apps, battery history,
system history, and optimization logs with WAL mode for thread safety.
"""
import os
import sqlite3
import csv
import logging
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Any
from .models import SystemSettings, ProtectedAppEntry, OptimizationLogEntry

logger = logging.getLogger("PowerGuard.Database")

DB_FILENAME = "powerguard.db"


class DatabaseManager:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.db_path = os.path.join(base_dir, DB_FILENAME)
        else:
            self.db_path = db_path
        
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self):
        """Create tables if they do not exist and seed default values."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL
                )
            """)

            # Protected apps table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS protected_apps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    process_name TEXT UNIQUE NOT NULL,
                    process_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Battery history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS battery_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    percentage REAL NOT NULL,
                    charging INTEGER NOT NULL
                )
            """)

            # System history table (CPU, RAM, Disk)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    cpu_percent REAL NOT NULL,
                    ram_percent REAL NOT NULL,
                    disk_percent REAL NOT NULL
                )
            """)

            # Optimization logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS optimization_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    process_name TEXT,
                    pid INTEGER,
                    action TEXT NOT NULL,
                    reason TEXT,
                    battery_percentage REAL,
                    mode TEXT,
                    result TEXT
                )
            """)

            conn.commit()

        self._seed_defaults()

    def _seed_defaults(self):
        """Seed default settings and essential protected apps if table is empty."""
        default_settings = {
            "refresh_interval": "2",
            "warning_threshold": "30",
            "critical_threshold": "15",
            "auto_optimize": "1",
            "high_cpu_threshold": "20.0",
            "notifications_enabled": "1",
            "minimize_to_tray": "1",
            "theme": "Warm Beige / Soft Sand"
        }

        with self._get_connection() as conn:
            cursor = conn.cursor()
            for key, val in default_settings.items():
                cursor.execute(
                    "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                    (key, val)
                )

            # Seed default protected apps commonly used
            default_protected = [
                ("chrome.exe", "Google Chrome"),
                ("code.exe", "Visual Studio Code"),
                ("python.exe", "Python Runtime"),
                ("discord.exe", "Discord"),
                ("teams.exe", "Microsoft Teams")
            ]
            for proc_name, path in default_protected:
                cursor.execute(
                    "INSERT OR IGNORE INTO protected_apps (process_name, process_path) VALUES (?, ?)",
                    (proc_name, path)
                )

            # Insert an initial startup entry if optimization_logs is empty
            cursor.execute("SELECT COUNT(*) FROM optimization_logs")
            if cursor.fetchone()[0] == 0:
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    INSERT INTO optimization_logs (timestamp, process_name, pid, action, reason, battery_percentage, mode, result)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (now_str, "PowerGuard", os.getpid(), "Service Started", "System initialization completed", 100.0, "Normal", "Success"))

            conn.commit()

    # ----------------- Settings Methods -----------------
    def get_setting(self, key: str, default: Any = None) -> Any:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                return row["value"]
            return default

    def set_setting(self, key: str, value: Any):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (key, str(value)))
            conn.commit()

    def get_all_settings(self) -> SystemSettings:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM settings")
            rows = cursor.fetchall()
            kv = {r["key"]: r["value"] for r in rows}

        return SystemSettings(
            refresh_interval=int(kv.get("refresh_interval", 2)),
            warning_threshold=int(kv.get("warning_threshold", 30)),
            critical_threshold=int(kv.get("critical_threshold", 15)),
            auto_optimize=bool(int(kv.get("auto_optimize", 1))),
            high_cpu_threshold=float(kv.get("high_cpu_threshold", 20.0)),
            notifications_enabled=bool(int(kv.get("notifications_enabled", 1))),
            minimize_to_tray=bool(int(kv.get("minimize_to_tray", 1))),
            theme=kv.get("theme", "Warm Beige / Soft Sand")
        )

    def save_all_settings(self, s: SystemSettings):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            data = [
                ("refresh_interval", str(s.refresh_interval)),
                ("warning_threshold", str(s.warning_threshold)),
                ("critical_threshold", str(s.critical_threshold)),
                ("auto_optimize", "1" if s.auto_optimize else "0"),
                ("high_cpu_threshold", str(s.high_cpu_threshold)),
                ("notifications_enabled", "1" if s.notifications_enabled else "0"),
                ("minimize_to_tray", "1" if s.minimize_to_tray else "0"),
                ("theme", s.theme)
            ]
            for key, val in data:
                cursor.execute("""
                    INSERT INTO settings (key, value) VALUES (?, ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """, (key, val))
            conn.commit()

    # ----------------- Protected Apps Methods -----------------
    def get_protected_apps(self) -> List[ProtectedAppEntry]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, process_name, process_path, created_at FROM protected_apps ORDER BY process_name ASC")
            rows = cursor.fetchall()
            return [
                ProtectedAppEntry(
                    id=r["id"],
                    process_name=r["process_name"],
                    process_path=r["process_path"] or "",
                    created_at=r["created_at"] or ""
                ) for r in rows
            ]

    def add_protected_app(self, process_name: str, process_path: str = "") -> bool:
        process_name = process_name.strip().lower()
        if not process_name:
            return False
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    INSERT INTO protected_apps (process_name, process_path, created_at)
                    VALUES (?, ?, ?)
                """, (process_name, process_path, now_str))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def remove_protected_app(self, app_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM protected_apps WHERE id = ?", (app_id,))
            conn.commit()
            return cursor.rowcount > 0

    def is_app_protected(self, process_name: str) -> bool:
        process_name = process_name.strip().lower()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM protected_apps WHERE LOWER(process_name) = ?", (process_name,))
            return cursor.fetchone() is not None

    # ----------------- Battery History Methods -----------------
    def record_battery_reading(self, percentage: float, charging: bool):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO battery_history (timestamp, percentage, charging)
                VALUES (?, ?, ?)
            """, (now_str, percentage, 1 if charging else 0))
            conn.commit()

    def get_battery_history(self, hours: float = 24) -> List[Tuple[str, float, int]]:
        cutoff = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT timestamp, percentage, charging
                FROM battery_history
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
            """, (cutoff,))
            rows = cursor.fetchall()
            return [(r["timestamp"], r["percentage"], r["charging"]) for r in rows]

    # ----------------- System History Methods -----------------
    def record_system_reading(self, cpu_percent: float, ram_percent: float, disk_percent: float):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO system_history (timestamp, cpu_percent, ram_percent, disk_percent)
                VALUES (?, ?, ?, ?)
            """, (now_str, cpu_percent, ram_percent, disk_percent))
            # Keep table from growing indefinitely (keep last 5000 rows)
            cursor.execute("""
                DELETE FROM system_history WHERE id IN (
                    SELECT id FROM system_history ORDER BY id DESC LIMIT -1 OFFSET 5000
                )
            """)
            conn.commit()

    def get_system_history(self, limit: int = 60) -> List[Tuple[str, float, float, float]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT timestamp, cpu_percent, ram_percent, disk_percent
                FROM system_history
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            # Return in chronological order
            return [(r["timestamp"], r["cpu_percent"], r["ram_percent"], r["disk_percent"]) for r in reversed(rows)]

    # ----------------- Optimization Logs Methods -----------------
    def add_optimization_log(self, entry: OptimizationLogEntry) -> int:
        now_str = entry.timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO optimization_logs
                (timestamp, process_name, pid, action, reason, battery_percentage, mode, result)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                now_str,
                entry.process_name,
                entry.pid,
                entry.action,
                entry.reason,
                entry.battery_percentage,
                entry.mode,
                entry.result
            ))
            conn.commit()
            return cursor.lastrowid

    def get_optimization_logs(
        self,
        limit: int = 300,
        search: str = "",
        mode: str = "",
        action: str = ""
    ) -> List[OptimizationLogEntry]:
        query = "SELECT id, timestamp, process_name, pid, action, reason, battery_percentage, mode, result FROM optimization_logs WHERE 1=1"
        params: List[Any] = []

        if search:
            query += " AND (process_name LIKE ? OR action LIKE ? OR reason LIKE ?)"
            s_param = f"%{search}%"
            params.extend([s_param, s_param, s_param])
        if mode and mode != "All":
            query += " AND mode = ?"
            params.append(mode)
        if action and action != "All":
            query += " AND action = ?"
            params.append(action)

        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [
                OptimizationLogEntry(
                    id=r["id"],
                    timestamp=r["timestamp"],
                    process_name=r["process_name"] or "",
                    pid=r["pid"] or 0,
                    action=r["action"] or "",
                    reason=r["reason"] or "",
                    battery_percentage=r["battery_percentage"] or 0.0,
                    mode=r["mode"] or "Normal",
                    result=r["result"] or "Success"
                ) for r in rows
            ]

    def get_recent_activity(self, limit: int = 5) -> List[OptimizationLogEntry]:
        return self.get_optimization_logs(limit=limit)

    def clear_logs(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM optimization_logs")
            conn.commit()

    def export_logs_to_csv(self, filepath: str) -> bool:
        logs = self.get_optimization_logs(limit=10000)
        try:
            with open(filepath, mode="w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    "ID", "Timestamp", "Process Name", "PID", "Action",
                    "Reason", "Battery %", "Mode", "Result"
                ])
                for log in logs:
                    writer.writerow([
                        log.id,
                        log.timestamp,
                        log.process_name,
                        log.pid,
                        log.action,
                        log.reason,
                        f"{log.battery_percentage:.1f}%",
                        log.mode,
                        log.result
                    ])
            return True
        except Exception as e:
            logger.error(f"Error exporting logs to CSV: {e}")
            return False
