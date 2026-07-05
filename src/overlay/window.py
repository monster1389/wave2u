"""PyQt5 透明覆盖层窗口

点击穿透使用 Windows API 直接设置 WS_EX_TRANSPARENT（Qt 的
WA_TransparentForMouseEvents 在此环境无效）。
鼠标拖拽检测使用全局钩子 GetAsyncKeyState + QCursor。
"""

import ctypes
import logging
from typing import Optional, Callable

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QCursor

from src.config import OVERLAY_FPS

logger = logging.getLogger("nikke-overlay")

# Windows 常量
VK_LBUTTON = 0x01
GWL_EXSTYLE = -20
WS_EX_TRANSPARENT = 0x00000020
WS_EX_LAYERED = 0x00080000
SWP_FRAMECHANGED = 0x0020
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010
SWP_NOZORDER = 0x0004


class OverlayWindow(QWidget):
    """透明、置顶、无边框覆盖层窗口"""

    _paint_count = 0
    _clickthrough_applied = False

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

    def showEvent(self, event):
        super().showEvent(event)
        # 窗口显示后：通过 Windows API 设置点击穿透
        QTimer.singleShot(0, self._enable_clickthrough)
        # 再延迟一次确保生效（模拟"切窗口再切回来"的效果）
        QTimer.singleShot(500, self._enable_clickthrough)

    def _enable_clickthrough(self):
        """用 Windows API 设置 WS_EX_TRANSPARENT 实现点击穿透"""
        try:
            hwnd = int(self.winId())
            user32 = ctypes.windll.user32

            # 读取当前扩展样式
            current = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            had_transparent = bool(current & WS_EX_TRANSPARENT)

            # 添加 WS_EX_TRANSPARENT（保留已有样式）
            new_style = current | WS_EX_TRANSPARENT
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)

            # SetWindowPos 使样式变更生效
            user32.SetWindowPos(
                hwnd, 0, 0, 0, 0, 0,
                SWP_FRAMECHANGED | SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_NOZORDER
            )

            if not had_transparent:
                logger.info("已启用点击穿透（WS_EX_TRANSPARENT）")
                self._clickthrough_applied = True
        except Exception as e:
            logger.warning(f"设置点击穿透失败: {e}")

    # ── 全局鼠标轮询 ──

    _prev_left = False

    def _tick(self):
        """每帧：轮询全局鼠标 + 触发重绘"""
        self._poll_mouse()
        self.update()

    def _poll_mouse(self):
        pos = QCursor.pos()
        left_down = (ctypes.windll.user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000) != 0

        if left_down and not self._prev_left:
            self._dragging = True
            self._start_pos = (pos.x(), pos.y())
            self._current_pos = (pos.x(), pos.y())
            if self.on_drag_start:
                self.on_drag_start(pos.x(), pos.y())

        elif left_down and self._prev_left and self._dragging:
            self._current_pos = (pos.x(), pos.y())
            if self.on_drag_move and self._start_pos:
                sx, sy = self._start_pos
                self.on_drag_move(sx, sy, pos.x(), pos.y())

        elif not left_down and self._prev_left and self._dragging:
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
