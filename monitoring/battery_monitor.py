"""
Battery monitoring module using psutil and Windows APIs.
Retrieves real battery metrics, charging status, and remaining time.
"""
import psutil
from typing import Optional
from database.models import BatterySnapshot


class BatteryMonitor:
    def __init__(self):
        self._last_percent: Optional[float] = None

    def get_snapshot(self) -> BatterySnapshot:
        """Fetch live battery data from the system."""
        try:
            battery = psutil.sensors_battery()
        except Exception:
            battery = None

        if battery is None:
            return BatterySnapshot(
                percent=0.0,
                plugged=True,
                secsleft=None,
                is_available=False,
                power_source="AC Power",
                status_str="Desktop / No Battery",
                time_str="N/A (Connected to AC)"
            )

        percent = round(float(battery.percent), 1)
        plugged = bool(battery.power_plugged)
        secsleft = battery.secsleft

        # Calculate time string
        if plugged:
            power_source = "AC Connected"
            if percent >= 99.5:
                status_str = "Fully Charged"
                time_str = "Plugged in, 100%"
            elif secsleft and secsleft > 0 and secsleft != psutil.POWER_TIME_UNLIMITED:
                hours = secsleft // 3600
                minutes = (secsleft % 3600) // 60
                status_str = "Charging"
                time_str = f"{hours}h {minutes:02d}m until full"
            else:
                status_str = "Charging"
                time_str = "Calculating time..."
        else:
            power_source = "Battery Power"
            if secsleft and secsleft > 0 and secsleft != psutil.POWER_TIME_UNLIMITED:
                hours = secsleft // 3600
                minutes = (secsleft % 3600) // 60
                status_str = "Discharging"
                time_str = f"{hours}h {minutes:02d}m remaining"
            else:
                status_str = "Discharging"
                time_str = "Calculating remaining..."

        self._last_percent = percent

        return BatterySnapshot(
            percent=percent,
            plugged=plugged,
            secsleft=secsleft if (secsleft and secsleft > 0 and secsleft != psutil.POWER_TIME_UNLIMITED) else None,
            is_available=True,
            power_source=power_source,
            status_str=status_str,
            time_str=time_str
        )
