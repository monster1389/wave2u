"""
直接测试 OverlayWindow 类，排除 main.py 干扰。
路径修正版（相对于 test_mouse_overlay_b.py）。

运行：
    .venv/Scripts/python scripts/test_overlay_direct.py
"""

import sys
import os
# 修正 path：把项目根目录加入 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import logging
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QMouseEvent

from src.overlay.window import OverlayWindow

logging.basicConfig(level=logging.DEBUG, format="[%(levelname)s] %(message)s")
log = logging.getLogger("direct-test")

app = QApplication(sys.argv)

# 直接用 OverlayWindow
w = OverlayWindow()
w.setGeometry(0, 0, 2240, 1400)

# 一个简单渲染器，画显眼的红色半透明 + 点击计数
class SimpleRenderer:
    clicks = 0
    def draw(self, painter, win_w, win_h):
        painter.fillRect(0, 0, win_w, win_h, QColor(255, 0, 0, 80))  # 红色，半透明
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(100, 100, f"OverlayWindow 直接测试")
        painter.drawText(100, 130, f"Clicks: {self.clicks}")
        if self.clicks > 0:
            painter.drawText(100, 160, "✅ 收到鼠标事件！")

r = SimpleRenderer()
w.set_renderer(r)

# 连回调
def on_start(sx, sy):
    r.clicks += 1
    log.info(f"✅ on_drag_start 被调用: ({sx},{sy})")

w.on_drag_start = on_start
w.on_drag_move = lambda sx, sy, mx, my: log.debug(f"拖拽 ({sx},{sy})->({mx},{my})")

w.show()
log.info("OverlayWindow 直接测试（红色半透明），请点击拖拽")
sys.exit(app.exec_())
