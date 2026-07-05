"""
覆盖层窗口独立测试。

启动一个空白覆盖层，用于手动测试窗口位置和对齐。

Usage:
    .venv/Scripts/python scripts/test_overlay.py
"""

import sys
sys.path.insert(0, "src")

from PyQt5.QtWidgets import QApplication
from src.overlay.window import OverlayWindow
from src.overlay.renderer import Renderer


def main():
    app = QApplication(sys.argv)

    renderer = Renderer()
    # 添加一些测试数据
    fx, fy, fw, fh = 800, 210, 637, 845
    renderer.grid_rect = (fx, fy, fw, fh)
    renderer.launch_point = (fx + fw // 2, fy + fh - 20)

    # 模拟方块
    renderer.blocks = [
        {"col": 3, "row": 4, "x": fx + 200, "y": fy + 300, "w": 106, "h": 105},
    ]

    # 模拟轨迹
    pts = []
    for i in range(200):
        t = i * 0.05
        pts.append((
            int(fx + fw // 2 + t * 2 * 10),
            int(fy + fh - 20 - t * 10),
        ))
    renderer.trajectory = pts
    renderer.endpoint = pts[-1]

    overlay = OverlayWindow(renderer=renderer)
    overlay.resize_to(0, 0, 1920, 1080)
    overlay.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
