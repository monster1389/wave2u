"""
最小化鼠标事件测试。
隔离测试透明窗口能否接收鼠标点击，排除所有应用逻辑干扰。

运行：
    .venv/Scripts/python scripts/test_mouse_overlay.py
"""

import sys
import logging
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QMouseEvent

logging.basicConfig(level=logging.DEBUG, format="[%(levelname)s] %(message)s")
log = logging.getLogger("mouse-test")


class TestWindow(QWidget):
    """纯测试：透明窗口 + 鼠标事件"""

    clicks = 0
    moves = 0
    releases = 0

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mouse Test Overlay")

        # ── 尝试不同的 flags / attributes 组合 ──
        # 方案 A: 当前生产代码使用的组合
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        # 全屏覆盖
        self.setGeometry(0, 0, 2240, 1400)

        # 定时刷新
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update)
        self._timer.start(33)

    # ── 鼠标事件 ──
    def mousePressEvent(self, event: QMouseEvent):
        self.clicks += 1
        log.info(f"🖱️ 鼠标按下 #{self.clicks}  ({event.x()}, {event.y()}) button={event.button()}")
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        self.moves += 1
        if self.moves % 30 == 0:  # 打印频率限制
            log.debug(f"鼠标移动 #{self.moves}  ({event.x()}, {event.y()})")
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.releases += 1
        log.info(f"🖱️ 鼠标松开 #{self.releases}  ({event.x()}, {event.y()})")
        event.accept()

    # ── 绘制：一个显眼的半透明红色矩形，确认覆盖层可见 ──
    def paintEvent(self, event):
        painter = QPainter(self)
        # 填充半透明红色背景，确保看到覆盖层
        painter.fillRect(self.rect(), QColor(255, 0, 0, 40))
        # 画提示文字
        painter.setPen(QColor(255, 255, 255, 200))
        painter.drawText(self.rect(), Qt.AlignCenter,
                         f"Clicks: {self.clicks}\nMoves: {self.moves}")
        painter.end()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = TestWindow()
    w.show()
    log.info("测试窗口已显示。请点击并拖拽鼠标，观察日志是否有鼠标事件。")
    sys.exit(app.exec_())
