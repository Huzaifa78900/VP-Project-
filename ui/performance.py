"""
Performance page for PowerGuard OS Monitor.
Provides live CPU, RAM, and Disk telemetry, per-core CPU bars,
disk partitions breakdown, and real-time pyqtgraph charts.
"""
from typing import List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
    QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView,
    QScrollArea, QFrame
)
from PyQt6.QtCore import Qt
from database.models import CPUSnapshot, RAMSnapshot, DiskSnapshot
from widgets.charts import LiveMetricChart
from resources.styles import (
    COLOR_BG, COLOR_SURFACE, COLOR_BORDER, COLOR_BORDER_LIGHT,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    COLOR_PRIMARY, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER
)


class PerformancePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet(f"background-color: {COLOR_BG}; border: none;")

        content_widget = QWidget()
        content_widget.setStyleSheet(f"background-color: {COLOR_BG};")
        self.main_layout = QVBoxLayout(content_widget)
        self.main_layout.setContentsMargins(28, 24, 28, 28)
        self.main_layout.setSpacing(20)

        scroll_area.setWidget(content_widget)
        outer_layout.addWidget(scroll_area)

        # 1. Header
        header = QVBoxLayout()
        title_lbl = QLabel("Performance & Hardware Monitor")
        title_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 24px; font-weight: 700;")
        sub_lbl = QLabel("Live hardware utilization, core distribution, memory mapping, and disk telemetry.")
        sub_lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 13px;")
        header.addWidget(title_lbl)
        header.addWidget(sub_lbl)
        self.main_layout.addLayout(header)

        # 2. Live Pyqtgraph Charts (CPU, RAM, Disk)
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(16)

        self.chart_cpu = LiveMetricChart("Live CPU Utilization", "%", 100.0, COLOR_PRIMARY, self)
        charts_layout.addWidget(self.chart_cpu)

        self.chart_ram = LiveMetricChart("Live RAM Utilization", "%", 100.0, COLOR_SUCCESS, self)
        charts_layout.addWidget(self.chart_ram)

        self.chart_disk = LiveMetricChart("Disk I/O Activity", "MB/s", 50.0, COLOR_WARNING, self)
        charts_layout.addWidget(self.chart_disk)

        self.main_layout.addLayout(charts_layout)

        # 3. CPU Core Breakdown & RAM Details (2 Columns)
        details_layout = QHBoxLayout()
        details_layout.setSpacing(16)

        # Left: CPU Core Details
        self.cpu_card = self._build_cpu_details_card()
        details_layout.addWidget(self.cpu_card, stretch=55)

        # Right: RAM Breakdown Card
        self.ram_card = self._build_ram_details_card()
        details_layout.addWidget(self.ram_card, stretch=45)

        self.main_layout.addLayout(details_layout)

        # 4. Disk Partitions & I/O Table
        self.disk_card = self._build_disk_partitions_card()
        self.main_layout.addWidget(self.disk_card)

    def _build_cpu_details_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("CpuDetailsCard")
        card.setStyleSheet(f"""
            QFrame#CpuDetailsCard {{
                background-color: {COLOR_SURFACE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Card Title Row
        top_row = QHBoxLayout()
        title = QLabel("Processor Architecture & Core Distribution")
        title.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px; font-weight: 700;")
        top_row.addWidget(title)
        top_row.addStretch()

        self.cpu_meta_lbl = QLabel("0 Cores • 0.00 GHz")
        self.cpu_meta_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px; font-weight: 600;")
        top_row.addWidget(self.cpu_meta_lbl)
        layout.addLayout(top_row)

        # Per-core grid
        self.core_bars_grid = QGridLayout()
        self.core_bars_grid.setSpacing(8)
        self.core_bars = []
        self.core_labels = []

        layout.addLayout(self.core_bars_grid)
        return card

    def _build_ram_details_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("RamDetailsCard")
        card.setStyleSheet(f"""
            QFrame#RamDetailsCard {{
                background-color: {COLOR_SURFACE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("System Memory (RAM) Allocation")
        title.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px; font-weight: 700;")
        layout.addWidget(title)

        # Overall RAM bar
        self.ram_total_bar = QProgressBar()
        self.ram_total_bar.setFixedHeight(8)
        self.ram_total_bar.setTextVisible(False)
        self.ram_total_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #EFEBE3;
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {COLOR_SUCCESS};
                border-radius: 4px;
            }}
        """)
        layout.addWidget(self.ram_total_bar)

        # Stats rows
        self.ram_used_val = QLabel("Used: 0.0 GB")
        self.ram_used_val.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px; font-weight: 600;")

        self.ram_avail_val = QLabel("Available: 0.0 GB")
        self.ram_avail_val.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px; font-weight: 600;")

        self.ram_total_val = QLabel("Total: 0.0 GB")
        self.ram_total_val.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")

        stats_layout = QGridLayout()
        stats_layout.addWidget(self.ram_used_val, 0, 0)
        stats_layout.addWidget(self.ram_avail_val, 0, 1)
        stats_layout.addWidget(self.ram_total_val, 1, 0)

        layout.addLayout(stats_layout)
        layout.addStretch()
        return card

    def _build_disk_partitions_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("DiskPartitionsCard")
        card.setStyleSheet(f"""
            QFrame#DiskPartitionsCard {{
                background-color: {COLOR_SURFACE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Top row: title & live I/O speed counters
        top_row = QHBoxLayout()
        title = QLabel("Storage Drives & Real Disk I/O Activity")
        title.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px; font-weight: 700;")
        top_row.addWidget(title)
        top_row.addStretch()

        self.disk_io_lbl = QLabel("Read: 0.0 MB/s • Write: 0.0 MB/s")
        self.disk_io_lbl.setStyleSheet(f"color: {COLOR_WARNING}; font-size: 12px; font-weight: 700;")
        top_row.addWidget(self.disk_io_lbl)
        layout.addLayout(top_row)

        # Partitions Table
        self.partitions_table = QTableWidget()
        self.partitions_table.setColumnCount(6)
        self.partitions_table.setHorizontalHeaderLabels([
            "Drive", "Mount Point", "File System", "Used Space", "Free Space", "Utilization"
        ])
        self.partitions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.partitions_table.verticalHeader().setVisible(False)
        self.partitions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.partitions_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.partitions_table.setFixedHeight(120)

        layout.addWidget(self.partitions_table)
        return card

    def update_metrics(self, cpu: CPUSnapshot, ram: RAMSnapshot, disk: DiskSnapshot):
        # 1. Update charts
        self.chart_cpu.add_point(cpu.percent, f"{cpu.percent:.1f}%")
        self.chart_ram.add_point(ram.percent, f"{ram.percent:.1f}%")
        total_io = disk.read_speed_mb + disk.write_speed_mb
        self.chart_disk.add_point(total_io, f"{total_io:.2f} MB/s")

        # 2. Update CPU Core details
        self.cpu_meta_lbl.setText(f"{cpu.physical_cores if hasattr(cpu, 'physical_cores') else cpu.core_count} Physical / {cpu.logical_count} Logical • {cpu.current_freq:.2f} GHz")

        # Dynamically build or update per-core bars
        num_cores = len(cpu.per_core)
        if len(self.core_bars) != num_cores:
            # Recreate bars
            for b in self.core_bars:
                b.deleteLater()
            for l in self.core_labels:
                l.deleteLater()
            self.core_bars.clear()
            self.core_labels.clear()

            cols = 2 if num_cores <= 8 else 4
            for i in range(num_cores):
                lbl = QLabel(f"Core {i}: 0%")
                lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 11px;")
                bar = QProgressBar()
                bar.setFixedHeight(6)
                bar.setTextVisible(False)
                bar.setRange(0, 100)
                bar.setStyleSheet(f"""
                    QProgressBar {{
                        background-color: #EFEBE3;
                        border: none;
                        border-radius: 3px;
                    }}
                    QProgressBar::chunk {{
                        background-color: {COLOR_PRIMARY};
                        border-radius: 3px;
                    }}
                """)
                row = i // cols
                col = (i % cols) * 2
                self.core_bars_grid.addWidget(lbl, row, col)
                self.core_bars_grid.addWidget(bar, row, col + 1)
                self.core_labels.append(lbl)
                self.core_bars.append(bar)

        for i, val in enumerate(cpu.per_core):
            if i < len(self.core_bars):
                self.core_bars[i].setValue(int(val))
                self.core_labels[i].setText(f"Core {i}: {val:.0f}%")

        # 3. Update RAM
        self.ram_total_bar.setValue(int(ram.percent))
        self.ram_used_val.setText(f"Used: {ram.used_gb:.1f} GB ({ram.percent:.1f}%)")
        self.ram_avail_val.setText(f"Available: {ram.available_gb:.1f} GB")
        self.ram_total_val.setText(f"Total Installed: {ram.total_gb:.1f} GB")

        # 4. Update Disk Partitions Table
        self.disk_io_lbl.setText(f"Read: {disk.read_speed_mb:.2f} MB/s • Write: {disk.write_speed_mb:.2f} MB/s")

        self.partitions_table.setRowCount(len(disk.partitions))
        for row, p in enumerate(disk.partitions):
            self.partitions_table.setItem(row, 0, QTableWidgetItem(p.device))
            self.partitions_table.setItem(row, 1, QTableWidgetItem(p.mountpoint))
            self.partitions_table.setItem(row, 2, QTableWidgetItem(p.fstype))
            self.partitions_table.setItem(row, 3, QTableWidgetItem(f"{p.used_gb:.1f} GB"))
            self.partitions_table.setItem(row, 4, QTableWidgetItem(f"{p.free_gb:.1f} GB"))

            pct_item = QTableWidgetItem(f"{p.percent:.1f}%")
            self.partitions_table.setItem(row, 5, pct_item)
