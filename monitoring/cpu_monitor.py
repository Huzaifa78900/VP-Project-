"""
CPU monitoring module using psutil.
Retrieves real CPU usage percentage, per-core metrics, frequency, and core counts.
"""
import psutil
from database.models import CPUSnapshot


class CPUMonitor:
    def __init__(self):
        self.physical_cores = psutil.cpu_count(logical=False) or 1
        self.logical_cores = psutil.cpu_count(logical=True) or 1
        # Prime the CPU monitoring so subsequent calls return accurate intervals
        try:
            psutil.cpu_percent(interval=None)
            psutil.cpu_percent(percpu=True, interval=None)
        except Exception:
            pass

    def get_snapshot(self) -> CPUSnapshot:
        """Fetch live CPU usage and hardware frequencies."""
        try:
            total_percent = round(psutil.cpu_percent(interval=None), 1)
        except Exception:
            total_percent = 0.0

        try:
            per_core = [round(p, 1) for p in psutil.cpu_percent(percpu=True, interval=None)]
        except Exception:
            per_core = [total_percent] * self.logical_cores

        current_freq_ghz = 0.0
        max_freq_ghz = 0.0
        try:
            freq = psutil.cpu_freq()
            if freq:
                current_freq_ghz = round(freq.current / 1000.0, 2)
                max_freq_ghz = round((freq.max if freq.max > 0 else freq.current) / 1000.0, 2)
        except Exception:
            pass

        return CPUSnapshot(
            percent=total_percent,
            per_core=per_core,
            current_freq=current_freq_ghz,
            max_freq=max_freq_ghz,
            core_count=self.physical_cores,
            logical_count=self.logical_cores
        )
