"""
Process safety module for PowerGuard OS Monitor.
Ensures critical Windows operating system processes and PowerGuard itself
are never modified, throttled, or suspended.
"""
import os
from typing import Set, Tuple, Optional

# Core Windows critical system process names (lowercase)
CRITICAL_WINDOWS_PROCESSES: Set[str] = {
    "system",
    "system idle process",
    "registry",
    "smss.exe",
    "csrss.exe",
    "wininit.exe",
    "services.exe",
    "lsass.exe",
    "winlogon.exe",
    "svchost.exe",
    "explorer.exe",
    "dwm.exe",
    "fontdrvhost.exe",
    "spoolsv.exe",
    "memory compression",
    "sihost.exe",
    "taskhostw.exe",
    "ctfmon.exe",
    "conhost.exe",
    "audiodg.exe",
    "runtimebroker.exe",
    "securityhealthservice.exe",
    "securityhealthsystray.exe",
    "msmpeng.exe",
    "nissrv.exe",
    "searchindexer.exe"
}


class SafetyChecker:
    @staticmethod
    def get_own_pid() -> int:
        return os.getpid()

    @staticmethod
    def is_critical(pid: int, name: str, exe_path: Optional[str] = None) -> bool:
        """
        Check if a process is a critical Windows system component or PowerGuard itself.
        """
        # Protect PowerGuard itself
        if pid == os.getpid():
            return True

        if pid == 0 or pid == 4:
            # PID 0 is Idle, PID 4 is System
            return True

        clean_name = name.strip().lower()
        if clean_name in CRITICAL_WINDOWS_PROCESSES:
            return True

        # Check path: critical processes usually live in System32
        if exe_path:
            norm_path = os.path.normpath(exe_path).lower()
            sys32 = os.path.normpath(os.environ.get("SystemRoot", "C:\\Windows") + "\\System32").lower()
            if norm_path.startswith(sys32) and clean_name in CRITICAL_WINDOWS_PROCESSES:
                return True

        return False

    @staticmethod
    def can_modify(
        pid: int,
        name: str,
        exe_path: Optional[str],
        protected_names: Set[str]
    ) -> Tuple[bool, str]:
        """
        Evaluate if a process is safe to be managed or optimized.
        Returns (can_modify, reason_if_not).
        """
        if pid == os.getpid():
            return False, "PowerGuard OS Monitor (Self-protection)"

        if pid <= 4:
            return False, "System kernel / Idle process"

        clean_name = name.strip().lower()
        if clean_name in CRITICAL_WINDOWS_PROCESSES:
            return False, f"Critical Windows system component ({name})"

        if clean_name in protected_names:
            return False, f"User protected application ({name})"

        return True, "Eligible"
