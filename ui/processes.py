"""
Process Manager page for PowerGuard OS Monitor.
Provides live Windows process inspection, search, sorting,
priority adjustment, process suspend/resume/terminate, and protected app tagging.
"""
from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QFrame, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from database.models import ProcessItem
from database.db import DatabaseManager
from optimization.process_manager import ProcessManager
from optimization.safety import SafetyChecker
from resources.styles import (
    COLOR_BG, COLOR_SURFACE, COLOR_BORDER, COLOR_BORDER_LIGHT,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    COLOR_PRIMARY, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER
)
from resources.icons import get_icon, get_pixmap


class ProcessesPage(QWidget):
    protected_apps_updated = pyqtSignal()
    action_logged = pyqtSignal(str, str, str)  # process_name, action, result

    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.all_processes: List[ProcessItem] = []
        self._current_filter_text = ""
        self._sort_column = 2  # default sort by CPU % descending
        self._sort_ascending = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(16)

        # 1. Header
        header = QVBoxLayout()
        header.setSpacing(2)
        title_lbl = QLabel("Windows Process Manager")
        title_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 24px; font-weight: 700;")
        sub_lbl = QLabel("Inspect active Windows tasks, throttle high CPU consumers, or manage execution states safely.")
        sub_lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 13px;")
        header.addWidget(title_lbl)
        header.addWidget(sub_lbl)
        layout.addLayout(header)

        # 2. Controls Toolbar (Search, Filter, Actions)
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search processes by name or PID...")
        self.search_input.setFixedWidth(280)
        self.search_input.textChanged.connect(self._on_search_changed)
        toolbar.addWidget(self.search_input)

        toolbar.addStretch()

        # Action Buttons
        self.btn_lower = QPushButton("Lower Priority")
        self.btn_lower.setIcon(get_icon("performance", color=COLOR_TEXT_PRIMARY, size=14))
        self.btn_lower.clicked.connect(self._on_lower_priority)
        toolbar.addWidget(self.btn_lower)

        self.btn_restore = QPushButton("Restore Normal")
        self.btn_restore.setIcon(get_icon("refresh", color=COLOR_TEXT_PRIMARY, size=14))
        self.btn_restore.clicked.connect(self._on_restore_priority)
        toolbar.addWidget(self.btn_restore)

        self.btn_suspend = QPushButton("Suspend")
        self.btn_suspend.clicked.connect(self._on_suspend)
        toolbar.addWidget(self.btn_suspend)

        self.btn_resume = QPushButton("Resume")
        self.btn_resume.clicked.connect(self._on_resume)
        toolbar.addWidget(self.btn_resume)

        self.btn_protect = QPushButton("Protect App")
        self.btn_protect.setIcon(get_icon("protected", color="#FFFFFF", size=14))
        self.btn_protect.setProperty("role", "primary")
        self.btn_protect.clicked.connect(self._on_protect_app)
        toolbar.addWidget(self.btn_protect)

        self.btn_terminate = QPushButton("End Task")
        self.btn_terminate.setProperty("role", "danger")
        self.btn_terminate.clicked.connect(self._on_terminate)
        toolbar.addWidget(self.btn_terminate)

        layout.addLayout(toolbar)

        # 3. Main Process Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Process Name", "PID", "CPU Usage", "Memory (MB)", "Status", "Priority", "User / Security"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(False)  # We handle sorting manually to preserve data types

        layout.addWidget(self.table)

        # 4. Status Bar / Selection Indicator
        self.status_bar = QLabel("Displaying 0 running processes.")
        self.status_bar.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(self.status_bar)

    def _on_search_changed(self, text: str):
        self._current_filter_text = text.strip().lower()
        self._render_table()

    def update_processes(self, procs: List[ProcessItem]):
        self.all_processes = procs
        self._render_table()

    def _get_selected_proc(self) -> Optional[ProcessItem]:
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return None
        row = selected_rows[0].row()
        pid_item = self.table.item(row, 1)
        if not pid_item:
            return None
        pid = int(pid_item.text())
        for p in self.all_processes:
            if p.pid == pid:
                return p
        return None

    def _render_table(self):
        filtered = []
        for p in self.all_processes:
            if self._current_filter_text:
                if self._current_filter_text not in p.name.lower() and self._current_filter_text not in str(p.pid):
                    continue
            filtered.append(p)

        # Save selected PID to restore after re-render
        current_sel = self._get_selected_proc()
        selected_pid = current_sel.pid if current_sel else None

        self.table.setRowCount(len(filtered))
        restore_row = -1

        for row, p in enumerate(filtered):
            if p.pid == selected_pid:
                restore_row = row

            # 0. Name + Protection icon
            name_text = p.name
            if p.is_protected:
                name_text += "  [Protected]"
            elif p.is_system_critical:
                name_text += "  [System]"

            item_name = QTableWidgetItem(name_text)
            if p.is_protected:
                item_name.setForeground(Qt.GlobalColor.darkGreen)

            # 1. PID
            item_pid = QTableWidgetItem(str(p.pid))
            item_pid.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # 2. CPU
            item_cpu = QTableWidgetItem(f"{p.cpu_percent:.1f}%")
            item_cpu.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            # 3. RAM
            item_mem = QTableWidgetItem(f"{p.memory_mb:.1f} MB")
            item_mem.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            # 4. Status
            item_status = QTableWidgetItem(p.status)
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # 5. Priority
            item_prio = QTableWidgetItem(p.priority)
            item_prio.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # 6. User
            item_user = QTableWidgetItem(p.username or "SYSTEM")

            self.table.setItem(row, 0, item_name)
            self.table.setItem(row, 1, item_pid)
            self.table.setItem(row, 2, item_cpu)
            self.table.setItem(row, 3, item_mem)
            self.table.setItem(row, 4, item_status)
            self.table.setItem(row, 5, item_prio)
            self.table.setItem(row, 6, item_user)

        if restore_row >= 0:
            self.table.selectRow(restore_row)

        self.status_bar.setText(f"Displaying {len(filtered)} processes (Total active: {len(self.all_processes)}).")

    # ----------------- Process Action Handlers -----------------
    def _on_lower_priority(self):
        proc = self._get_selected_proc()
        if not proc:
            QMessageBox.information(self, "No Selection", "Please select a process from the table first.")
            return

        protected_names = {a.process_name for a in self.db.get_protected_apps()}
        success, msg = ProcessManager.lower_priority(proc.pid, protected_names)
        self.action_logged.emit(proc.name, "Lower Priority", msg)

        if success:
            QMessageBox.information(self, "Priority Adjusted", msg)
        else:
            QMessageBox.warning(self, "Action Denied", msg)

    def _on_restore_priority(self):
        proc = self._get_selected_proc()
        if not proc:
            QMessageBox.information(self, "No Selection", "Please select a process from the table first.")
            return

        protected_names = {a.process_name for a in self.db.get_protected_apps()}
        success, msg = ProcessManager.restore_priority(proc.pid, protected_names)
        self.action_logged.emit(proc.name, "Restore Priority", msg)

        if success:
            QMessageBox.information(self, "Priority Restored", msg)
        else:
            QMessageBox.warning(self, "Action Denied", msg)

    def _on_suspend(self):
        proc = self._get_selected_proc()
        if not proc:
            QMessageBox.information(self, "No Selection", "Please select a process from the table first.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Process Suspension",
            f"Are you sure you want to suspend {proc.name} (PID {proc.pid})?\n"
            "This will pause the application until manually resumed.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            protected_names = {a.process_name for a in self.db.get_protected_apps()}
            success, msg = ProcessManager.suspend_process(proc.pid, protected_names)
            self.action_logged.emit(proc.name, "Suspend Process", msg)
            if success:
                QMessageBox.information(self, "Process Suspended", msg)
            else:
                QMessageBox.warning(self, "Action Denied", msg)

    def _on_resume(self):
        proc = self._get_selected_proc()
        if not proc:
            QMessageBox.information(self, "No Selection", "Please select a process from the table first.")
            return

        protected_names = {a.process_name for a in self.db.get_protected_apps()}
        success, msg = ProcessManager.resume_process(proc.pid, protected_names)
        self.action_logged.emit(proc.name, "Resume Process", msg)
        if success:
            QMessageBox.information(self, "Process Resumed", msg)
        else:
            QMessageBox.warning(self, "Action Denied", msg)

    def _on_terminate(self):
        proc = self._get_selected_proc()
        if not proc:
            QMessageBox.information(self, "No Selection", "Please select a process from the table first.")
            return

        reply = QMessageBox.warning(
            self,
            "Confirm End Process",
            f"Are you sure you want to terminate {proc.name} (PID {proc.pid})?\n"
            "Unsaved work in this application may be lost.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            protected_names = {a.process_name for a in self.db.get_protected_apps()}
            success, msg = ProcessManager.terminate_process(proc.pid, protected_names)
            self.action_logged.emit(proc.name, "Terminate Process", msg)
            if success:
                QMessageBox.information(self, "Process Terminated", msg)
            else:
                QMessageBox.warning(self, "Action Denied", msg)

    def _on_protect_app(self):
        proc = self._get_selected_proc()
        if not proc:
            QMessageBox.information(self, "No Selection", "Please select a process from the table first.")
            return

        added = self.db.add_protected_app(proc.name, proc.name)
        if added:
            QMessageBox.information(
                self,
                "Protected Wishlist Updated",
                f"'{proc.name}' is now protected from automatic throttling and termination."
            )
            self.protected_apps_updated.emit()
            self._render_table()
        else:
            QMessageBox.information(
                self,
                "Already Protected",
                f"'{proc.name}' is already in your protected wishlist."
            )
