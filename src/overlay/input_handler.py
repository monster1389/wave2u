"""鼠标输入处理器：点击+拖拽瞄准"""

from typing import Optional, Tuple, Callable
from PyQt5.QtCore import Qt, QObject, QEvent
from PyQt5.QtGui import QMouseEvent


class InputHandler(QObject):
    """处理覆盖层上的鼠标事件"""

    def __init__(self, overlay_widget):
        super().__init__(overlay_widget)
        self._widget = overlay_widget
        self._dragging = False
        self._start_pos: Optional[Tuple[int, int]] = None
        self._current_pos: Optional[Tuple[int, int]] = None

        # 回调
        self.on_drag_start: Optional[Callable[[int, int], None]] = None
        self.on_drag_move: Optional[Callable[[int, int, int, int], None]] = None
        self.on_drag_end: Optional[Callable[[int, int, int, int], None]] = None
        self.on_click_elsewhere: Optional[Callable[[], None]] = None

        # 安装事件过滤器
        overlay_widget.installEventFilter(self)

    @property
    def is_dragging(self) -> bool:
        return self._dragging

    @property
    def start_pos(self) -> Optional[Tuple[int, int]]:
        return self._start_pos

    @property
    def current_pos(self) -> Optional[Tuple[int, int]]:
        return self._current_pos

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if obj != self._widget:
            return super().eventFilter(obj, event)

        if event.type() == QEvent.MouseButtonPress:
            me = QMouseEvent(event)
            if me.button() == Qt.LeftButton:
                self._dragging = True
                self._start_pos = (me.x(), me.y())
                self._current_pos = (me.x(), me.y())
                if self.on_drag_start:
                    self.on_drag_start(me.x(), me.y())
                return True

        elif event.type() == QEvent.MouseMove:
            me = QMouseEvent(event)
            if self._dragging:
                self._current_pos = (me.x(), me.y())
                if self.on_drag_move and self._start_pos:
                    sx, sy = self._start_pos
                    self.on_drag_move(sx, sy, me.x(), me.y())
                return True

        elif event.type() == QEvent.MouseButtonRelease:
            me = QMouseEvent(event)
            if self._dragging and me.button() == Qt.LeftButton:
                self._dragging = False
                if self.on_drag_end and self._start_pos:
                    sx, sy = self._start_pos
                    self.on_drag_end(sx, sy, self._current_pos[0], self._current_pos[1])
                return True

        return super().eventFilter(obj, event)

    def reset(self):
        """重置拖拽状态"""
        self._dragging = False
        self._start_pos = None
        self._current_pos = None
