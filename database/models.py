"""
Data models and dataclasses for PowerGuard OS Monitor.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class BatterySnapshot:
    percent: float = 0.0
    plugged: bool = False
    secsleft: Optional[int] = None
    is_available: bool = True
    power_source: str = "Battery"
    status_str: str = "Discharging"
    time_str: str = "Calculating..."


@dataclass
class CPUSnapshot:
    percent: float = 0.0
    per_core: List[float] = field(default_factory=list)
    current_freq: float = 0.0  # MHz or GHz
    max_freq: float = 0.0
    core_count: int = 1
    logical_count: int = 1


@dataclass
class RAMSnapshot:
    total_bytes: int = 0
    used_bytes: int = 0
    available_bytes: int = 0
    percent: float = 0.0

    @property
    def total_gb(self) -> float:
        return self.total_bytes / (1024 ** 3)

    @property
    def used_gb(self) -> float:
        return self.used_bytes / (1024 ** 3)

    @property
    def available_gb(self) -> float:
        return self.available_bytes / (1024 ** 3)


@dataclass
class DiskPartitionInfo:
    device: str
    mountpoint: str
    fstype: str
    total_gb: float
    used_gb: float
    free_gb: float
    percent: float


@dataclass
class DiskSnapshot:
    partitions: List[DiskPartitionInfo] = field(default_factory=list)
    primary_mount: str = "C:\\"
    primary_total_gb: float = 0.0
    primary_used_gb: float = 0.0
    primary_free_gb: float = 0.0
    primary_percent: float = 0.0
    read_speed_mb: float = 0.0
    write_speed_mb: float = 0.0


@dataclass
class ProcessItem:
    pid: int
    name: str
    cpu_percent: float
    memory_mb: float
    status: str
    priority: str
    username: str = ""
    path: str = ""
    is_protected: bool = False
    is_system_critical: bool = False


@dataclass
class OptimizationLogEntry:
    id: Optional[int] = None
    timestamp: str = ""
    process_name: str = ""
    pid: int = 0
    action: str = ""
    reason: str = ""
    battery_percentage: float = 0.0
    mode: str = "Normal"
    result: str = "Success"


@dataclass
class ProtectedAppEntry:
    id: Optional[int] = None
    process_name: str = ""
    process_path: str = ""
    created_at: str = ""


@dataclass
class SystemSettings:
    refresh_interval: int = 2          # seconds: 1, 2, 5, 10
    warning_threshold: int = 30        # Battery % below which Power Saver activates
    critical_threshold: int = 15       # Battery % below which Emergency activates
    auto_optimize: bool = True         # Automatic optimization ON / OFF
    high_cpu_threshold: float = 20.0   # CPU % threshold for throttling in Power Saver
    notifications_enabled: bool = True
    minimize_to_tray: bool = True
    theme: str = "Warm Beige / Soft Sand"
