"""
直接测试 OverlayWindow 的鼠标事件，排除 main.py 的所有干扰。

运行：
    .venv/Scripts/python scripts/test_overlay_direct.py
"""

import sys
sys.path.insert(0, "src")

import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from src.overlay.window import OverlayWindow

logging.basicConfig(level=logging.DEBUG, format="[%(levelname)s] %(message)s")
log = logging.getLogger("direct-test")

app = QApplication(sys.argv)

w = OverlayWindow()
w.setGeometry(0, 0, 2240, 1400)
w.show()
log.info("OverlayWindow 直接测试（白色半透明），请点击拖拽")

# 在覆盖层上画点击计数
class DummyRenderer:
    clicks = 0
    def draw(self, painter, win_w, win_h):
        from PyQt5.QtGui import QColor
        painter.fillRect(0, 0, win_w, win_h, QColor(255, 255, 255, 30))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(400, 400, f"Clicks: {self.clicks}")

r = DummyRenderer()
w.set_renderer(r)

# 自己连回调计数
def on_start(sx, sy):
    r.clicks += 1
    log.info(f"✅ on_drag_start: ({sx},{sy}) total={r.clicks}")
w.on_drag_start = on_start
w.on_drag_move = lambda sx, sy, mx, my: log.debug(f"拖拽 ({sx},{sy})->({mx},{my})")

sys.exit(app.exec_())
