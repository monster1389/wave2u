"""
测试入口：用 MinimalOverlay 替换 OverlayWindow。
与生产完全相同的运行方式，只换掉覆盖层实现。

运行：
    .venv/Scripts/python -m src.test_main
"""

import sys
import logging

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

from src.overlay.minimal import MinimalOverlay

logging.basicConfig(level=logging.DEBUG, format="[%(levelname)s] %(message)s")
log = logging.getLogger("test-main")


class TestApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.overlay = MinimalOverlay()

        # 定时器：与生产代码的行为一致
        self._window_timer = QTimer(self.app)
        self._window_timer.timeout.connect(self._check)
        self._window_timer.start(1000)

    def _check(self):
        # 如果还没显示就显示（模拟生产 _check_window）
        if not self.overlay.isVisible():
            self.overlay.show()
            log.info("MinimalOverlay 已显示")

    def run(self):
        self._check()
        sys.exit(self.app.exec_())


def main():
    app = TestApp()
    app.run()


if __name__ == "__main__":
    main()
