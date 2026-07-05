"""
测试：WindowStaysOnTopHint VS SetWindowPos HWND_TOP 对点击穿透的影响

测试 A: 无 WindowStaysOnTopHint，用 SetWindowPos 保持在最上
测试 B: 有 WindowStaysOnTopHint (原始方案)

运行：
    .venv/Scripts/python scripts/test_clickthrough.py
"""

import sys
import ctypes
import logging
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QCursor

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger("ct-test")

VK_LBUTTON = 0x01
HWND_TOP = 0
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001


class TestA(QWidget):
    """无 WindowStaysOnTopHint + SetWindowPos HWND_TOP"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test A (HWND_TOP)")
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setGeometry(0, 0, 2240, 1400)

        self._prev_left = False
        self._clicks = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)

    def showEvent(self, event):
        super().showEvent(event)
        # 用 SetWindowPos 推到 Z 序最上面（不是 topmost）
        try:
            hwnd = int(self.winId())
            ctypes.windll.user32.SetWindowPos(hwnd, HWND_TOP, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
            log.info("Test A: SetWindowPos HWND_TOP 已执行")
        except Exception as e:
            log.warning(f"SetWindowPos 失败: {e}")

    def _tick(self):
        self.update()
        # 每帧重新确保 Z 序
        left_down = (ctypes.windll.user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000) != 0
        if left_down and not self._prev_left:
            self._clicks += 1
            pos = QCursor.pos()
            log.info(f"🖱️ Test A 检测到全局点击 #{self._clicks}: ({pos.x()}, {pos.y()})")
        self._prev_left = left_down

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(255, 0, 0, 25))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(100, 100, f"Test A (HWND_TOP) — 点击应穿透")
        painter.drawText(100, 130, f"全局点击: {self._clicks}")
        painter.end()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 只运行 Test A
    w = TestA()
    w.show()
    log.info("Test A 已显示（红色），请点击覆盖层下方 — 看是否能点到底层窗口")
    sys.exit(app.exec_())
