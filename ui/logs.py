"""
Logs & Optimization History page for PowerGuard OS Monitor.
Provides persistent audit trail, filtering, search, and CSV export.
"""
import os
from typing import List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QMessageBox, QFileDialog, QFrame
)
from PyQt6.QtCore import Qt
from database.db import DatabaseManager
from database.models import OptimizationLogEntry
from resources.styles import (
    COLOR_BG, COLOR_SURFACE, COLOR_BORDER, COLOR_BORDER_LIGHT,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    COLOR_PRIMARY, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER
)
from resources.icons import get_icon, get_pixmap


class LogsPage(QWidget):
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(16)

        # 1. Header
        header = QVBoxLayout()
        header.setSpacing(2)
        title_lbl = QLabel("Optimization Logs & Audit History")
        title_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 24px; font-weight: 700;")
        sub_lbl = QLabel("Complete timeline of autonomous power adjustments, process actions, and battery triggers.")
        sub_lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 13px;")
        header.addWidget(title_lbl)
        header.addWidget(sub_lbl)
        layout.addLayout(header)

        # 2. Filter Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        # Search Input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search logs by process, action, or reason...")
        self.search_input.setFixedWidth(280)
        self.search_input.textChanged.connect(self.refresh_logs)
        toolbar.addWidget(self.search_input)

        # Mode Filter
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["All Modes", "Normal", "Power Saver", "Emergency"])
        self.combo_mode.currentIndexChanged.connect(self.refresh_logs)
        toolbar.addWidget(self.combo_mode)

        toolbar.addStretch()

        # Export CSV Button
        self.btn_export = QPushButton("Export CSV")
        self.btn_export.setIcon(get_icon("export", color=COLOR_TEXT_PRIMARY, size=15))
        self.btn_export.clicked.connect(self.export_csv)
        toolbar.addWidget(self.btn_export)

        # Clear Logs Button
        self.btn_clear = QPushButton("Clear Logs")
        self.btn_clear.setIcon(get_icon("trash", color=COLOR_TEXT_PRIMARY, size=15))
        self.btn_clear.clicked.connect(self.clear_logs)
        toolbar.addWidget(self.btn_clear)

        layout.addLayout(toolbar)

        # 3. Logs Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Timestamp", "Process Name", "PID", "Action Taken", "Reason / Trigger", "Battery", "Mode", "Result"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)

        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(self.table)

        self.refresh_logs()

    def refresh_logs(self):
        search_query = self.search_input.text().strip()
        mode_filter = self.combo_mode.currentText()
        if mode_filter == "All Modes":
            mode_filter = ""

        logs = self.db.get_optimization_logs(
            limit=250,
            search=search_query,
            mode=mode_filter
        )

        self.table.setRowCount(len(logs))
        for row, entry in enumerate(logs):
            # 0. Timestamp
            self.table.setItem(row, 0, QTableWidgetItem(entry.timestamp))

            # 1. Process Name
            self.table.setItem(row, 1, QTableWidgetItem(entry.process_name or "System"))

            # 2. PID
            pid_str = str(entry.pid) if entry.pid > 0 else "-"
            item_pid = QTableWidgetItem(pid_str)
            item_pid.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, item_pid)

            # 3. Action
            self.table.setItem(row, 3, QTableWidgetItem(entry.action))

            # 4. Reason
            self.table.setItem(row, 4, QTableWidgetItem(entry.reason))

            # 5. Battery
            item_batt = QTableWidgetItem(f"{entry.battery_percentage:.0f}%")
            item_batt.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 5, item_batt)

            # 6. Mode
            item_mode = QTableWidgetItem(entry.mode)
            item_mode.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 6, item_mode)

            # 7. Result
            item_res = QTableWidgetItem(entry.result)
            if "Success" in entry.result or "Active" in entry.result:
                item_res.setForeground(Qt.GlobalColor.darkGreen)
            elif "Protected" in entry.result:
                item_res.setForeground(Qt.GlobalColor.blue)
            self.table.setItem(row, 7, item_res)

    def export_csv(self):
        default_name = "powerguard_logs.csv"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Optimization Logs to CSV",
            default_name,
            "CSV Files (*.csv)"
        )
        if path:
            success = self.db.export_logs_to_csv(path)
            if success:
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Optimization audit logs successfully exported to:\n{path}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Export Failed",
                    "Unable to write CSV file. Please check folder permissions."
                )

    def clear_logs(self):
        reply = QMessageBox.question(
            self,
            "Clear Logs Confirmation",
            "Are you sure you want to permanently erase all optimization logs?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.clear_logs()
            self.refresh_logs()
            QMessageBox.information(self, "Logs Cleared", "All log history has been cleared.")
