"""
Optimization package for PowerGuard OS Monitor.
"""
from .safety import SafetyChecker, CRITICAL_WINDOWS_PROCESSES
from .process_manager import ProcessManager
from .optimizer import SmartOptimizer

__all__ = [
    "SafetyChecker",
    "CRITICAL_WINDOWS_PROCESSES",
    "ProcessManager",
    "SmartOptimizer"
]
