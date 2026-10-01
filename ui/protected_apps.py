"""
Protected Applications (Wishlist) page for PowerGuard OS Monitor.
Provides persistent wishlist management ensuring essential apps
are never throttled, suspended, or terminated during battery optimizations.
"""
from typing import List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QFrame, QDialog, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from database.db import DatabaseManager
from database.models import ProtectedAppEntry, ProcessItem
from resources.styles import (
    COLOR_BG, COLOR_SURFACE, COLOR_BORDER, COLOR_BORDER_LIGHT,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    COLOR_PRIMARY, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER
)
from resources.icons import get_icon, get_pixmap


class SelectProcessDialog(QDialog):
    """Dialog allowing user to choose from currently running processes."""
    def __init__(self, running_procs: List[ProcessItem], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Running Application to Protect")
        self.resize(380, 420)
        self.selected_name = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        lbl = QLabel("Choose an active process from the list:")
        lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-weight: 600;")
        layout.addWidget(lbl)

        # Search
        self.search = QLineEdit()
        self.search.setPlaceholderText("Filter running apps...")
        self.search.textChanged.connect(self._filter_list)
        layout.addWidget(self.search)

        self.list_widget = QListWidget()
        # Unique names
        self.unique_names = sorted(list(set(p.name for p in running_procs if p.pid > 4)))
        for name in self.unique_names:
            self.list_widget.addItem(name)

        layout.addWidget(self.list_widget)

        # Buttons
        btns = QHBoxLayout()
        btns.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_cancel)

        btn_add = QPushButton("Protect App")
        btn_add.setProperty("role", "primary")
        btn_add.clicked.connect(self._on_add)
        btns.addWidget(btn_add)

        layout.addLayout(btns)

    def _filter_list(self, text: str):
        t = text.lower()
        self.list_widget.clear()
        for name in self.unique_names:
            if t in name.lower():
                self.list_widget.addItem(name)

    def _on_add(self):
        item = self.list_widget.currentItem()
        if item:
            self.selected_name = item.text()
            self.accept()
        else:
            QMessageBox.information(self, "No Selection", "Please pick an application from the list.")


class ProtectedAppsPage(QWidget):
    wishlist_changed = pyqtSignal()

    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.running_processes: List[ProcessItem] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(16)

        # 1. Header
        header = QVBoxLayout()
        header.setSpacing(2)
        title_lbl = QLabel("Protected Applications (Wishlist)")
        title_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 24px; font-weight: 700;")
        sub_lbl = QLabel("Applications listed here are immune to priority reduction and automated suspension.")
        sub_lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 13px;")
        header.addWidget(title_lbl)
        header.addWidget(sub_lbl)
        layout.addLayout(header)

        # 2. Add Controls Toolbar
        toolbar_card = QFrame()
        toolbar_card.setObjectName("ToolbarCard")
        toolbar_card.setStyleSheet(f"""
            QFrame#ToolbarCard {{
                background-color: {COLOR_SURFACE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 12px;
            }}
        """)
        t_layout = QHBoxLayout(toolbar_card)
        t_layout.setContentsMargins(16, 12, 16, 12)
        t_layout.setSpacing(10)

        # Text input for custom process name
        self.input_app_name = QLineEdit()
        self.input_app_name.setPlaceholderText("Enter executable name (e.g. spotify.exe, code.exe)...")
        self.input_app_name.returnPressed.connect(self._on_add_custom)
        t_layout.addWidget(self.input_app_name)

        btn_add = QPushButton("Add to Wishlist")
        btn_add.setProperty("role", "primary")
        btn_add.setIcon(get_icon("plus", color="#FFFFFF", size=14))
        btn_add.clicked.connect(self._on_add_custom)
        t_layout.addWidget(btn_add)

        btn_browse = QPushButton("Pick from Running Apps")
        btn_browse.setIcon(get_icon("apps", color=COLOR_TEXT_PRIMARY, size=15))
        btn_browse.clicked.connect(self._on_pick_running)
        t_layout.addWidget(btn_browse)

        layout.addWidget(toolbar_card)

        # 3. Table of Protected Apps
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Protected Application", "Description / Path", "Date Added", "Action"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(self.table)

        self.refresh_table()

    def set_running_processes(self, procs: List[ProcessItem]):
        self.running_processes = procs

    def refresh_table(self):
        apps = self.db.get_protected_apps()
        self.table.setRowCount(len(apps))

        for row, app in enumerate(apps):
            # 0. Name with check icon
            name_item = QTableWidgetItem(f"  {app.process_name}")
            name_item.setIcon(get_icon("shield-check", color=COLOR_SUCCESS, size=14))

            # 1. Path / Description
            path_item = QTableWidgetItem(app.process_path or "User Configured")

            # 2. Date
            date_item = QTableWidgetItem(app.created_at)

            # 3. Remove Button
            remove_btn = QPushButton("Remove")
            remove_btn.setFixedSize(70, 26)
            remove_btn.setProperty("role", "danger")
            remove_btn.clicked.connect(lambda checked, app_id=app.id, name=app.process_name: self._on_remove(app_id, name))

            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, path_item)
            self.table.setItem(row, 2, date_item)
            self.table.setCellWidget(row, 3, remove_btn)

    def _on_add_custom(self):
        name = self.input_app_name.text().strip()
        if not name:
            return

        if not name.endswith(".exe"):
            name += ".exe"

        added = self.db.add_protected_app(name, "User Specified")
        if added:
            self.input_app_name.clear()
            self.refresh_table()
            self.wishlist_changed.emit()
            QMessageBox.information(self, "App Protected", f"'{name}' added to protected wishlist.")
        else:
            QMessageBox.information(self, "Already Exists", f"'{name}' is already in the wishlist.")

    def _on_pick_running(self):
        dlg = SelectProcessDialog(self.running_processes, self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.selected_name:
            added = self.db.add_protected_app(dlg.selected_name, "Selected from Running Processes")
            if added:
                self.refresh_table()
                self.wishlist_changed.emit()
                QMessageBox.information(self, "App Protected", f"'{dlg.selected_name}' added to protected wishlist.")
            else:
                QMessageBox.information(self, "Already Exists", f"'{dlg.selected_name}' is already in the wishlist.")

    def _on_remove(self, app_id: int, name: str):
        reply = QMessageBox.question(
            self,
            "Remove from Protected Apps",
            f"Remove '{name}' from the protected wishlist?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.remove_protected_app(app_id)
            self.refresh_table()
            self.wishlist_changed.emit()
