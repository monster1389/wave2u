"""
极简生产克隆：与 test_mouse_overlay_b.py 完全相同的窗口，
但作为 src/overlay/minimal.py 被 python -m src.main 加载。

运行方法与生产代码完全相同：
    .venv/Scripts/python -m src.main

如果这个能收到鼠标事件但 OverlayWindow 收不到，说明:
  问题在 window.py 与 main.py 的交互中

如果这个也收不到，说明:
  问题在 python -m 的运行方式或 import 路径
"""

import sys
import ctypes
import logging
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QMouseEvent

logging.basicConfig(level=logging.DEBUG, format="[%(levelname)s] %(message)s")
log = logging.getLogger("minimal-overlay")


class MinimalOverlay(QWidget):
    """与 test_mouse_overlay_b.py 完全相同的实现"""

    clicks = 0

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Minimal Overlay")

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self.setGeometry(0, 0, 2240, 1400)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update)
        self._timer.start(33)

    def showEvent(self, event):
        super().showEvent(event)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

    def mousePressEvent(self, event: QMouseEvent):
        self.clicks += 1
        log.info(f"🖱️ 按下 #{self.clicks}  ({event.x()}, {event.y()})")
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.clicks > 0:
            log.debug(f"移动: ({event.x()}, {event.y()})")
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        log.info(f"🖱️ 松开 ({event.x()}, {event.y()})")
        event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 255, 0, 30))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(self.rect(), Qt.AlignCenter,
                         f"MINIMAL: Clicks={self.clicks}")
        painter.end()


# ── 与 src/main.py 相同的 main 入口 ──
def main():
    # 注意：这里不用 QApplication，让 caller 提供
    w = MinimalOverlay()
    w.show()
    log.info("MinimalOverlay 已显示（绿色半透明）")
    return w


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main()
    sys.exit(app.exec_())
