"""PyQt5 透明覆盖层窗口"""

import ctypes
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
        self.update()

    # ── 窗口显示后修复 Windows 点击穿透问题 ──

    def showEvent(self, event):
        super().showEvent(event)
        # 确保窗口创建后重新设置鼠标事件属性
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        # Windows: 清除 WS_EX_TRANSPARENT 标记
        try:
            hwnd = int(self.winId())
            GWL_EXSTYLE = -20
            WS_EX_TRANSPARENT = 0x00000020
            WS_EX_LAYERED = 0x00080000
            user32 = ctypes.windll.user32
            current = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            # 保留 WS_EX_LAYERED，清除 WS_EX_TRANSPARENT
            new_style = (current | WS_EX_LAYERED) & ~WS_EX_TRANSPARENT
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
            logger.debug("已清除 WS_EX_TRANSPARENT（Windows 点击穿透）")
        except Exception as e:
            logger.warning(f"清除 WS_EX_TRANSPARENT 失败: {e}")

    # ── 鼠标事件 ──

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
        self._paint_count += 1
        if self._paint_count % 30 == 0:
            has_traj = len(self._renderer.trajectory) if self._renderer else -1
            logger.debug(f"绘制 #{self._paint_count}, trajectory={has_traj}pts")
        if self._renderer:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            self._renderer.draw(painter, self.width(), self.height())
            painter.end()
