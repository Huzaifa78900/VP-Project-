# PowerGuard OS Monitor
> **Smart Desktop Assistant for Battery & System Performance**  
> *Visual Programming University Project*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)](https://riverbankcomputing.com/software/pyqt/)
[![Design](https://img.shields.io/badge/Theme-Warm%20Beige%20%2F%20Soft%20Sand-E2D7C7.svg)](#visual-identity)
[![License](https://img.shields.io/badge/License-Academic-lightgrey.svg)](#)

---

## 1. Project Overview

**PowerGuard OS Monitor** is a desktop application designed for Windows laptops and workstations. It continuously monitors live system vitals—**Battery, CPU, RAM, Storage Disks, and Running Processes**—and autonomously executes intelligent power-saving actions when battery reserves drop.

### The Core Concept:
$$\text{BATTERY} \longrightarrow \text{SYSTEM} \longrightarrow \text{SMART ACTION}$$
> *"From a low-battery warning to an intelligent response."*

Unlike static UI mockups, **PowerGuard functions exclusively on real hardware telemetry** queried directly from the Windows OS via `psutil`, native Windows APIs, and asynchronous multithreading.

---

## 2. Visual Identity & Aesthetics (Design 2)

PowerGuard strictly adheres to **Design 2 — Warm Beige / Soft Sand** from the project design specifications:

- **Background:** Warm off-white / soft sand (`#FAF8F5`)
- **Primary Accent:** Soft purple (`#8B5CF6`)
- **Success State:** Fresh green (`#10B981`)
- **Warning State:** Warm orange (`#F59E0B`)
- **Danger / Emergency:** Soft red (`#EF4444`)
- **Card Surfaces:** Warm white (`#FFFFFF`) with thin borders (`#E8E2D8`) and 12px rounded corners
- **Typography:** `Segoe UI`, crisp hierarchy, generous whitespace, and modern SVG vector icons

Purple is strictly utilized as a refined accent (selected navigation, active states, key action buttons) rather than dominating the entire interface.

---

## 3. Key Features

### 📊 Live Dashboard
- **Greeting & System Status:** Dynamic greeting by time of day, active status indicator (`● System Active`), and real-time clock.
- **4 Real-Time Metric Cards:**
  - **Battery:** Percentage, charging/discharging state, remaining time calculation.
  - **CPU Usage:** Overall percentage, live processor clock frequency (GHz), physical core count.
  - **RAM Usage:** Memory percentage, used GB vs total installed capacity.
  - **Disk Usage:** Primary partition storage consumption and free capacity.
- **Battery Usage Trend:** Anti-aliased `pyqtgraph` area chart with soft green gradient fill and `1h`, `24h`, and `7d` history filters.
- **Battery Optimization Modes:** Visual indicators for **Normal Mode**, **Power Saver Mode**, and **Emergency Mode**.
- **Quick Actions:** Instant buttons to view audit logs, export CSV reports, or configure the wishlist.
- **Triage Cards:** Top applications by resource consumption, protected apps wishlist, and recent optimization activity.

### ⚡ Performance & Hardware Monitor
- Real-time `pyqtgraph` rolling history charts for CPU, RAM, and Disk I/O activity (MB/s).
- **Per-core CPU distribution bars** dynamically generated for all physical/logical processor cores.
- **Drive Partitions Table:** Real partitions (`C:\`, etc.), filesystem types, used/free space, and capacity utilization.

### 🔋 Battery Intelligence
- Circular health gauge with dynamic color states (Green > 30%, Orange ≤ 30%, Red ≤ 15%).
- AC wall outlet vs battery discharge status.
- Battery discharge rate and estimated remaining battery runtime.

### ⚙️ Windows Process Manager
- Live iteration of Windows processes (`psutil.process_iter`).
- Real-time search filter by process name or PID.
- Process actions: **Lower Priority**, **Restore Priority**, **Suspend**, **Resume**, **End Task**.
- **Process Safety Layer:** Automatically forbids modifying critical Windows processes (`smss.exe`, `csrss.exe`, `services.exe`, `explorer.exe`, etc.) and self-protects PowerGuard.

### 🛡️ Protected Applications (Wishlist)
- Users can add essential software (e.g., `code.exe`, `chrome.exe`, `python.exe`) to a persistent wishlist.
- Protected applications are **immune** to automated throttling, priority demotion, or suspension.

### 📝 Audit Logs & CSV Export
- Persistent logging of mode transitions, automated priority adjustments, and safety exceptions in SQLite.
- Interactive filtering by operating mode and keyword search.
- **One-click CSV Export** (`QFileDialog`) for academic and performance auditing.

### 🔔 System Tray Integration
- Minimizes to Windows Notification Area with custom tray icon.
- Context menu with live battery status, operating mode, and optimization state.
- Windows desktop balloon notifications for mode changes and automated actions.

---

## 4. Visual Programming Concepts Demonstrated

This project showcases core principles of **Visual Programming (VP)**:

1. **Event-Driven Architecture:**
   - GUI reacts asynchronously to internal timers, thread signals, and user events without blocking.
2. **PyQt6 Signals & Slots:**
   - Decoupled communication across the system (e.g., worker thread emits `metrics_updated`, received concurrently by Dashboard, Performance, Battery, and Sidebar widgets).
3. **Multithreading with `QThread`:**
   - Dedicated `MonitorWorker(QThread)` handles OS telemetry polling, preventing GUI lag or freezing.
4. **Database Connectivity & Persistence:**
   - SQLite integration (`DatabaseManager`) with WAL (Write-Ahead Logging) mode for concurrent access across worker and UI threads.
5. **Real-Time Data Visualization:**
   - Hardware-accelerated vector charting using `pyqtgraph` with custom axes formatting and time range filters.
6. **State & Decision Machine:**
   - `SmartOptimizer` evaluates system state against configurable threshold rules.

---

## 5. Project Architecture

```
PowerGuard/
│
├── main.py                     # Application entry point & Qt event loop
├── requirements.txt            # Project dependencies
├── README.md                   # Complete documentation
├── test_app.py                 # Automated verification test suite
│
├── database/                   # SQLite persistence layer
│   ├── __init__.py
│   ├── db.py                   # Thread-safe SQLite manager & CSV exporter
│   └── models.py               # Data classes (Snapshots, Logs, Settings)
│
├── monitoring/                 # Hardware telemetry sub-modules
│   ├── __init__.py
│   ├── monitor_worker.py       # QThread background worker
│   ├── battery_monitor.py      # psutil battery queries & time calculations
│   ├── cpu_monitor.py          # CPU usage, per-core metrics, frequencies
│   ├── memory_monitor.py       # Virtual RAM allocations
│   ├── disk_monitor.py         # Partitions & delta disk I/O rates
│   └── process_monitor.py      # Windows process telemetry & top hogs
│
├── optimization/               # Automated response & safety engine
│   ├── __init__.py
│   ├── safety.py               # Windows critical process safety firewall
│   ├── process_manager.py      # Process priority, suspend, resume, kill
│   └── optimizer.py            # Battery mode evaluator & throttler
│
├── resources/                  # Design tokens & vector graphics
│   ├── __init__.py
│   ├── styles.py               # Warm Beige Design 2 stylesheet tokens
│   └── icons.py                # Crisp scalable SVG vector icon provider
│
├── widgets/                    # Reusable custom UI components
│   ├── __init__.py
│   ├── metric_card.py          # Metric card with progress indicator
│   ├── toggle_switch.py        # Animated toggle switch (On / Off)
│   ├── mode_card.py            # Battery mode cards (Normal, Saver, Emergency)
│   ├── charts.py               # pyqtgraph BatteryTrend & LiveMetric charts
│   ├── sidebar.py              # Warm Beige sidebar with health card
│   └── status_card.py          # Quick Actions, Top Apps, Activity cards
│
└── ui/                         # Main window & application views
    ├── __init__.py
    ├── main_window.py          # Main QMainWindow & system tray
    ├── dashboard.py            # Dashboard view (Design 2 layout)
    ├── performance.py          # Performance & hardware details view
    ├── apps_widgets.py         # Apps footprint view
    ├── battery.py              # Detailed battery analytics view
    ├── processes.py            # Process manager table & controls
    ├── protected_apps.py       # Wishlist manager view
    ├── logs.py                 # Audit logs & CSV export view
    └── settings.py             # User configuration view
```

---

## 6. Installation & Setup

### Prerequisites
- Windows 10 or Windows 11
- Python 3.10+ (Python 3.12 recommended)

### Step-by-Step Instructions

1. **Clone or Open the Repository:**
   ```powershell
   cd "c:\Users\lenovo\Desktop\vp project"
   ```

2. **Create a Virtual Environment (Recommended):**
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Run the Application:**
   ```powershell
   python main.py
   ```

5. **Run the Verification Suite:**
   ```powershell
   python test_app.py
   ```

---

## 7. Administrator Permissions Note

PowerGuard does **not** require administrator permissions for routine monitoring (CPU, RAM, Disk, Battery, Process viewing, Wishlist management, Logging, and CSV export).

However, Windows OS security prevents standard users from modifying the priority of processes owned by other user accounts or elevated services. If you intend to throttle third-party background applications that run elevated, right-click your terminal or Python shortcut and select **"Run as Administrator"**.

If an action is blocked by Windows security, PowerGuard handles it gracefully with a friendly message:
> *"Unable to modify this process. Windows may require administrator permission, or the process may have already exited."*

---

## 8. Database Schema

Stored in `powerguard.db` in SQLite:

- `settings`: Key-value storage for thresholds, polling intervals, and notification preferences.
- `protected_apps`: Process names and paths safeguarded from automated actions.
- `battery_history`: Historical battery percentage and charging timestamps.
- `system_history`: Historical CPU, RAM, and Disk percentage metrics.
- `optimization_logs`: Timestamped audit trail of all mode transitions, process priority modifications, and skipped protected apps.

---

## 9. Academic Project Credits

- **Course:** Visual Programming (VP)
- **Project Title:** PowerGuard OS Monitor
- **Subtitle:** Smart Desktop Assistant for Battery & System Performance
- **Visual Design:** Design 2 — Warm Beige / Soft Sand
