"""
Process management controller with strict safety enforcement and error handling.
Allows lowering/restoring priority, suspending, resuming, and terminating eligible processes.
"""
import psutil
import logging
from typing import Tuple, Optional, Set
from .safety import SafetyChecker

logger = logging.getLogger("PowerGuard.ProcessManager")


class ProcessManager:
    @staticmethod
    def _verify_target(pid: int, protected_names: Optional[Set[str]] = None) -> Tuple[bool, Optional[psutil.Process], str]:
        """Verify process existence and safety constraints."""
        if protected_names is None:
            protected_names = set()
        else:
            protected_names = {n.lower() for n in protected_names}

        try:
            proc = psutil.Process(pid)
            name = proc.name()
        except psutil.NoSuchProcess:
            return False, None, f"Process with PID {pid} no longer exists."
        except psutil.AccessDenied:
            return False, None, f"Access denied inspecting process {pid}. Administrator rights may be required."
        except Exception as e:
            return False, None, f"Error inspecting process {pid}: {str(e)}"

        exe_path = None
        try:
            exe_path = proc.exe()
        except Exception:
            pass

        can_mod, reason = SafetyChecker.can_modify(pid, name, exe_path, protected_names)
        if not can_mod:
            return False, proc, f"Action blocked: {reason}"

        return True, proc, "OK"

    @classmethod
    def lower_priority(cls, pid: int, protected_names: Optional[Set[str]] = None) -> Tuple[bool, str]:
        """Safely lower process priority to Below Normal or Idle."""
        valid, proc, msg = cls._verify_target(pid, protected_names)
        if not valid or not proc:
            return False, msg

        try:
            target_priority = getattr(psutil, "BELOW_NORMAL_PRIORITY_CLASS", 16384)
            proc.nice(target_priority)
            return True, f"Reduced priority of {proc.name()} (PID {pid}) to Below Normal."
        except psutil.AccessDenied:
            return False, f"Access denied lowering priority for {proc.name()}. Requires elevated permissions."
        except psutil.NoSuchProcess:
            return False, f"Process {pid} exited before priority could be modified."
        except Exception as e:
            return False, f"Failed to modify priority: {str(e)}"

    @classmethod
    def restore_priority(cls, pid: int, protected_names: Optional[Set[str]] = None) -> Tuple[bool, str]:
        """Safely restore process priority to Normal."""
        valid, proc, msg = cls._verify_target(pid, protected_names)
        if not valid or not proc:
            return False, msg

        try:
            target_priority = getattr(psutil, "NORMAL_PRIORITY_CLASS", 32)
            proc.nice(target_priority)
            return True, f"Restored priority of {proc.name()} (PID {pid}) to Normal."
        except psutil.AccessDenied:
            return False, f"Access denied restoring priority for {proc.name()}."
        except psutil.NoSuchProcess:
            return False, f"Process {pid} no longer exists."
        except Exception as e:
            return False, f"Failed to restore priority: {str(e)}"

    @classmethod
    def suspend_process(cls, pid: int, protected_names: Optional[Set[str]] = None) -> Tuple[bool, str]:
        """Safely suspend process execution."""
        valid, proc, msg = cls._verify_target(pid, protected_names)
        if not valid or not proc:
            return False, msg

        try:
            proc.suspend()
            return True, f"Suspended process {proc.name()} (PID {pid})."
        except psutil.AccessDenied:
            return False, f"Access denied suspending {proc.name()}. Requires elevated permissions."
        except psutil.NoSuchProcess:
            return False, f"Process {pid} no longer exists."
        except Exception as e:
            return False, f"Failed to suspend process: {str(e)}"

    @classmethod
    def resume_process(cls, pid: int, protected_names: Optional[Set[str]] = None) -> Tuple[bool, str]:
        """Safely resume a suspended process."""
        valid, proc, msg = cls._verify_target(pid, protected_names)
        if not valid or not proc:
            return False, msg

        try:
            proc.resume()
            return True, f"Resumed process {proc.name()} (PID {pid})."
        except psutil.AccessDenied:
            return False, f"Access denied resuming {proc.name()}."
        except psutil.NoSuchProcess:
            return False, f"Process {pid} no longer exists."
        except Exception as e:
            return False, f"Failed to resume process: {str(e)}"

    @classmethod
    def terminate_process(cls, pid: int, protected_names: Optional[Set[str]] = None) -> Tuple[bool, str]:
        """Safely terminate an eligible user process with confirmation checks."""
        valid, proc, msg = cls._verify_target(pid, protected_names)
        if not valid or not proc:
            return False, msg

        try:
            pname = proc.name()
            proc.terminate()
            return True, f"Terminated process {pname} (PID {pid})."
        except psutil.AccessDenied:
            return False, f"Access denied terminating {proc.name()}. Requires elevated permissions."
        except psutil.NoSuchProcess:
            return False, f"Process {pid} has already exited."
        except Exception as e:
            return False, f"Failed to terminate process: {str(e)}"
