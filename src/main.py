"""
NIKKE 实时预判线覆盖层 — 入口点

启动流程：
  1. 初始化窗口跟踪器
  2. 初始化检测模块
  3. 创建并显示 PyQt5 覆盖层
  4. 启动主循环（QTimer 驱动）

Usage:
    .venv/Scripts/python -m src.main
"""

import sys
import logging
from typing import Optional, Tuple

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor

from src.config import DETECTION_INTERVAL, WINDOW_CHECK_INTERVAL
from src.game_window import GameWindowTracker
from src.detection.blocks import detect_blocks
from src.detection.launch_point import detect_launch_point
from src.physics.trajectory import simulate
from src.overlay.window import OverlayWindow
from src.overlay.renderer import Renderer
from src.overlay.input_handler import InputHandler

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("nikke-overlay")


class NikkeOverlayApp:
    """应用主控制器"""

    def __init__(self):
        self.app = QApplication(sys.argv)

        # 组件
        self.window_tracker = GameWindowTracker()
        self.renderer = Renderer()
        self.overlay = OverlayWindow(renderer=self.renderer)
        self.input_handler = InputHandler(self.overlay)

        # 状态
        self._blocks: list = []
        self._launch_point: Optional[Tuple[int, int]] = None

        # 定时器
        self._detect_timer = QTimer(self.app)
        self._detect_timer.timeout.connect(self._run_detection)
        self._detect_timer.start(int(DETECTION_INTERVAL * 1000))

        self._window_timer = QTimer(self.app)
        self._window_timer.timeout.connect(self._check_window)
        self._window_timer.start(int(WINDOW_CHECK_INTERVAL * 1000))

        # 连接鼠标回调
        self.input_handler.on_drag_start = self._on_drag_start
        self.input_handler.on_drag_move = self._on_drag_move
        self.input_handler.on_drag_end = self._on_drag_end

    def _check_window(self):
        """检测窗口位置变化"""
        self.window_tracker.refresh()
        if self.window_tracker.is_found:
            x, y, w, h = self.window_tracker.rect
            self.overlay.resize_to(x, y, w, h)
            if not self.overlay.isVisible():
                self.overlay.show()
                logger.info(f"覆盖层已显示: ({x},{y}) {w}x{h}")
                self._run_detection()
        else:
            if self.overlay.isVisible():
                self.overlay.hide()
                logger.info("窗口未找到，覆盖层已隐藏")
            self.renderer.status_text = "Window not found"
            self.renderer.status_color = QColor(200, 0, 0)

    def _run_detection(self):
        """运行检测管线"""
        if not self.window_tracker.is_found:
            return

        try:
            import pyautogui
            import cv2
            import numpy as np

            screenshot = pyautogui.screenshot()
            frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            # 方块检测
            blocks = detect_blocks(frame)
            if blocks:
                self._blocks = blocks
                self.renderer.blocks = blocks
                logger.info(f"检测到 {len(blocks)} 个方块")

            # 发射点检测（仅首次）
            if self._launch_point is None:
                pt = detect_launch_point(frame)
                if pt:
                    self._launch_point = pt
                    self.renderer.launch_point = pt
                    logger.info(f"发射点: {pt}")
                    self.renderer.status_text = "Ready"
                    self.renderer.status_color = QColor(0, 200, 0)
                else:
                    self.renderer.status_text = "Detecting..."

        except Exception as e:
            logger.warning(f"检测失败: {e}")

    def _on_drag_start(self, sx: int, sy: int):
        """点击时以鼠标位置为发射起点"""
        self._launch_point = (sx, sy)
        self.renderer.launch_point = (sx, sy)
        logger.info(f"发射点已设置: ({sx}, {sy})")

    def _on_drag_move(self, sx: int, sy: int, mx: int, my: int):
        """拖拽移动 → 更新预判线"""
        # 使用点击位置 (sx,sy) 作为发射点，无需等待 CV 检测
        dx = mx - sx
        dy = my - sy

        self.renderer.is_dragging = True
        self.renderer.mouse_pos = (mx, my)

        # 模拟轨迹
        waypoints, reason, col, row = simulate(sx, sy, dx, dy, self._blocks)
        self.renderer.trajectory = waypoints
        if waypoints:
            self.renderer.endpoint = waypoints[-1]

    def _on_drag_end(self, sx: int, sy: int, mx: int, my: int):
        """松开鼠标 → 锁定路径"""
        self.renderer.is_dragging = False

    def run(self):
        """启动应用"""
        self._check_window()
        sys.exit(self.app.exec_())


def main():
    app = NikkeOverlayApp()
    app.run()


if __name__ == "__main__":
    main()
