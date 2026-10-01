"""
Warm Beige / Soft Sand Design System (Design 2)
Matches the warm, modern, calm, and professional aesthetic of the reference UI.
"""

# Palette Constants
COLOR_BG = "#FAF8F5"           # Warm off-white / soft sand
COLOR_SURFACE = "#FFFFFF"      # Pure white card surface
COLOR_SURFACE_WARM = "#FCFAF8" # Warm cream card surface
COLOR_SIDEBAR = "#F4F0E8"      # Warm beige sidebar
COLOR_BORDER = "#E8E2D8"       # Delicate warm border
COLOR_BORDER_LIGHT = "#F0ECE4" # Subtle inner border
COLOR_NAV_ACTIVE = "#E4DACB"   # Soft warm tan/beige nav active background
COLOR_NAV_HOVER = "#ECE4D8"    # Soft beige nav hover

# Accent & Semantic Tokens
COLOR_PRIMARY = "#8B5CF6"      # Soft purple primary accent
COLOR_PRIMARY_HOVER = "#7C3AED"# Darker purple hover
COLOR_PRIMARY_LIGHT = "#F5F3FF"# Purple tint background
COLOR_SUCCESS = "#10B981"      # Fresh green
COLOR_SUCCESS_LIGHT = "#ECFDF5"# Green tint background
COLOR_WARNING = "#F59E0B"      # Warm orange
COLOR_WARNING_LIGHT = "#FFFBEB"# Orange tint background
COLOR_DANGER = "#EF4444"       # Soft red
COLOR_DANGER_LIGHT = "#FEF2F2" # Red tint background

# Typography Colors
COLOR_TEXT_PRIMARY = "#1E1A17"   # Deep charcoal / warm black
COLOR_TEXT_SECONDARY = "#615A52" # Neutral warm slate
COLOR_TEXT_MUTED = "#8E867B"     # Soft muted gray-beige
COLOR_TEXT_LIGHT = "#B0A89D"     # Light placeholder

MAIN_STYLESHEET = f"""
/* Global Window & Typography */
QMainWindow, QDialog, QWidget {{
    background-color: {COLOR_BG};
    color: {COLOR_TEXT_PRIMARY};
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
}}

/* Tooltips */
QToolTip {{
    background-color: {COLOR_SURFACE};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}}

/* Scrollbars */
QScrollBar:vertical {{
    border: none;
    background: transparent;
    width: 6px;
    margin: 0px 0px 0px 0px;
}}
QScrollBar::handle:vertical {{
    background: #D9D2C7;
    min-height: 25px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical:hover {{
    background: #BDB4A6;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
}}

QScrollBar:horizontal {{
    border: none;
    background: transparent;
    height: 6px;
}}
QScrollBar::handle:horizontal {{
    background: #D9D2C7;
    min-width: 25px;
    border-radius: 3px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* Buttons */
QPushButton {{
    background-color: #EDE8DE;
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 7px 14px;
    font-weight: 500;
    font-size: 13px;
}}
QPushButton:hover {{
    background-color: #E3DCCF;
    border-color: #D3CAB9;
}}
QPushButton:pressed {{
    background-color: #D7CFBF;
}}
QPushButton:disabled {{
    background-color: #F0ECE4;
    color: {COLOR_TEXT_MUTED};
    border-color: {COLOR_BORDER_LIGHT};
}}

/* Primary Purple Button */
QPushButton[role="primary"] {{
    background-color: {COLOR_PRIMARY};
    color: #FFFFFF;
    border: 1px solid {COLOR_PRIMARY};
    font-weight: 600;
}}
QPushButton[role="primary"]:hover {{
    background-color: {COLOR_PRIMARY_HOVER};
    border-color: {COLOR_PRIMARY_HOVER};
}}
QPushButton[role="primary"]:pressed {{
    background-color: #6D28D9;
}}

/* Success Button */
QPushButton[role="success"] {{
    background-color: {COLOR_SUCCESS};
    color: #FFFFFF;
    border: 1px solid {COLOR_SUCCESS};
    font-weight: 600;
}}
QPushButton[role="success"]:hover {{
    background-color: #059669;
    border-color: #059669;
}}

/* Danger Button */
QPushButton[role="danger"] {{
    background-color: {COLOR_DANGER};
    color: #FFFFFF;
    border: 1px solid {COLOR_DANGER};
    font-weight: 600;
}}
QPushButton[role="danger"]:hover {{
    background-color: #DC2626;
    border-color: #DC2626;
}}

/* Input Fields */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background-color: {COLOR_SURFACE};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 7px 12px;
    font-size: 13px;
    selection-background-color: {COLOR_PRIMARY};
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border: 1.5px solid {COLOR_PRIMARY};
    background-color: #FFFFFF;
}}
QComboBox::drop-down {{
    border: none;
    padding-right: 10px;
}}
QComboBox QAbstractItemView {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    selection-background-color: {COLOR_NAV_ACTIVE};
    selection-color: {COLOR_TEXT_PRIMARY};
    padding: 4px;
}}

/* Tables */
QTableWidget, QTableView {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: 10px;
    gridline-color: {COLOR_BORDER_LIGHT};
    selection-background-color: {COLOR_NAV_ACTIVE};
    selection-color: {COLOR_TEXT_PRIMARY};
    font-size: 12.5px;
}}
QHeaderView::section {{
    background-color: #F8F5EE;
    color: {COLOR_TEXT_SECONDARY};
    font-weight: 600;
    font-size: 12px;
    border: none;
    border-bottom: 1px solid {COLOR_BORDER};
    padding: 8px 10px;
    text-align: left;
}}
QTableWidget::item {{
    padding: 6px 10px;
    border-bottom: 1px solid {COLOR_BORDER_LIGHT};
}}
QTableWidget::item:selected {{
    background-color: {COLOR_NAV_ACTIVE};
    color: {COLOR_TEXT_PRIMARY};
}}

/* Checkboxes */
QCheckBox {{
    spacing: 8px;
    color: {COLOR_TEXT_PRIMARY};
    font-size: 13px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1.5px solid {COLOR_BORDER};
    background-color: {COLOR_SURFACE};
}}
QCheckBox::indicator:hover {{
    border-color: {COLOR_PRIMARY};
}}
QCheckBox::indicator:checked {{
    background-color: {COLOR_PRIMARY};
    border-color: {COLOR_PRIMARY};
}}

/* Progress Bars */
QProgressBar {{
    border: 1px solid {COLOR_BORDER_LIGHT};
    border-radius: 6px;
    background-color: #EFEBE3;
    text-align: center;
    color: {COLOR_TEXT_SECONDARY};
    font-size: 11px;
    font-weight: 600;
}}
QProgressBar::chunk {{
    background-color: {COLOR_PRIMARY};
    border-radius: 5px;
}}

/* Card Frame Base */
QFrame[role="card"] {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: 12px;
}}

/* Header and Labels */
QLabel[role="heading"] {{
    color: {COLOR_TEXT_PRIMARY};
    font-size: 22px;
    font-weight: 700;
}}
QLabel[role="subheading"] {{
    color: {COLOR_TEXT_SECONDARY};
    font-size: 13px;
}}
QLabel[role="card-title"] {{
    color: {COLOR_TEXT_SECONDARY};
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
QLabel[role="metric-value"] {{
    color: {COLOR_TEXT_PRIMARY};
    font-size: 26px;
    font-weight: 700;
}}
QLabel[role="metric-subtitle"] {{
    color: {COLOR_TEXT_MUTED};
    font-size: 12px;
}}
"""
