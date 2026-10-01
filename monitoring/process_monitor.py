"""
Process monitoring module using psutil.
Retrieves running processes with CPU%, Memory, Status, and Priority.
"""
import psutil
from typing import List, Set, Optional
from database.models import ProcessItem
from optimization.safety import SafetyChecker


PRIORITY_NAMES = {
    getattr(psutil, "IDLE_PRIORITY_CLASS", 64): "Idle",
    getattr(psutil, "BELOW_NORMAL_PRIORITY_CLASS", 16384): "Below Normal",
    getattr(psutil, "NORMAL_PRIORITY_CLASS", 32): "Normal",
    getattr(psutil, "ABOVE_NORMAL_PRIORITY_CLASS", 32768): "Above Normal",
    getattr(psutil, "HIGH_PRIORITY_CLASS", 128): "High",
    getattr(psutil, "REALTIME_PRIORITY_CLASS", 256): "Realtime",
}


class ProcessMonitor:
    def __init__(self):
        pass

    def get_process_list(self, protected_names: Optional[Set[str]] = None) -> List[ProcessItem]:
        """
        Fetch all running processes with their live metrics.
        Non-blocking and protected against permission exceptions.
        """
        if protected_names is None:
            protected_names = set()
        else:
            protected_names = {n.lower() for n in protected_names}

        items: List[ProcessItem] = []

        # Iterate over processes safely
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status', 'username']):
            try:
                info = p.info
                pid = info['pid']
                name = info['name'] or f"PID-{pid}"
                clean_name = name.lower()

                # Memory in MB
                mem_bytes = info['memory_info'].rss if info['memory_info'] else 0
                mem_mb = round(mem_bytes / (1024 ** 2), 1)

                cpu_pct = round(info['cpu_percent'] or 0.0, 1)
                status = info['status'] or "running"
                username = info['username'] or "SYSTEM"

                # Process priority
                try:
                    prio_val = p.nice()
                    priority_str = PRIORITY_NAMES.get(prio_val, str(prio_val))
                except Exception:
                    priority_str = "Normal"

                # Check safety
                is_crit = SafetyChecker.is_critical(pid, name)
                is_prot = clean_name in protected_names

                item = ProcessItem(
                    pid=pid,
                    name=name,
                    cpu_percent=cpu_pct,
                    memory_mb=mem_mb,
                    status=status.capitalize(),
                    priority=priority_str,
                    username=username,
                    is_protected=is_prot,
                    is_system_critical=is_crit
                )
                items.append(item)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception:
                continue

        # Sort primarily by CPU % descending, then by Memory descending
        items.sort(key=lambda x: (x.cpu_percent, x.memory_mb), reverse=True)
        return items

    def get_top_apps(self, limit: int = 5, protected_names: Optional[Set[str]] = None) -> List[ProcessItem]:
        """
        Get the top resource-consuming applications for dashboard display.
        Excludes System Idle Process.
        """
        all_procs = self.get_process_list(protected_names)
        filtered = [
            p for p in all_procs
            if p.pid != 0 and "idle" not in p.name.lower()
        ]
        return filtered[:limit]
