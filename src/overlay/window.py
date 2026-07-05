"""PyQt5 透明覆盖层窗口"""

import logging
from typing import Optional, Callable

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QMouseEvent

from src.config import OVERLAY_FPS

logger = logging.getLogger("nikke-overlay")


class OverlayWindow(QWidget):
    """透明、置顶、无边框覆盖层窗口"""

    _paint_count = 0

    def __init__(self, renderer=None, parent=None):
        super().__init__(parent)
        self._renderer = renderer
        self._dragging = False
        self._start_pos: Optional[tuple[int, int]] = None
        self._current_pos: Optional[tuple[int, int]] = None

        # 外部回调
        self.on_drag_start: Optional[Callable[[int, int], None]] = None
        self.on_drag_move: Optional[Callable[[int, int, int, int], None]] = None
        self.on_drag_end: Optional[Callable[[int, int, int, int], None]] = None

        # 窗口标志
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

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

    # ── 鼠标事件：直接在窗口上重写，不依赖 eventFilter ──

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._start_pos = (event.x(), event.y())
            self._current_pos = (event.x(), event.y())
            logger.debug(f"鼠标按下: ({event.x()}, {event.y()})")
            if self.on_drag_start:
                self.on_drag_start(event.x(), event.y())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging:
            self._current_pos = (event.x(), event.y())
            if self.on_drag_move and self._start_pos:
                sx, sy = self._start_pos
                self.on_drag_move(sx, sy, event.x(), event.y())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._dragging and event.button() == Qt.LeftButton:
            self._dragging = False
            if self.on_drag_end and self._start_pos:
                sx, sy = self._start_pos
                self.on_drag_end(sx, sy, self._current_pos[0], self._current_pos[1])
            event.accept()
            return
        super().mouseReleaseEvent(event)

    # ── 绘制 ──

    def paintEvent(self, event):
        """Qt 绘制事件"""
        self._paint_count += 1
        if self._paint_count % 30 == 0:
            has_traj = len(self._renderer.trajectory) if self._renderer else -1
            logger.debug(f"绘制 #{self._paint_count}, trajectory={has_traj}pts")
        if self._renderer:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            self._renderer.draw(painter, self.width(), self.height())
            painter.end()
