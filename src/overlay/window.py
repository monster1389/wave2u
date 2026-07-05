"""PyQt5 透明覆盖层窗口

使用全局鼠标钩子（GetAsyncKeyState）检测点击拖拽，
窗口本身设置 WA_TransparentForMouseEvents=True 让点击穿透到游戏。
"""

import ctypes
import logging
from typing import Optional, Callable

from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QCursor

from src.config import OVERLAY_FPS

logger = logging.getLogger("nikke-overlay")

# Windows 虚拟键码
VK_LBUTTON = 0x01


class OverlayWindow(QWidget):
    """透明、置顶、无边框覆盖层窗口（点击穿透）"""

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
        # 点击穿透：所有鼠标事件传递到下面的游戏窗口
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        # 刷新定时器（也用于轮询鼠标状态）
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000 // OVERLAY_FPS)

    def set_renderer(self, renderer):
        self._renderer = renderer

    def resize_to(self, x: int, y: int, w: int, h: int):
        current = self.geometry()
        if (x, y, w, h) != (current.x(), current.y(), current.width(), current.height()):
            self.setGeometry(x, y, w, h)
            logger.debug(f"覆盖层位置更新: ({x},{y}) {w}x{h}")

    def _tick(self):
        """每帧：轮询全局鼠标 + 触发重绘"""
        self._poll_mouse()
        self.update()

    # ── 全局鼠标轮询（不依赖窗口事件） ──

    _prev_left = False

    def _poll_mouse(self):
        """用 Windows API 检测全局鼠标状态"""
        pos = QCursor.pos()  # 全局屏幕坐标
        left_down = (ctypes.windll.user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000) != 0

        if left_down and not self._prev_left:
            # 鼠标按下
            self._dragging = True
            self._start_pos = (pos.x(), pos.y())
            self._current_pos = (pos.x(), pos.y())
            logger.debug(f"全局鼠标按下: ({pos.x()}, {pos.y()})")
            if self.on_drag_start:
                self.on_drag_start(pos.x(), pos.y())

        elif left_down and self._prev_left and self._dragging:
            # 拖拽中
            self._current_pos = (pos.x(), pos.y())
            if self.on_drag_move and self._start_pos:
                sx, sy = self._start_pos
                self.on_drag_move(sx, sy, pos.x(), pos.y())

        elif not left_down and self._prev_left and self._dragging:
            # 鼠标松开
            self._dragging = False
            if self.on_drag_end and self._start_pos:
                sx, sy = self._start_pos
                self.on_drag_end(sx, sy, self._current_pos[0], self._current_pos[1])

        self._prev_left = left_down

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
