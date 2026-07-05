"""
鼠标事件测试 B 版：测试 showEvent + ctypes 是否破坏鼠标事件。

与 test_mouse_overlay.py 完全相同，但添加了 showEvent + ctypes 代码。
如果这个版本收不到鼠标事件，说明 ctypes SetWindowLongW 有问题。
如果这个版本能收到，说明问题在生产代码的其他地方。

运行：
    .venv/Scripts/python scripts/test_mouse_overlay_b.py
"""

import sys
import ctypes
import logging
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QMouseEvent

logging.basicConfig(level=logging.DEBUG, format="[%(levelname)s] %(message)s")
log = logging.getLogger("mouse-test-b")


class TestWindowB(QWidget):
    """带 showEvent + ctypes 的测试窗口"""

    clicks = 0
    moves = 0

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mouse Test B")

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

    # ── 与生产代码相同的 showEvent ──
    def showEvent(self, event):
        super().showEvent(event)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        try:
            hwnd = int(self.winId())
            GWL_EXSTYLE = -20
            WS_EX_TRANSPARENT = 0x00000020
            WS_EX_LAYERED = 0x00080000
            user32 = ctypes.windll.user32
            current = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            log.info(f"WS_EX 原始值: 0x{current:08X}")
            new_style = (current | WS_EX_LAYERED) & ~WS_EX_TRANSPARENT
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
            # 验证修改生效
            after = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            log.info(f"WS_EX 修改后: 0x{after:08X}")
            log.info(f"WS_EX_TRANSPARENT 清除前: {'有' if current & WS_EX_TRANSPARENT else '无'}, 清除后: {'有' if after & WS_EX_TRANSPARENT else '无'}")
        except Exception as e:
            log.warning(f"ctypes 失败: {e}")

    def mousePressEvent(self, event: QMouseEvent):
        self.clicks += 1
        log.info(f"🖱️ 按下 #{self.clicks}  ({event.x()}, {event.y()})")
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        self.moves += 1
        if self.moves % 30 == 0:
            log.debug(f"移动 #{self.moves}  ({event.x()}, {event.y()})")
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        log.info(f"🖱️ 松开 ({event.x()}, {event.y()})")
        event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 255, 40))
        painter.setPen(QColor(255, 255, 255, 200))
        painter.drawText(self.rect(), Qt.AlignCenter,
                         f"B: Clicks={self.clicks}  Moves={self.moves}")
        painter.end()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = TestWindowB()
    w.show()
    log.info("测试窗口 B 已显示（蓝色半透明），请点击并拖拽。")
    sys.exit(app.exec_())
