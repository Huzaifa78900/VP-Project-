"""
PowerGuard OS Monitor
Smart Desktop Assistant for Battery & System Performance

Visual Programming University Project
Entry point of the application.
"""
import sys
import os
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from database.db import DatabaseManager
from ui.main_window import MainWindow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("PowerGuard")


def main():
    logger.info("Initializing PowerGuard OS Monitor...")

    # Enable High DPI scaling and modern rendering attributes
    if hasattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("PowerGuard OS Monitor")
    app.setApplicationDisplayName("PowerGuard OS Monitor")
    app.setOrganizationName("PowerGuard")

    # Initialize SQLite Database
    db = DatabaseManager()

    # Create & display Main Window
    window = MainWindow(db)
    window.show()

    logger.info("PowerGuard user interface launched successfully.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
