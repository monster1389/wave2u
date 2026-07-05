"""
测试点击穿透：WA_TransparentForMouseEvents = True 的组合。

验证：覆盖层设置了点击穿透后，点击是否能到达下面的窗口。

运行：
    .venv/Scripts/python scripts/test_clickthrough.py
"""

import sys
import ctypes
import logging
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger("clickthrough-test")

VK_LBUTTON = 0x01


class ClickThroughTest(QWidget):
    """测试各种标志组合的点击穿透效果"""

    def __init__(self, use_topmost=True, use_transparent=True, use_tool=True):
        super().__init__()
        self._counter = 0

        flags = Qt.FramelessWindowHint
        if use_topmost:
            flags |= Qt.WindowStaysOnTopHint
        if use_tool:
            flags |= Qt.Tool
        self.setWindowFlags(flags)

        if use_transparent:
            self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        # 关键：点击穿透
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self.setGeometry(0, 0, 2240, 1400)

        # 用全局钩子检测鼠标
        self._prev_left = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._timer.start(33)

    def _poll(self):
        left_down = (ctypes.windll.user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000) != 0
        if left_down and not self._prev_left:
            from PyQt5.QtGui import QCursor
            pos = QCursor.pos()
            log.info(f"🖱️ 检测到全局点击: ({pos.x()}, {pos.y()})")
        self._prev_left = left_down

    def paintEvent(self, event):
        self._counter += 1
        if self._counter % 30 == 0:
            painter = QPainter(self)
            # 画半透明，确认覆盖层可见
            painter.fillRect(self.rect(), QColor(255, 0, 0, 20))
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(100, 100, "点击穿透测试")
            painter.drawText(100, 130, "点击应能穿透到下面的窗口")
            painter.end()


def main():
    app = QApplication(sys.argv)
    w = ClickThroughTest()
    w.show()
    log.info("测试窗口已显示（红色半透明）")
    log.info("请点击窗口下方的任意位置，观察是否能点到底层窗口")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
