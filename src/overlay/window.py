"""PyQt5 透明覆盖层窗口"""

import logging
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter

from src.config import OVERLAY_FPS

logger = logging.getLogger("nikke-overlay")


class OverlayWindow(QWidget):
    """透明、置顶、无边框覆盖层窗口"""

    _paint_count = 0

    def __init__(self, renderer=None, parent=None):
        super().__init__(parent)
        self._renderer = renderer

        # 窗口标志
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

        # 刷新定时器
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000 // OVERLAY_FPS)

    def set_renderer(self, renderer):
        self._renderer = renderer

    def resize_to(self, x: int, y: int, w: int, h: int):
        """调整覆盖层位置和尺寸"""
        self.setGeometry(x, y, w, h)
        logger.debug(f"覆盖层位置: ({x},{y}) {w}x{h}")

    def _tick(self):
        """每帧触发的更新"""
        self.update()

    def paintEvent(self, event):
        """Qt 绘制事件"""
        self._paint_count += 1
        if self._paint_count % 30 == 0:
            has_traj = len(self._renderer.trajectory) if self._renderer else -1
            logger.debug(f"绘制 #{self._paint_count}, trajectory={has_traj}pts, renderer={self._renderer is not None}")
        if self._renderer:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            self._renderer.draw(painter, self.width(), self.height())
            painter.end()
