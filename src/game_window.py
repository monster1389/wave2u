"""NIKKE 游戏窗口跟踪器"""

from typing import Optional, Tuple
import pygetwindow as gw


class GameWindowTracker:
    """跟踪 NIKKE 游戏窗口的位置和大小"""

    def __init__(self, window_title: str = "NIKKE"):
        self.window_title = window_title
        self._window: Optional[gw.Window] = None
        self._x = self._y = self._w = self._h = 0

    @property
    def is_found(self) -> bool:
        return self._window is not None

    @property
    def rect(self) -> Tuple[int, int, int, int]:
        """返回 (x, y, w, h)"""
        return (self._x, self._y, self._w, self._h)

    def refresh(self) -> bool:
        """
        刷新窗口位置信息。

        Returns:
            True 如果窗口已找到且位置有变化
        """
        windows = gw.getWindowsWithTitle(self.window_title)
        visible = [w for w in windows if w.visible]

        if not visible:
            if self._window is not None:
                self._window = None
                return True
            return False

        win = visible[0]
        if not win.isMinimized:
            new_rect = (win.left, win.top, win.width, win.height)
            if new_rect != (self._x, self._y, self._w, self._h):
                self._x, self._y, self._w, self._h = new_rect
                self._window = win
                return True

        return False
