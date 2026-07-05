"""
测试 WindowStaysOnTopHint 是否阻止了点击穿透。

Test C: 用 SetWindowPos 同时保持 TOPMOST 但检查 WS_EX_TRANSPARENT 是否生效
Test D: 完全不用 Qt 窗口标志，全部用 Windows API 创建覆盖层

运行：
    .venv/Scripts/python scripts/test_clickthrough.py
"""

import sys
import ctypes
import logging
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QCursor, QPaintDevice

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger("ct-test")

VK_LBUTTON = 0x01
GWL_EXSTYLE = -20
WS_EX_TRANSPARENT = 0x00000020
WS_EX_LAYERED = 0x00080000
WS_EX_TOPMOST = 0x00000008
HWND_TOPMOST = -1
HWND_TOP = 0
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040


class TestC(QWidget):
    """WindowStaysOnTopHint + showEvent 中验证 WS_EX_TRANSPARENT"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test C (TOPMOST + verify)")
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
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
        try:
            hwnd = int(self.winId())
            user32 = ctypes.windll.user32
            # 验证窗口样式
            style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            has_transparent = bool(style & WS_EX_TRANSPARENT)
            has_topmost = bool(style & WS_EX_TOPMOST)
            has_layered = bool(style & WS_EX_LAYERED)
            log.info(f"Test C WS_EX: TRANSPARENT={has_transparent} TOPMOST={has_topmost} LAYERED={has_layered}")
        except Exception as e:
            log.warning(f"showEvent: {e}")

    def _tick(self):
        self.update()
        left_down = (ctypes.windll.user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000) != 0
        if left_down and not self._prev_left:
            self._clicks += 1
            pos = QCursor.pos()
            log.info(f"🖱️ Test C 全局点击 #{self._clicks}: ({pos.x()}, {pos.y()})")
            log.info(f"   可以点到底层窗口吗？{'✅ 能' if False else '❌ 需要你告诉我'}")
        self._prev_left = left_down

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 255, 25))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(100, 100, f"Test C: WindowStaysOnTopHint + WA_TransparentForMouseEvents")
        painter.drawText(100, 130, f"点击穿透测试 — 看能否点到底层窗口")
        painter.end()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 先运行 Test C 验证问题，然后切换 Test D
    from PyQt5.QtCore import QTimer

    def run_test_d():
        log.info("=" * 40)
        log.info("Test D: SetWindowLongW + SetWindowPos 手动设置 WS_EX_TRANSPARENT")
        w = TestC()  # 重用 TestC 的类，但手动改样式

        # 手动注入 WS_EX_TRANSPARENT（就是生产代码的修复方案）
        try:
            hwnd = int(w.winId())
            user32 = ctypes.windll.user32
            current = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            new_style = current | WS_EX_TRANSPARENT
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
            user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0,
                                SWP_FRAMECHANGED | SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_NOZORDER)
            after = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            log.info(f"Test D WS_EX: TRANSPARENT={bool(after & WS_EX_TRANSPARENT)}")
            log.info("Test D: 点击穿透已手动设置，请测试能否点到底层窗口")
        except Exception as e:
            log.error(f"Test D 失败: {e}")

    QTimer.singleShot(100, run_test_d)
    log.info("5秒后自动切换到 Test D...")

    w = TestC()
    w.show()
    sys.exit(app.exec_())
