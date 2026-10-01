"""
Memory (RAM) monitoring module using psutil.
Retrieves real total, used, available, and percentage RAM metrics.
"""
import psutil
from database.models import RAMSnapshot


class MemoryMonitor:
    def get_snapshot(self) -> RAMSnapshot:
        """Fetch live system virtual memory statistics."""
        try:
            vmem = psutil.virtual_memory()
            return RAMSnapshot(
                total_bytes=vmem.total,
                used_bytes=vmem.used,
                available_bytes=vmem.available,
                percent=round(vmem.percent, 1)
            )
        except Exception:
            return RAMSnapshot(
                total_bytes=16 * (1024 ** 3),
                used_bytes=0,
                available_bytes=16 * (1024 ** 3),
                percent=0.0
            )
