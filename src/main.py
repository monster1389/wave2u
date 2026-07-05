"""
NIKKE 实时预判线覆盖层 — 入口点

工作流程：
  1. 实时截图检测游戏轨迹线（淡青色）
  2. 从轨迹线提取发射点 + 方向
  3. 模拟含反射的完整反弹路径
  4. 显示在覆盖层上
  5. 游戏轨迹消失 → 覆盖层自动清除

Usage:
    .venv/Scripts/python -m src.main
"""

import sys
import logging

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor

from src.config import DETECTION_INTERVAL, WINDOW_CHECK_INTERVAL
from src.game_window import GameWindowTracker
from src.detection.blocks import detect_blocks
from src.detection.launch_point import detect_trajectory
from src.physics.trajectory import simulate
from src.overlay.window import OverlayWindow
from src.overlay.renderer import Renderer

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

        # 状态
        self._blocks: list = []
        self._prev_frame = None     # 上一帧（用于帧差法）
        self._frame_count = 0       # 帧计数（用于定期全量检测）
        self._miss_count = 0          # 连续未检测到轨迹线的次数
        self._last_traj_data = None   # (lx, ly, dx, dy) 上次有效的轨迹
        self._max_miss = 3            # 最多保持3帧（~450ms）

        # 定时器
        self._detect_timer = QTimer(self.app)
        self._detect_timer.timeout.connect(self._run_detection)
        self._detect_timer.start(int(DETECTION_INTERVAL * 1000))

        self._window_timer = QTimer(self.app)
        self._window_timer.timeout.connect(self._check_window)
        self._window_timer.start(int(WINDOW_CHECK_INTERVAL * 1000))

    def _check_window(self):
        """检测窗口位置变化"""
        self.window_tracker.refresh()
        if self.window_tracker.is_found:
            x, y, w, h = self.window_tracker.rect
            self.overlay.resize_to(x, y, w, h)
            if not self.overlay.isVisible():
                self.overlay.show()
                logger.info(f"覆盖层已显示: ({x},{y}) {w}x{h}")
        else:
            if self.overlay.isVisible():
                self.overlay.hide()
                logger.info("窗口未找到，覆盖层已隐藏")
            self.renderer.status_text = "Window not found"
            self.renderer.status_color = QColor(200, 0, 0)

    def _run_detection(self):
        """检测游戏轨迹线 → 模拟完整反弹路径 → 显示"""
        if not self.window_tracker.is_found:
            return

        try:
            import pyautogui
            import cv2
            import numpy as np

            screenshot = pyautogui.screenshot()
            frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            # 1. 检测方块（帧差法，首次或每30帧做全量检测）
            blocks = detect_blocks(
                frame, self._prev_frame, self._blocks,
                force_full=(self._frame_count % 30 == 0)
            )
            self._blocks = blocks
            self.renderer.blocks = blocks
            self._frame_count += 1

            # 2. 帧差法检测轨迹线
            traj = detect_trajectory(frame, self._prev_frame)
            self._prev_frame = frame.copy()
            if traj:
                self._miss_count = 0
                self._last_traj_data = traj
                lx, ly, dx, dy = traj

                # 更新发射点显示
                self.renderer.launch_point = (lx, ly)

                # 3. 模拟完整反弹路径
                waypoints, reason, col, row = simulate(lx, ly, dx, dy, self._blocks)
                logger.debug(f"轨迹模拟: {len(waypoints)}点 {reason} hit=({col},{row})")
                self.renderer.trajectory = waypoints
                if waypoints:
                    self.renderer.endpoint = waypoints[-1]

                self.renderer.status_text = "预测中"
                self.renderer.status_color = QColor(0, 200, 0)
            else:
                # 没检测到 → 用上次有效结果保持几帧（防闪烁）
                self._miss_count += 1
                if self._miss_count < self._max_miss and self._last_traj_data:
                    # 用缓存的轨迹继续显示
                    lx, ly, dx, dy = self._last_traj_data
                    waypoints, reason, col, row = simulate(lx, ly, dx, dy, self._blocks)
                    logger.debug(f"缓存轨迹: {len(waypoints)}点 {reason}")
                    self.renderer.trajectory = waypoints
                    if waypoints:
                        self.renderer.endpoint = waypoints[-1]
                else:
                    # 真的没了 → 清除
                    if self.renderer.trajectory:
                        self.renderer.trajectory = []
                        self.renderer.endpoint = None
                        self.renderer.is_dragging = False
                        self._last_traj_data = None
                        self.renderer.status_text = "就绪"
                        self.renderer.status_color = QColor(100, 100, 100)

        except Exception as e:
            logger.warning(f"检测失败: {e}")

    def run(self):
        """启动应用"""
        self._check_window()
        sys.exit(self.app.exec_())


def main():
    app = NikkeOverlayApp()
    app.run()


if __name__ == "__main__":
    main()
