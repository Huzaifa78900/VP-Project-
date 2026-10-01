"""
Modern animated pill toggle switch for PowerGuard.
Used for Smart Battery Optimization (ON / OFF).
"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, pyqtProperty
from resources.styles import (
    COLOR_SUCCESS, COLOR_PRIMARY, COLOR_BORDER, COLOR_TEXT_PRIMARY, COLOR_TEXT_MUTED
)


class SwitchHandle(QWidget):
    def __init__(self, checked: bool = True, parent=None):
        super().__init__(parent)
        self.setFixedSize(46, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._checked = checked
        self._thumb_pos = 24.0 if checked else 2.0
        self._active_color = QColor(COLOR_SUCCESS)
        self._inactive_color = QColor("#D8D0C3")

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool):
        if self._checked != checked:
            self._checked = checked
            self._animate_thumb(checked)

    def _animate_thumb(self, checked: bool):
        self._anim = QPropertyAnimation(self, b"thumb_pos")
        self._anim.setDuration(160)
        self._anim.setStartValue(self._thumb_pos)
        self._anim.setEndValue(24.0 if checked else 2.0)
        self._anim.start()

    def get_thumb_pos(self) -> float:
        return self._thumb_pos

    def set_thumb_pos(self, pos: float):
        self._thumb_pos = pos
        self.update()

    thumb_pos = pyqtProperty(float, get_thumb_pos, set_thumb_pos)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)
            p = self.parent()
            if isinstance(p, ToggleSwitch):
                p.toggled.emit(self._checked)
                p.update_label()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Track background
        bg_color = self._active_color if self._checked else self._inactive_color
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 12, 12)

        # White Thumb
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawEllipse(int(self._thumb_pos), 2, 20, 20)
        painter.end()


class ToggleSwitch(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, text_on: str = "Optimization: On", text_off: str = "Optimization: Off", initial: bool = True, parent=None):
        super().__init__(parent)
        self.text_on = text_on
        self.text_off = text_off

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.handle = SwitchHandle(checked=initial, parent=self)
        self.label = QLabel(self.text_on if initial else self.text_off)
        self.label.setStyleSheet(f"""
            color: {COLOR_TEXT_PRIMARY};
            font-size: 12px;
            font-weight: 600;
        """)

        layout.addWidget(self.handle)
        layout.addWidget(self.label)

    def update_label(self):
        self.label.setText(self.text_on if self.handle.isChecked() else self.text_off)

    def isChecked(self) -> bool:
        return self.handle.isChecked()

    def setChecked(self, checked: bool):
        self.handle.setChecked(checked)
        self.update_label()
